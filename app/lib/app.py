from datetime import datetime, timedelta
import time
import requests
import json
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import html
import boto3

class Ozbargain():
    def __init__(self, logger) -> None:
        self.__logger = logger
        self.timestamp_file = None
        self.timestamp_parameter_key = None
        self.timestamp_parameter_value = None
        self.timestamp_file_frontpage = None
        self.timestamp_parameter_key_frontpage = None
        self.timestamp_parameter_value_frontpage = None
        self.aws_profile = None
        self.aws_region = None
        self.aws_session = None

        # Do some validation for required params
        try:
            self.aws_region = os.environ['OZBARGAIN_AWS_REGION']
            if not self.aws_region:
                self.aws_region = os.environ['AWS_REGION']
            if self.aws_region:
                # Gotta do some AWS stuff so we can specify account/region while testing.
                try:
                    self.aws_profile = os.environ['OZBARGAIN_AWS_PROFILE']
                    self.aws_session = boto3.Session(region_name=self.aws_region, profile_name=self.aws_profile)
                    self.ssm = self.aws_session.client('ssm', region_name=self.aws_region)
                except Exception as e:
                    self.__logger.debug(f"Could not create a session using specified profile '{self.aws_profile}', trying 'default' profile... Error: {repr(e)}")
                    try:
                        self.ssm = boto3.client('ssm', region_name=self.aws_region)
                    except Exception as e:
                        self.__logger.debug(f"Could not connect to SSM. Please ensure 'OZBARGAIN_AWS_PROFILE' and 'OZBARGAIN_AWS_REGION' environment variables exist and are correct. Error: {repr(e)}")
                        self.__logger.debug("Continuing with file setup, please ensure that you have the correct environment variables set.")
        except Exception as e:
            self.__logger.debug(f"No 'OZBARGAIN_AWS_REGION' environment variable set, this means SSM won't work. This is fine if using files or env variables for values. Error: {repr(e)}")

        try:
            self.slack_webhook = self.get_setting('OZBARGAIN_SLACK_WEBHOOK')
        except:
            self.slack_webhook = False
        if self.slack_webhook:
            self.__logger.debug(f'slack_webhook url: {self.slack_webhook}')
        else:
            self.__logger.debug(f'No Slack webhook defined.')

        try:
            self.slack_webhook_frontpage = self.get_setting('OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE')
        except:
            self.slack_webhook_frontpage = False
        if self.slack_webhook_frontpage:
            self.__logger.debug(f'slack_webhook_frontpage url: {self.slack_webhook_frontpage}')
        else:
            self.__logger.debug(f'No Slack Frontpage webhook defined.')

        try:
            self.discord_webhook = self.get_setting('OZBARGAIN_DISCORD_WEBHOOK')
        except:
            self.discord_webhook = False
        if self.discord_webhook:
            self.__logger.debug(f'discord_webhook: {self.discord_webhook}')
        else:
            self.__logger.debug(f'No Discord webhook defined.')

        try:
            self.discord_webhook_frontpage = self.get_setting('OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE')
        except:
            self.discord_webhook_frontpage = False
        if self.discord_webhook_frontpage:
            self.__logger.debug(f'discord_webhook_frontpage: {self.discord_webhook_frontpage}')
        else:
            self.__logger.debug(f'No Discord Frontpage webhook defined.')

        if not self.slack_webhook and not self.discord_webhook and not self.slack_webhook_frontpage and not self.discord_webhook_frontpage:
            raise Exception("No slack, slack_frontpage, discord or discord_frontpage Webhooks defined in environment variables or SSM Parameters 'OZBARGAIN_SLACK_WEBHOOK/OZBARGAIN_DISCORD_WEBHOOK/OZBARGAIN_SLACK_WEBHOOK_FRONTPAGE/OZBARGAIN_DISCORD_WEBHOOK_FRONTPAGE'")

        try:
            # Try to get the SSM parameter key and value for new deal data
            self.timestamp_parameter_key = self.get_setting('OZBARGAIN_TIMESTAMP_PARAMETER')
            self.timestamp_parameter_value = self.get_setting('OZBARGAIN_TIMESTAMP')
        except:
            try:
                # Try to get the file path instead
                self.timestamp_file = self.get_setting('OZBARGAIN_TIMESTAMP_FILE')
            except:
                pass

        try:
            # Try to get the SSM parameter key and value for frontpage data
            self.timestamp_parameter_key_frontpage = self.get_setting('OZBARGAIN_TIMESTAMP_FRONTPAGE_PARAMETER')
            self.timestamp_parameter_value_frontpage = self.get_setting('OZBARGAIN_TIMESTAMP_FRONTPAGE')
        except:
            try:
                # Try to get the file path instead
                self.timestamp_file_frontpage = self.get_setting('OZBARGAIN_TIMESTAMP_FILE_FRONTPAGE')
            except:
                pass

        if not self.timestamp_parameter_key and not self.timestamp_file and not self.timestamp_parameter_key_frontpage and not self.timestamp_file_frontpage:
            raise Exception("No OZBARGAIN_TIMESTAMP_(FRONTPAGE_)PARAMETER or OZBARGAIN_TIMESTAMP_FILE specified, where am I writing the new timestamp to?")

        self.ozbargain_feed_url = 'https://www.ozbargain.com.au/deals/feed'
        self.ozbargain_frontpage_feed_url = 'https://www.ozbargain.com.au/feed'
        self.ozbargain_logo = "https://files.delvu.com/images/ozbargain/logo/Square.png"
        self.default_timedelta_minutes = 5
        self.namespace = {'ozb': 'https://www.ozbargain.com.au'}

    def get_ssm_parameter_value(self, parameter_path):
        parameter = self.ssm.get_parameter(
            Name=parameter_path, 
            WithDecryption=True
        )
        result = parameter['Parameter']['Value']
        return result

    def set_timestamp_parameter_value(self, value, timestamp_file=None, parameter_key=None):
        # If file exists, write timestamp to it instead of SSM param
        if timestamp_file:
            # If file doesn't exist, let's try to create it for them
            if not os.path.isfile(timestamp_file):
                self.__logger.debug("File doesn't exist, creating...")
            with open(timestamp_file, 'w+') as file:
                file.write(str(value))
                self.__logger.debug("Wrote timestamp to file...")
        # Else write to SSM
        else:
            try:
                self.ssm.put_parameter(
                    Name=parameter_key,
                    Value=str(value),
                    Type='String',
                    Overwrite=True
                )
            except Exception as e:
                self.__logger.error(f"Error setting param in SSM: {e}")
            self.__logger.info(f"Successfully updated SSM parameter '{parameter_key}' to '{value}'.")

    def get_last_request_timestamp(self, timestamp_file=None, timestamp_parameter=None):
        # If file is specified and exists, grab that value
        if timestamp_file:
            self.__logger.debug(f"Timestamp file specified at: {timestamp_file}")
            try:
                with open(timestamp_file) as file:
                    file_contents = file.read()
                    self.__logger.info(f"Current timestamp from file: {file_contents}")
                    if not file_contents:
                        last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
                    else:
                        last_request_timestamp = int(file_contents)
            except Exception as e:
                self.__logger.error(f"Something went wrong grabbing the file data at {timestamp_file} (does the file exist yet?). Generating a timestamp (-{self.default_timedelta_minutes} minutes from now)...")
                last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
        # Else try SSM
        else:
            try:
                last_request_timestamp = int(timestamp_parameter)
                self.__logger.info(f"Obtained timestamp from SSM: {last_request_timestamp}")
            except Exception as e:
                # If not file/ssm, we just take 5 mins off current time and assume deals posted since last cron runtime (assuming cron is set to 5? It better be...)
                self.__logger.error(f"unable to obtain last published timestamp from SSM, Generating a timestamp (-{self.default_timedelta_minutes} minutes from now)... error: {e}")
                last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
        return last_request_timestamp

    def get_setting(self, setting_name):
        # This function will attempt to find the value of the 'setting_name' passed to it in either the environment variables
        # or will add a "_PARAMETER" suffix and attempt to get the VALUE of the parameter from SSM (not the key in the env).
        env_var = setting_name.upper()
        param_path = f'{env_var}_PARAMETER'
        if env_var in os.environ:
            return os.environ[env_var]
        elif param_path in os.environ:
            return self.get_ssm_parameter_value(os.environ[param_path])
        else:
            raise Exception(f"You must specify either {env_var} or {param_path}")

    def get_xml_tree(self, url, xml_file=False):
        self.__logger.debug("Getting XML Tree...")
        if xml_file:
            with open(xml_file, 'r') as file:
                xml_feed = file.read()
        else:
            headers = {}
            headers['cache-control'] = "max-age=0"
            xml_feed = requests.get(url, headers=headers).content
        xml_tree = ET.fromstring(xml_feed)
        return xml_tree

    def process_data(self, xml_tree, last_request_timestamp, slack_webhook=None, discord_webhook=None, slack_webhook_frontpage=None, discord_webhook_frontpage=None):
        channel = xml_tree.find('channel')
        items = list(channel.iterfind('item'))
        for item in items:
            title, pub_date, link, category, category_link, comments, description, image, direct_url = self.get_deal_data(item)
            self.__logger.info(f"Processing item: {title}")
            epoch_pub_date = self.get_timestamp(pub_date)
            if epoch_pub_date > last_request_timestamp:
                # Check if we're posting the frontpage or live deals. Either way, same post to slack/discord, but different hook.
                if slack_webhook_frontpage:
                    slack_webhook = slack_webhook_frontpage
                if slack_webhook:
                    response = self.post_to_slack(title, link, category, category_link, comments, description, image, direct_url, slack_webhook)
                    if response.status_code == 200:
                        self.__logger.info(f"Webhook to Slack successful.")
                    else:
                        raise Exception(f"Webhook to Slack returned an error: {response.text}")
                if discord_webhook_frontpage:
                    discord_webhook = discord_webhook_frontpage
                if discord_webhook:
                    response = self.post_to_discord(title, link, category, category_link, comments, description, image, direct_url, discord_webhook)
                    if response.status_code in [200, 204]:
                        self.__logger.info(f"Webhook to Discord successful.")
                    elif response.status_code == 429:
                        while response.status_code == 429:
                            errors = json.loads(
                                response.content.decode('utf-8'))
                            wh_sleep = (int(errors['retry_after']) / 1000) + 0.15
                            self.__logger.warning(f"Webhook rate limited: sleeping for {wh_sleep} seconds...")
                            time.sleep(wh_sleep)
                            response = self.post_to_discord(title, link, category, category_link, comments, description, image, direct_url, discord_webhook)
                            if response.status_code in [200, 204]:
                                self.__logger.info(f"Webhook to Discord successful.")
                                break
                    else:
                        raise Exception(f"Webhook to Discord returned an error: {response.text}")
            else:
                self.__logger.info(f"Breaking, as this item is up to date with last published item.")
                break

        # Update timestamp with latest deal published timestamp
        new_epoch_timestamp = self.get_timestamp(items[0].find('pubDate').text)
        if last_request_timestamp != new_epoch_timestamp:
            # If true, we're updating a frontpage timestamp
            if slack_webhook_frontpage or discord_webhook_frontpage:
                self.set_timestamp_parameter_value(
                    value=new_epoch_timestamp,
                    timestamp_file=self.timestamp_file_frontpage,
                    parameter_key=self.timestamp_parameter_key_frontpage
                )
            else:
                self.set_timestamp_parameter_value(
                    value=new_epoch_timestamp,
                    timestamp_file=self.timestamp_file,
                    parameter_key=self.timestamp_parameter_key
                )
        else:
            self.__logger.info(f"Latest deal already published to slack, no timestamp to update.")

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

    def post_to_slack(self, title, link, category, category_link, comments, description, image, direct_url, webhook):
        self.__logger.debug(f"Posting item to Slack.")
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
            webhook,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )

        return response

    def post_to_discord(self, title, link, category, category_link, comments, description, image, direct_url, webhook):
        self.__logger.debug(f"Posting item to Discord.")
        # for all params, see https://discordapp.com/developers/docs/resources/webhook#execute-webhook
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
            webhook,
            json=payload
        )

        return response

    def execute(self):
        xml_file = None
        xml_file_frontpage = None
        # If the user specifies an XML file for testing, let it override grabbing the feed from ozbargain site
        if 'OZBARGAIN_XML_FILE' in os.environ:
            xml_file = self.get_setting('OZBARGAIN_XML_FILE')
            if os.path.isfile(xml_file):
                self.__logger.warning(f"Using Deals XML file found at: {xml_file}")
            else:
                raise Exception(f"OZBARGAIN_XML_FILE specified in environment variables but file not accessible: {xml_file}")
        elif 'OZBARGAIN_XML_FILE_FRONTPAGE' in os.environ:
            xml_file_frontpage = self.get_setting('OZBARGAIN_XML_FILE_FRONTPAGE')
            if os.path.isfile(xml_file_frontpage):
                self.__logger.warning(f"Using Frontpage XML file found at: {xml_file_frontpage}")
            else:
                raise Exception(f"OZBARGAIN_XML_FILE_FRONTPAGE specified in environment variables but file not accessible: {xml_file_frontpage}")

        # Let the user override the timestamp if they wish - We want this behaviour to override both frontpage and deals
        if 'OZBARGAIN_TIMESTAMP_OVERRIDE' in os.environ:
            last_request_timestamp = int(self.get_setting('OZBARGAIN_TIMESTAMP_OVERRIDE'))
            last_request_timestamp_frontpage = int(self.get_setting('OZBARGAIN_TIMESTAMP_OVERRIDE'))
            self.__logger.warning(f"OZBARGAIN_TIMESTAMP_OVERRIDE set to: {last_request_timestamp}")
        else:
            self.__logger.info(">>> Obtaining Deals timestamp...")
            last_request_timestamp = self.get_last_request_timestamp(timestamp_file=self.timestamp_file, timestamp_parameter=self.timestamp_parameter_value)
            self.__logger.info(">>> Obtaining Frontpage timestamp...")
            last_request_timestamp_frontpage = self.get_last_request_timestamp(timestamp_file=self.timestamp_file_frontpage, timestamp_parameter=self.timestamp_parameter_value_frontpage)

        if self.slack_webhook or self.discord_webhook:
            self.__logger.info(">>> Processing Deals data...")
            xml_tree = self.get_xml_tree(self.ozbargain_feed_url, xml_file)
            self.process_data(xml_tree, last_request_timestamp, slack_webhook=self.slack_webhook, discord_webhook=self.discord_webhook)

        if self.slack_webhook_frontpage or self.discord_webhook_frontpage:
            self.__logger.info(">>> Processing Frontpage data...")
            xml_tree_frontpage = self.get_xml_tree(self.ozbargain_frontpage_feed_url, xml_file_frontpage)
            self.process_data(xml_tree_frontpage, last_request_timestamp_frontpage, slack_webhook_frontpage=self.slack_webhook_frontpage, discord_webhook_frontpage=self.discord_webhook_frontpage)
