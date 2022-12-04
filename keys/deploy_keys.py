import json
import os
import re
import sys

import keys.secrets as secrets

class COLOR:
    ERROR_COLOR = '\033[1;31m'
    INFO_COLOR = '\033[1;32m'
    WARN_COLOR = '\033[1;33m'
    NO_COLOR = '\033[0m'
    ORANGE = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'


KEY_ALIAS_NAME = 'alias/MSSecrets'
LOG_HEADER = f'{COLOR.INFO_COLOR}[deploy_keys]{COLOR.NO_COLOR}'


def _get_key_id(aliasName):
    return json.loads(os.popen(f'aws kms describe-key --key-id {aliasName}').read())['KeyMetadata']['KeyId']


def _get_deploy_command(name, key_id, value, overwrite_clause):
    return f'aws ssm put-parameter --name {name} --key-id "{key_id}" --type SecureString --value "{value}" --region us-east-1{overwrite_clause}'  # noqa: E501

# Deploy keys under the path f'/{key_name}/{env}/{secret[0]}'
#  -- key_name = the top level key in ./secrets.py
#  -- env = 'live'
#  -- secret[0] = name of the secret keys under [key_name].live in ./secrets.py
def deploy_keys(key_name, secrets, args, key_id):
    commands = []
    overwrite_clause = ' --overwrite' if 'overwrite' in args else ''
    for pair in secrets.items():
        env = pair[0]
        for secret in pair[1].items():
            name = f'/{key_name}/{env}/{secret[0]}'
            commands.append(f'printf "\n{COLOR.ORANGE}|{COLOR.YELLOW} {name}{COLOR.NO_COLOR}"')
            commands.append(_get_deploy_command(name, key_id, secret[1], overwrite_clause))

    return commands

def _cluster_args_dict(*args):
    result = {}
    is_key = r'^--'
    r = range(len(args))
    for i in r:
        key = re.sub(is_key, '', args[i])
        if re.match(is_key, args[i]) and i + 1 in r and not re.match(is_key, args[i + 1]):
            result[key] = args[i + 1]
            continue
        if re.match(is_key, args[i]):
            result[key] = ''
    return result

def _secrets_to_ignore(args):
    if args.get('ignore'):
        return args.get('ignore').split(',')
    return []

if __name__ == '__main__':
    args = _cluster_args_dict(*sys.argv[1:])
    key_id = _get_key_id(KEY_ALIAS_NAME)
    ignored_secrets = _secrets_to_ignore(args)
    keys = [n for n in dir(secrets) if not n.startswith('__') and n not in ignored_secrets]
    if not 'overwrite' in args: print(f'{LOG_HEADER} {COLOR.ORANGE}!dry_run!{COLOR.NO_COLOR}')
    print(f'{LOG_HEADER} running (args: {args})')
    print(f'{LOG_HEADER} key_id {key_id}')
    print(f'{LOG_HEADER} keys {keys}')
    for key in keys:
        try:
            commands = deploy_keys(key, getattr(secrets, key), args, key_id)
            for c in commands:
                os.system(c)
        except Exception as e:
            print(e)
            print(f'{COLOR.ERROR_COLOR}Oops!{COLOR.NO_COLOR} Issue running {r}, but forging ahead!')
