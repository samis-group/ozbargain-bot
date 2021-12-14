import os
from lib.app import Ozbargain
from lib.logger import Logger

def lambda_handler(event, context):
    verbose = os.environ.get('VERBOSE', 'false').lower() == 'true'
    try:
        logger = Logger(coloured=False).get_logger(verbose)
        ozbargain = Ozbargain(logger)
        ozbargain.validate()
        xml_tree = ozbargain.get_xml_tree()
        last_request_timestamp = ozbargain.get_last_request_timestamp()
        channel = xml_tree.find('channel')
        items = list(channel.iterfind('item'))
        for item in items:
            title, pub_date, link, category, category_link, comments, description, image, direct_url = ozbargain.get_deal_data(item)
            epoch_pub_date = ozbargain.get_timestamp(pub_date)
            if epoch_pub_date > last_request_timestamp:
                payload = ozbargain.ready_payload(title, link, category, category_link, comments, description, image, direct_url)
                response_code, response_text = ozbargain.post_to_slack(payload)
                if response_code != 200:
                    raise Exception(f"Request to slack returned an error: {response_text}")
                else:
                    logger.info(f"item processed successfully:\n{title}")
            else:
                logger.info(f"Breaking, as this item is up to date with last published to slack:\n{title}")
                break
        # Update timestamp SSM param with latest deal published timestamp
        new_epoch_timestamp = ozbargain.get_timestamp(items[0].find('pubDate').text)
        if last_request_timestamp != new_epoch_timestamp:
            ozbargain.set_ssm_parameter_value(
                parameter_path=os.environ['OZBARGAIN_TIMESTAMP_PARAMETER'],
                value=new_epoch_timestamp
            )
        else:
            logger.debug(f"Latest deal already published to slack.")
    except Exception as ex:
        error = f'Handler failed! {ex}'
        if logger is None:
            print(error)
        else:
            logger.error(f">>> Error: {error}")
        raise ex
