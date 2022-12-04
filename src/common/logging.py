import logging
import os


def running_in_aws():
    return bool(os.environ.get('AWS_EXECUTION_ENV'))


def get_logger(name="DEFAULT_LOGGER", level='INFO'):
    """
    Helper to set up logging consistently across all lambda functions.
    Configures both a named logger and the root logger.

    Args:
        name: (str) - the name of the logger that will be configured along with the root logger
        level: (str) - The log level to use.  Default is INFO.

    Returns:
        Object: Logger object
    """
    # __LAMBDA_FORMAT__ = (
    #     '%(asctime)s.%(msecs)-3d (Z)\t%(aws_request_id)s\t'
    #     '[%(levelname)-12s]\t%(message)s\n'
    # )
    __STANDARD_FORMAT__ = (
        '%(asctime)s.%(msecs)-3d (Z)\t%(name)s\t'
        '[%(levelname)-12s]\t%(message)s\n'
    )
    #
    logger = logging.getLogger(name)
    log_level = os.environ.get('LOG_LEVEL', level)
    logging.basicConfig(format=__STANDARD_FORMAT__)
    logger.setLevel(logging.getLevelName(log_level))
    return logger
