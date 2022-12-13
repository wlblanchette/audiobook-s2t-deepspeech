import boto3
import wave

AUDIO_BUCKET="ab-283419117448-s2t-audio"

session = boto3.Session(profile_name="audiobook-tools-dev")
s3 = session.client('s3')

def get_audio_s3_path(project_name="TEST_PROJECT", file_name="sherlock-holmes-sample.wav"):
  return "/".join("project-files", project_name, file_name)

def load_audio_file():
  response = s3.get_object(Bucket=AUDIO_BUCKET, Key=get_audio_s3_path())
  return wave.open(response['Body'])


# TODO: figure out how to run the model like
#   - https://github.com/mozilla/DeepSpeech/blob/master/native_client/python/client.py
#   - following: https://aws.amazon.com/blogs/machine-learning/deploy-multiple-machine-learning-models-for-inference-on-aws-lambda-and-amazon-efs/