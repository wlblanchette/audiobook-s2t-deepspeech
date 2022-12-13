ERROR_COLOR = \033[1;31m
INFO_COLOR = \033[1;32m
WARN_COLOR = \033[1;33m
NO_COLOR = \033[0m

FEATURE_NAME=s2t-deepspeech

AWS_ACCOUNT=283419117448
BUCKET_NAME=ab-${AWS_ACCOUNT}-${FEATURE_NAME}
BUCKET_URL=s3://${BUCKET_NAME}
STACK_NAME=${FEATURE_NAME}
AWS_PROFILE=audiobook-tools-dev
ECR_REPOSITORY_URI=${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/polyjuice-ml

#################
#
# General Targets
#
#################
.PHONY: lint
lint:
	@printf "${INFO_COLOR}cfn-lint...${NO_COLOR}\n"
	cfn-lint template.yaml
	@printf "${INFO_COLOR}flake8...${NO_COLOR}\n"
	flake8

lint-fix: $(PYTHON_DEPENDENCY_FILE)
	cd autopep8 --ignore E265,E266,E402,E302 --in-place --recursive --max-line-length=120 --exclude vendored .

test:
	@pytest -sv

init:
	@pip install -r ./requirements.txt

download-models:
	@curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
	@curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer

config:
	@printf "AWS_ACCOUNT: ${AWS_ACCOUNT}\n"
	@printf "BUCKET_URL: ${BUCKET_URL}\n"

ecr-login:
	@aws ecr get-login-password --region us-east-1 | docker login --username AWS \
--password-stdin $(AWS_ACCOUNT).dkr.ecr.us-east-1.amazonaws.com

deploy:
	@printf "${INFO_COLOR}Building...${NO_COLOR}\n" && \
	sam build --use-container && \
	printf "${INFO_COLOR}Packaging...${NO_COLOR}\n" && \
	sam package --output-template-file packaged.yaml --s3-bucket ${BUCKET_NAME} --profile ${AWS_PROFILE} --image-repository ${ECR_REPOSITORY_URI} && \
	printf "${INFO_COLOR}Deploying...${NO_COLOR}\n" && \
	sam deploy --template-file packaged.yaml --region us-east-1 --capabilities CAPABILITY_IAM --stack-name ${STACK_NAME} --profile ${AWS_PROFILE} --image-repository ${ECR_REPOSITORY_URI}

deploy-packaged:
	@sam deploy --template-file packaged.yaml --region us-east-1 --capabilities CAPABILITY_IAM --stack-name ${STACK_NAME} --profile ${AWS_PROFILE} --image-repository ${ECR_REPOSITORY_URI}

# deploy-keys:
# 	@python -m keys.deploy_keys --ignore TD_AMERITRADE,TRADESTATION

# deploy-keys-overwrite:
# 	@python -m keys.deploy_keys --ignore TD_AMERITRADE,TRADESTATION --overwrite

describe-parameters:
	@aws ssm describe-parameters

invoke:
	@printf "${INFO_COLOR}Building...${NO_COLOR}\n" && \
	sam build --use-container && \
	printf "${INFO_COLOR}Invoking...${NO_COLOR}\n" && \
	sam local invoke --event ./events/query_params.json

test-poc:
	@http POST https://xmnhv13j2d.execute-api.us-east-1.amazonaws.com/Prod/hello \
	  name=fred

test-inference:
	@http POST https://7p9arazyci.execute-api.us-east-1.amazonaws.com/Prod/deepspeech \
	  audio_s3_path=project-files/TEST_PROJECT/sherlock-holmes-sample.wav