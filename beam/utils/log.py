import logging


def log_error(message):
    logger = logging.getLogger('django')
    logger.error(message)
