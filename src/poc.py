import json
import sentry_sdk
from sentry_sdk import capture_exception
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from src.common.logging import get_logger

log = get_logger(name="poc.handler", level="DEBUG")

sentry_sdk.init(
    dsn="https://87fb01dc12e74d52a792dc2e073996d4@sentry.io/1829747",
    integrations=[AwsLambdaIntegration()]
)


# Doing a rigid pipeline like this with rigid intermediary data structures
# is probably not going to work well if strategies are using completely
# different brokerages and APIs.
def handler(event, context):
    """
    Parameters
    ----------
    queryStringParameters:
        - name (Required)          fred or george
    """
    try:
        body = json.loads(event.get('body'))
        log.debug(f'[handler]: body {body}')

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "hello!",
            }),
        }
    except Exception as e:
        log.exception(e)
        capture_exception(e)
        return {"statusCode": 500}
