ERROR_COLOR="\033[1;31m"
INFO_COLOR="\033[1;32m"
WARN_COLOR="\033[1;33m"
NO_COLOR="\033[0m"

FEATURE_NAME=s2t-deepspeech

AWS_ACCOUNT=283419117448
BUCKET_NAME=ab-${AWS_ACCOUNT}-${FEATURE_NAME}
BUCKET_URL=s3://${BUCKET_NAME}
STACK_NAME=${FEATURE_NAME}
AWS_PROFILE=audiobook-tools-dev
ECR_REPOSITORY_URI=${AWS_ACCOUNT}.dkr.ecr.us-east-1.amazonaws.com/polyjuice-ml


### Developer Functions ###
function pj_lint() {
	echo "${INFO_COLOR}cfn-lint...${NO_COLOR}\n"
	cfn-lint template.yaml
	echo "${INFO_COLOR}flake8...${NO_COLOR}\n"
	flake8
}

function pj_lint() {
	autopep8 --ignore E265,E266,E402,E302 --in-place --recursive --max-line-length=120 --exclude vendored .
}

function pj_init() {
	pip install -r ./requirements-dev.txt
}

function pj_clean_sam() {
  rm -r .aws-sam
  rm packaged.yaml
}

function pj_clean_all() {
  find . -path "*.egg-info" -exec rm -r {} \;
  find . -path "*build*" -exec rm -r {} \;
  rm -r .aws-sam
}


### Deployments and Testing ###
function pj_deploy() {
  readonly template_name=${1:?"template path"}
  readonly parameter_overrides=${2}
  STACK_NAME="$FEATURE_NAME--$subproject"

  echo "🌴 Configuration"
  echo "----------------"
  echo "Template Name: $template_name"
  echo "Parameter Overrides: $parameter_overrides"
  echo "AWS Account: $AWS_ACCOUNT"
  echo "AWS Profile: $AWS_PROFILE"
  echo "Bucket Name: $BUCKET_NAME"
  echo "Stack Name: $STACK_NAME"
  echo "----------------"

  # TODO: this is only necessary when local moduels are shared
  #       via pip installation
  echo "🌴 ${INFO_COLOR}pip...${NO_COLOR}\n"
  pip install -r requirements-dev.txt

  echo "🌴 ${INFO_COLOR}Building...${NO_COLOR}\n"
  sam build -t $template_name --use-container

  echo "🌴 ${INFO_COLOR}Packaging...${NO_COLOR}\n"
  sam package \
    --output-template-file packaged.yaml \
    --s3-bucket ${BUCKET_NAME} \
    --profile ${AWS_PROFILE} \
    --image-repository ${ECR_REPOSITORY_URI}

  local deploy_cmd="sam deploy "
  deploy_cmd+="--template-file packaged.yaml "
  deploy_cmd+="--region us-east-1 "
  deploy_cmd+="--capabilities CAPABILITY_IAM "
  deploy_cmd+="--stack-name ${STACK_NAME} "
  deploy_cmd+="--profile ${AWS_PROFILE} "
  deploy_cmd+="--image-repository ${ECR_REPOSITORY_URI} "
  if [[ -n $parameter_overrides ]]
  then
    echo $parameter_overrides
    deploy_cmd+="--parameter-overrides $parameter_overrides "
  fi
  echo "🌴 ${INFO_COLOR}Deploying...${NO_COLOR}\n"
  echo "🌴 (cmd: $deploy_cmd)"
  eval $deploy_cmd
}

function pj_config() {
	echo "AWS_ACCOUNT: ${AWS_ACCOUNT}"
	echo "BUCKET_URL: ${BUCKET_URL}"
}

# ---- Project specific ----
function pj_deploy_ml_inference() {
  pj_deploy template-ml-inference.yaml
}

function pj_download_models() {
  curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
	curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer
}

function pj_test_inference() {
  readonly audio_s3_path=${1:?"audio_s3_path is required"}
  local inference_api_url=$(aws cloudformation describe-stacks --profile $AWS_PROFILE | jq -r '.Stacks[] | select(.StackName == "s2t-deepspeech") | .Outputs[] | select(.OutputKey == "InferenceApi") | .OutputValue')
  http POST $inference_api_url audio_s3_path=$audio_s3_path
}

function pj_list_audio_files() {
  aws s3 ls s3://ab-283419117448-s2t-audio/transcoded-16khz/ --profile audiobook-tools-dev
}
