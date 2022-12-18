import json
import os
import wave
import boto3
import numpy as np

from typing import Dict, Tuple, Any

from timeit import default_timer as timer
from deepspeech import Model

from research.contract_parsing import metadata_json_output

AUDIO_BUCKET="ab-283419117448-s2t-audio"

session = boto3.Session(profile_name="audiobook-tools-dev")
s3 = session.client('s3')

def get_audio_s3_path(project_name="TEST_PROJECT", file_name="sherlock-holmes-sample.wav"):
  return "/".join("project-files", project_name, file_name)

def load_audio_file():
  response = s3.get_object(Bucket=AUDIO_BUCKET, Key=get_audio_s3_path())
  return wave.open(response['Body'])

def get_audio_file(audio_s3_path) -> Tuple[float, Any]:
    response = s3.get_object(Bucket=AUDIO_BUCKET, Key=audio_s3_path)
    wav = wave.open(response['Body'])
    # TODO: Figure out how framerates are configured for the model.
    framerate = wav.getframerate()
    audio_length = wav.getnframes() * (1 / framerate)
    audio_buffer = np.frombuffer(wav.readframes(wav.getnframes()), np.int16)
    return audio_length, audio_buffer

def get_model():
  model = Model("ml-inference/deepspeech-0.9.3-models.pbmm")
  model.enableExternalScorer("ml-inference/deepspeech-0.9.3-models.scorer")
  return model


# TODO: figure out how to run the model like
#   - https://github.com/mozilla/DeepSpeech/blob/master/native_client/python/client.py
#   - following: https://aws.amazon.com/blogs/machine-learning/deploy-multiple-machine-learning-models-for-inference-on-aws-lambda-and-amazon-efs/

def run_inference(model: Model):
  audio_s3_path = "transcoded-16khz/sherlock-holmes-sample.wav"
  start = timer()
  (audio_length, audio_buffer) = get_audio_file(audio_s3_path)
  duration = timer() - start
  print(f'[lambda_handler] Loading audio took {duration:.3}s.')

  start = timer()
  result = model.sttWithMetadata(audio_buffer, 1)
  duration = timer() - start
  print(f'[lambda_handler] Inference took {duration:.3}s for {audio_length:.3}s audio file.')
  return metadata_json_output(result)