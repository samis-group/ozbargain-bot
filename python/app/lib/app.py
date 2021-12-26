from datetime import datetime, timedelta
import time
import boto3
import requests
import json
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import html

class Ozbargain():
    def __init__(self, logger) -> None:
        self.__logger = logger
        # Do some validation for required params
        try:
            self.ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])
        except:
            self.__logger.debug("Could not connect to SSM, Please ensure that you have the following environment variables set: OZBARGAIN_TIMESTAMP_FILE, OZBARGAIN_SLACK_WEBHOOK and OZBARGAIN_CURL_COOKIE")

        try:
            self.slack_webhook = self.get_setting('OZBARGAIN_SLACK_WEBHOOK')
        except:
            self.slack_webhook = False
        if self.slack_webhook:
            self.__logger.debug(f'slack_webhook url: {self.slack_webhook}')
        else:
            self.__logger.info(f'No Slack webhook defined.')

        self.discord_webhook = self.get_setting('OZBARGAIN_DISCORD_WEBHOOK')
        if self.discord_webhook:
            self.__logger.debug(f'discord_webhook: {self.discord_webhook}')
        else:
            self.__logger.info(f'No Discord webhook defined.')

        if not self.slack_webhook and not self.discord_webhook:
            raise Exception("No slack or discord Webhook defined in environment variables or SSM Parameters 'ozbargain_slack_webhook/ozbargain_discord_webhook'")

        try:
            self.curl_cookie = self.get_setting('OZBARGAIN_CURL_COOKIE')
        except:
            raise Exception("Unable to locate required curl cookie in environment variable or SSM Parameter 'ozbargain_curl_cookie'.")
        try:
            # Try to get the SSM parameter
            self.timestamp_parameter = self.get_setting('OZBARGAIN_TIMESTAMP')
        except:
            try:
                # Try to get the file path instead
                self.timestamp_file = self.get_setting('OZBARGAIN_TIMESTAMP_FILE')
            except:
                raise Exception("No OZBARGAIN_TIMESTAMP_PARAMETER or OZBARGAIN_TIMESTAMP_FILE specified, where am I writing the new timestamp to?")
        self.ozbargain_feed_url = 'https://www.ozbargain.com.au/deals/feed'
        self.ozbargain_logo = "https://files.delvu.com/images/ozbargain/logo/Square.png"
        self.default_timedelta_minutes = 5
        self.namespace = {'ozb': 'https://www.ozbargain.com.au'}

    def get_ssm_parameter_value(self, parameter_path):
        parameter = self.ssm.get_parameter(
            Name=parameter_path, 
            WithDecryption=True)
        result = parameter['Parameter']['Value']
        return result

    def set_timestamp_parameter_value(self, value):
        # If file exists, write timestamp to it instead of SSM param
        if self.timestamp_file:
            # If file doesn't exist, let's try to create it for them
            if not os.path.isfile(self.timestamp_file):
                self.__logger.debug("File doesn't exist, creating...")
            with open(self.timestamp_file, 'w+') as file:
                file.write(str(value))
                self.__logger.debug("Wrote timestamp to file...")
        # Else write to SSM
        else:
            try:
                self.ssm.put_parameter(
                    Name=self.timestamp_parameter,
                    Value=str(value),
                    Type='String',
                    Overwrite=True
                )
            except Exception as e:
                self.__logger.error(f"Error setting param in SSM: {e}")
            self.__logger.info(f"Updated SSM parameter '{self.timestamp_parameter}' to '{value}'.")

    def get_setting(self, setting_name):
        env_var = setting_name.upper()
        param_path = f'{env_var}_PARAMETER'
        if env_var in os.environ:
            return os.environ[env_var]
        elif param_path in os.environ:
            return self.get_ssm_parameter_value(os.environ[param_path])
        else:
            raise Exception(f"You must specify either {env_var} or {param_path}")

    def get_xml_tree(self, xml_file=False):
        self.__logger.info("Getting XML Tree...")
        if xml_file:
            with open(xml_file, 'r') as file:
                xml_feed = file.read()
        else:
            headers = {}
            headers['cache-control'] = "max-age=0"
            headers['cookie'] = f"G_ENABLED_IDPS=google; PHPSESSID={self.curl_cookie}"
            xml_feed = requests.get(self.ozbargain_feed_url, headers=headers).content
        xml_tree = ET.fromstring(xml_feed)
        return xml_tree

    def get_deal_data(self, item):
        # Certain characters need to be stripped So that they don't break the formatting of the slack messages.
        strip_items_title = ["|", "<", ">", "*"]
        strip_items_other = ["|", "{", "}", "*"]
        title = item.find('title').text
        title_escaped = html.unescape(title)
        self.__logger.debug(f'title_escaped: {title_escaped}')
        title = self.strip_items(strip_items_title, title)
        self.__logger.debug(f'title: {title}')
        pub_date = item.find('pubDate').text
        self.__logger.debug(f'pub_date: {pub_date}')
        link = item.find('link').text
        link = self.strip_items(strip_items_other, link)
        self.__logger.debug(f'link: {link}')
        category = item.find('category').text
        category = self.strip_items(["{", "}", "*"], category)
        self.__logger.debug(f'category: {category}')
        category_link = item.find('category').attrib['domain']
        category_link = self.strip_items(strip_items_other, category_link)
        self.__logger.debug(f'category_link: {category_link}')
        comments = item.find('comments').text
        comments = self.strip_items(strip_items_other, comments)
        self.__logger.debug(f'comments: {comments}')
        description_long = item.find('description').text
        # Description requires parsing HTML
        html_parser = BeautifulSoup(description_long, 'html.parser')
        description_long_parsed = html_parser.get_text()
        # I've yet to figure out how to limit or create an expanding block in slack for longer descriptions
        # Just gonna hard limit so descriptions can't take over the channel
        # HTML inside the description goes 'div > a > img (these 3 nested tags get closed off) > Actual description in the rest'
        # So let's grab every child after the first index i.e. index 1 and up
        if len(description_long_parsed) > 200:
            description = description_long_parsed[0:200] + '...'
        else:
            description = description_long_parsed
        description = self.strip_items(strip_items_other, description)
        self.__logger.debug(f'description: {description}')
        # The rest of the data is in the ozb:meta namespace in XML
        try:
            image = item.find('ozb:meta', self.namespace).attrib['image']
            image = self.strip_items(strip_items_other, image)
        except KeyError:
            image = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"
        self.__logger.debug(f'image: {image}')
        try:
            direct_url = item.find('ozb:meta', self.namespace).attrib['url']
        except KeyError:
            self.__logger.warning(f"Unable to find dealer link, defaulting to ozbargain deals page.")
            direct_url = "https://www.ozbargain.com.au/deals/"
        self.__logger.debug(f'direct_url: {direct_url}')
        return title, pub_date, link, category, category_link, comments, description, image, direct_url

    def get_timestamp(self, time_to_convert):
        # Gets a string timestamp, converts it to time from epoch for ez calculations.
        converted_timestamp = datetime.strptime(time_to_convert, "%a, %d %b %Y %X %z")
        self.__logger.debug(f'converted timestamp to datetime object for "{time_to_convert}": {converted_timestamp}')
        epoch_timestamp = int(datetime.fromisoformat(str(converted_timestamp)).timestamp())
        self.__logger.debug(f'timestamp since epoch for "{time_to_convert}": {epoch_timestamp}')
        return epoch_timestamp
    
    def strip_items(self, strip_chars, string):
        # Function to Search and Replace string for encoding Unicode Characters to URL encoded characters
        # so Slack can interpret them Instead of breaking the formatting.
        for item in strip_chars:
            string = string.replace(item, '')
        return string

    def post_to_slack(self, title, link, category, category_link, comments, description, image, direct_url):
        self.__logger.info(f"Readying payload for item: '{title}'")
        # Gotta transform some data to load it into the json to look pretty in slack
        category_data = f"Category | <{category_link}|*{category}*>"
        link_and_title = f"<{link}|*{title}*>"
        description = f"```{description}```"
        payload = {
            "blocks": [
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": image,
                            "alt_text": "Images"
                        },
                        {
                            "type": "mrkdwn",
                            "text": category_data
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": link_and_title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": description
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": image,
                        "alt_text": title
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View OzB Page"
                            },
                            "style": "primary",
                            "url": link
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Grab Deal"
                            },
                            "url": direct_url
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Comments"
                            },
                            "style": "danger",
                            "url": comments
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            self.slack_webhook,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        return response

    def post_to_discord(self, title, link, category, category_link, comments, description, image, direct_url):
        #for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
        color = int("ff8c00", 16)
        category_data = f'Category | {html.unescape(category)}'
        payload = {
            "avatar_url": self.ozbargain_logo,
            "embeds": [
                {
                    "author": {
                        "name": category_data,
                        "url": category_link,
                        "icon_url": image
                    },
                    "title": title,
                    "description": description,
                    "url": link,
                    "color": color,
                    "thumbnail": {
                        "url": image
                    },
                    "fields": [
                        {
                            "name": "Comments",
                            "value": comments
                        },
                        {
                            "name": "Direct to Vendor",
                            "value": direct_url
                        }
                    ]
                }
            ],
        }

        response = requests.post(
            self.discord_webhook,
            json=payload
        )

        return response

    def execute(self):
        # If the user specifies an XML file for testing, let it override grabbing the feed from ozbargain site
        if 'XML_FILE' in os.environ:
            xml_file = self.get_setting('XML_FILE')
            if os.path.isfile(xml_file):
                self.__logger.debug(f"XML_FILE found at: {xml_file}")
            else:
                raise Exception(f"XML_FILE specified in environment variables but file not accessible: {xml_file}")
        else:
            xml_file = False

        # Let the user override the timestamp if they wish
        if 'TIMESTAMP_OVERRIDE' in os.environ:
            last_request_timestamp = int(self.get_setting('TIMESTAMP_OVERRIDE'))
            self.__logger.debug(f"TIMESTAMP_OVERRIDE set to: {last_request_timestamp}")
        # If file is specified and exists, grab that value
        elif self.timestamp_file:
            self.__logger.debug(f"Timestamp file specified at: {self.timestamp_file}")
            try:
                with open(self.timestamp_file) as file:
                    file_contents = file.read()
                    self.__logger.debug(f"file timestamp contents: {file_contents}")
                    if not file_contents:
                        last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
                    else:
                        last_request_timestamp = int(file_contents)
            except Exception as e:
                self.__logger.error(f"Something went wrong grabbing the file data at {self.timestamp_file} (does the file exist yet?). Generating a timestamp...")
                last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
        else:
            try:
                self.__logger.info("getting timestamp from SSM...")
                last_request_timestamp = int(self.timestamp_parameter)
            except Exception as e:
                self.__logger.error(f"unable to obtain last published timestamp from SSM, generating one... error: {e}")
                last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
        self.__logger.debug(f"last_request_timestamp: {last_request_timestamp}")

        xml_tree = self.get_xml_tree(xml_file)
        channel = xml_tree.find('channel')
        items = list(channel.iterfind('item'))
        for item in items:
            title, pub_date, link, category, category_link, comments, description, image, direct_url = self.get_deal_data(item)
            epoch_pub_date = self.get_timestamp(pub_date)
            if epoch_pub_date > last_request_timestamp:
                if self.slack_webhook:
                    response = self.post_to_slack(title, link, category, category_link, comments, description, image, direct_url)
                    if response.status_code == 200:
                        self.__logger.info(f"Webhook to Slack successful: {title}")
                    else:
                        raise Exception(f"Webhook to Slack returned an error: {response.text}")
                if self.discord_webhook:
                    response = self.post_to_discord(title, link, category, category_link, comments, description, image, direct_url)
                    if response.status_code in [200, 204]:
                        self.__logger.info(f"Webhook to Discord successful: {title}")
                    elif response.status_code == 429:
                        while response.status_code == 429:
                            errors = json.loads(
                                response.content.decode('utf-8'))
                            wh_sleep = (int(errors['retry_after']) / 1000) + 0.15
                            self.__logger.error(f"Webhook rate limited: sleeping for {wh_sleep} seconds...")
                            time.sleep(wh_sleep)
                            response = self.post_to_discord(title, link, category, category_link, comments, description, image, direct_url)
                            if response.status_code in [200, 204]:
                                self.__logger.info(f"Webhook to Discord successful: {title}")
                                break
                    else:
                        raise Exception(f"Webhook to Discord returned an error: {response.text}")
            else:
                self.__logger.info(f"Breaking, as this item is up to date with last published: {title}")
                break

        # Update timestamp with latest deal published timestamp
        new_epoch_timestamp = self.get_timestamp(items[0].find('pubDate').text)
        if last_request_timestamp != new_epoch_timestamp:
            self.set_timestamp_parameter_value(
                value=new_epoch_timestamp
            )
        else:
            self.__logger.debug(f"Latest deal already published to slack.")
