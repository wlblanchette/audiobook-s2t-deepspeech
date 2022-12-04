import boto3
import boto3.dynamodb.types

from src.common.logging import get_logger

log = get_logger(name="dynamo", level="DEBUG")

def table(name):
    """Return a boto3 DynamoDB.Table for the table name.
    Args:
        name (str): the base name of the table
    Returns:
        table (Table): boto3 DynamoDB.Table
    """

    logger.debug(f'Connecting to {name} table using default endpoint')
    return boto3.resource('dynamodb').Table(name)
