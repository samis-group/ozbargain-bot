import logging

class Logger:

    def __init__(self, coloured=True):
        self.__formatter = ColoredFormatter() if coloured else StandardFormatter()

    def get_logger(self, verbose=True, name='ozbargainbot'):
        log_level = logging.DEBUG if verbose else logging.INFO
        logger = logging.getLogger(name)
        if (logger.hasHandlers()):
            logger.handlers.clear()
        handler = logging.StreamHandler()
        handler.setLevel(log_level)
        handler.setFormatter(self.__formatter)
        logger.addHandler(handler)
        logger.setLevel(log_level)
        # Silence the noisy boto loggers...
        boto_and_friends_logging_level = logging.INFO if verbose else logging.WARN
        for logger_name in ['boto', 'botocore', 'boto3', 'nose', 'urllib3', 's3transfer']:
            logging.getLogger(logger_name).setLevel(boto_and_friends_logging_level)
        return logger

class StandardFormatter(logging.Formatter):
    FORMAT_NORMAL = f'%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
    FORMAT_DETAILED = f'%(asctime)s [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)'
    FORMATS = {
        logging.DEBUG: FORMAT_NORMAL,
        logging.INFO: FORMAT_NORMAL,
        logging.WARNING: FORMAT_NORMAL,
        logging.ERROR: FORMAT_DETAILED,
        logging.CRITICAL: FORMAT_DETAILED
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.datefmt = '%H:%M:%S'
        return formatter.format(record)

class ColoredFormatter(logging.Formatter):
    COLOR_GREY = "\x1b[38;21m"
    COLOR_GREEN = "\x1b[32;21m"
    COLOR_YELLOW = "\x1b[33;21m"
    COLOR_RED = "\x1b[31;21m"
    COLOR_BOLD_RED = "\x1b[31;1m"
    COLOR_RESET = "\x1b[0m "
    FORMAT_NORMAL = f'%(asctime)s [%(name)s] [%(levelname)s] %(message)s'
    FORMAT_DETAILED = f'%(asctime)s [%(name)s] [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)'
    FORMATS = {
        logging.DEBUG: COLOR_GREY + FORMAT_NORMAL + COLOR_RESET,
        logging.INFO: COLOR_GREEN + FORMAT_NORMAL + COLOR_RESET,
        logging.WARNING: COLOR_YELLOW + FORMAT_NORMAL + COLOR_RESET,
        logging.ERROR: COLOR_RED + FORMAT_DETAILED + COLOR_RESET,
        logging.CRITICAL: COLOR_BOLD_RED + FORMAT_DETAILED + COLOR_RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        formatter.datefmt = '%H:%M:%S'
        return formatter.format(record)
