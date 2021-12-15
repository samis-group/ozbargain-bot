import os
from lib.app import Ozbargain
from lib.logger import Logger

def lambda_handler(event, context):
    verbose = os.environ.get('VERBOSE', 'false').lower() == 'true'
    logger = Logger(coloured=False).get_logger(verbose)
    try:
        ozbargain = Ozbargain(logger)
        ozbargain.execute()
    except Exception as ex:
        error = f'Handler failed! {ex}'
        if logger is None:
            print(error)
        else:
            logger.error(f">>> Error: {error}")
        raise ex

# Local testing - invoke the script directly
if __name__ == "__main__":
    verbose = os.environ.get('VERBOSE', 'false').lower() == 'true'
    logger = Logger().get_logger(verbose)
    ozbargain = Ozbargain(logger)
    ozbargain.execute()
