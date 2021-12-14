from datetime import datetime, timedelta
import time
import boto3
import requests
import json
import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

class Ozbargain():
    def __init__(self, logger) -> None:
        self.__logger = logger
        self.slack_webhook = self.get_setting('slack_webhook')
        self.__logger.debug(f'slack_webhook url: {self.slack_webhook}')
        self.ozbargain_feed_url = 'https://www.ozbargain.com.au/deals/feed'
        self.ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION'])
        self.default_timedelta_minutes = 5
        self.namespace = {'ozb': 'https://www.ozbargain.com.au'}

    def validate(self):
        self.__logger.info("Validating...")
        if not self.slack_webhook:
            raise Exception("No slack Webhook defined in environment variable 'SLACK_WEBHOOK'")
        if not self.ssm:
            raise Exception("Unable to connect to SSM.")
        if not os.environ['CURL_COOKIE']:
            raise Exception("Unable to locate required curl cookie.")
        if not os.environ['OZBARGAIN_TIMESTAMP_PARAMETER']:
            raise Exception("'OZBARGAIN_TIMESTAMP_PARAMETER' environment variable for SSM parameter store string required.")

    def get_ssm_parameter_value(self, parameter_path):
        parameter = self.ssm.get_parameter(
            Name=parameter_path, 
            WithDecryption=True)
        result = parameter['Parameter']['Value']
        return result

    def set_ssm_parameter_value(self, parameter_path, value):
        parameter = self.ssm.put_parameter(
            Name=parameter_path,
            Value=str(value),
            Type='String',
            Overwrite=True
        )
        self.__logger.info(f"Updated SSM parameter '{parameter_path}' to '{value}'.")
        return parameter

    def get_setting(self, setting_name):
        envVar = setting_name.upper()
        paramPath = f'{envVar}_PARAMETER'
        if envVar in os.environ:
            return os.environ[envVar]
        elif paramPath in os.environ:
            return self.get_ssm_parameter_value(os.environ[paramPath])
        else:
            raise Exception(f"You must specify either {envVar} or {paramPath}")

    def get_xml_tree(self):
        self.__logger.info("Getting XML Tree...")
        curl_cookie = self.get_setting('curl_cookie')
        headers = {}
        headers['cache-control'] = "max-age=0"
        headers['cookie'] = f"G_ENABLED_IDPS=google; PHPSESSID={curl_cookie}"
        xml_feed = requests.get(self.ozbargain_feed_url, headers=headers)
        xml_tree = ET.fromstring(xml_feed.content)
        return xml_tree

    def get_last_request_timestamp(self):
        try:
            self.__logger.info("getting timestamp from SSM...")
            last_request_timestamp = int(self.get_setting('ozbargain_timestamp'))
        except Exception as e:
            self.__logger.error(f"unable to obtain last published timestamp from SSM, generating one... error: {e}")
            last_request_timestamp = int(time.mktime((datetime.now() - timedelta(minutes=self.default_timedelta_minutes)).timetuple()))
        self.__logger.debug(f"last_request_timestamp: {last_request_timestamp}")
        return last_request_timestamp

    def get_deal_data(self, item):
        # Certain characters need to be stripped So that they don't break the formatting of the slack messages.
        strip_items_title = ["&", "<", ">", "*"]
        strip_items_other = ["&", "{", "}", "*"]
        title = item.find('title').text
        title = self.strip_items(strip_items_title, title)
        self.__logger.debug(f'title: {title}')
        pub_date = item.find('pubDate').text
        self.__logger.debug(f'pub_date: {pub_date}')
        link = item.find('link').text
        link = self.strip_items(strip_items_other, link)
        self.__logger.debug(f'link: {link}')
        category = item.find('category').text
        category = self.strip_items(strip_items_other, category)
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
        image = item.find('ozb:meta', self.namespace).attrib['image']
        image = self.strip_items(strip_items_other, image)
        self.__logger.debug(f'image: {image}')
        if not image:
            image = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/300px-No_image_available.svg.png"
        direct_url = item.find('ozb:meta', self.namespace).attrib['url']
        self.__logger.debug(f'direct_url: {direct_url}')
        return title, pub_date, link, category, category_link, comments, description, image, direct_url

    def get_timestamp(self, time_to_convert):
        # Gets a string timestamp, converts it to time from epoch for ez calculations.
        converted_timestamp = datetime.strptime(time_to_convert, "%a, %d %b %Y %X %z")
        self.__logger.debug(f'converted timestamp to datetime object for {time_to_convert}: {converted_timestamp}')
        epoch_timestamp = int(datetime.fromisoformat(str(converted_timestamp)).timestamp())
        self.__logger.debug(f'timestamp since epoch for {time_to_convert}: {epoch_timestamp}')
        return epoch_timestamp
    
    def strip_items(self, strip_chars, string):
        # Function to Search and Replace string for encoding Unicode Characters to URL encoded characters
        # so Slack can interpret them Instead of breaking the formatting.
        for item in strip_chars:
            string = string.replace(item, '')
        return string

    def ready_payload(self, title, link, category, category_link, comments, description, image, direct_url):
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
        return payload

    def post_to_slack(self, payload):
        response = requests.post(
            self.slack_webhook,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            verify=False
        )
        return response.status_code, response.text
