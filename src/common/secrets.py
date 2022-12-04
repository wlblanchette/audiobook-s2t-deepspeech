import boto3

client = boto3.client('ssm')

def _get_configuration(ssm_parameter_path):
    """
    Load configparser from config stored in SSM Parameter Store
    :param ssm_parameter_path: Path to app config in SSM Parameter Store
    :return: ConfigParser holding loaded config
    """
    configuration = {}
    try:
        # Get all parameters for this app
        param_details = client.get_parameters_by_path(
            Path=ssm_parameter_path,
            Recursive=False,
            WithDecryption=True
        )

        # Loop through the returned parameters and populate the ConfigParser
        if 'Parameters' in param_details and len(param_details.get('Parameters')) > 0:
            for param in param_details.get('Parameters'):
                param_path_array = param.get('Name').split("/")
                section_name = param_path_array[len(param_path_array) - 1]
                configuration[section_name] = param.get('Value')

    except Exception as e:
        print("Encountered an error loading config from SSM.", e)
    finally:
        return configuration


def get_secrets(ssm_parameter_path):
    return _get_configuration(ssm_parameter_path)
