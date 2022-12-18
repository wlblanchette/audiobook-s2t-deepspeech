import json
import os
import wave
import boto3
import numpy as np

from typing import Dict, Tuple, Any

from timeit import default_timer as timer
from deepspeech import Model

from contract_parsing import metadata_json_output


MODEL_PATH = "./deepspeech-0.9.3-models.pbmm" # os.getenv('MODEL_PATH', "/mnt/ml/models/deepspeech-0.9.3-models.pbmm")
SCORER_PATH = "./deepspeech-0.9.3-models.scorer" # os.getenv('SCORER_PATH', "/mnt/ml/models/deepspeech-0.9.3-models.scorer")
AUDIO_BUCKET = os.getenv('AUDIO_BUCKET', "ab-283419117448-s2t-audio")

# Cache readers in memory to avoid downloading again
# Note that if using large number of models, you'll have to write an LRU cache as this map will overflow on memory.
MODEL_CACHE: Dict[str, Model] = {}
CACHE_KEY = 'MODEL'

def isPing(event):
    return 'isWarmerEvent' in event

s3 = boto3.client('s3')

def get_audio_file(audio_s3_path) -> Tuple[float, Any]:
    response = s3.get_object(Bucket=AUDIO_BUCKET, Key=audio_s3_path)
    wav = wave.open(response['Body'])
    # TODO: Figure out how framerates are configured for the model.
    framerate = wav.getframerate()
    audio_length = wav.getnframes() * (1 / framerate)
    audio_buffer = np.frombuffer(wav.readframes(wav.getnframes()), np.int16)
    return audio_length, audio_buffer

# TODO: refactor this to respond to S3 events in transcoded project directories
#       and create corresponding metadata files.
#       Should explore some of this writing too https://datatalks.club/blog/ml-deployment-lambda.html#future-enhancements-and-tradeoffs.
def lambda_handler(event, context):
    if isPing(event):
        print(f'------ cache was active: {CACHE_KEY in MODEL_CACHE} ------')
        if CACHE_KEY not in MODEL_CACHE:
            print(f"[lambda_handler] model not cached")
            MODEL_CACHE[CACHE_KEY] = Model(MODEL_PATH)
        print(f'------ cache is now active: {CACHE_KEY in MODEL_CACHE} ------')
        print(f'------ function is warm  ------')
        return

    # Reading the body to extract the URL and the language
    body = json.loads(event['body'])
    audio_s3_path = body.get('audio_s3_path', "project-files/TEST_PROJECT/sherlock-holmes-sample.wav")
    print(f'[lambda_handler] audio_s3_path', audio_s3_path)

    audio_load_start = timer()
    (audio_length, audio_buffer) = get_audio_file(audio_s3_path)
    audio_load_duration = timer() - audio_load_start
    print(f"[lambda_handler] Loaded audio in {audio_load_duration:.3}s.")

    model_load_start = timer()
    if CACHE_KEY not in MODEL_CACHE:
        print(f"[lambda_handler] model not cached")
        MODEL_CACHE[CACHE_KEY] = Model(MODEL_PATH)
    model = MODEL_CACHE[CACHE_KEY]
    model_load_duration = timer() - model_load_start
    print(f'[lambda_handler] Loaded model in {model_load_duration:.3}s.')

    scorer_load_start = timer()
    model.enableExternalScorer(SCORER_PATH)
    scorer_load_duration = timer() - scorer_load_start
    print(f'[lambda_handler] Loaded scorer in {scorer_load_duration:.3}s.')

    inference_start = timer()
    result = model.sttWithMetadata(audio_buffer, 1)
    inference_duration = timer() - inference_start
    print(f'[lambda_handler] Inference took {inference_duration:.3}s for {audio_length:.3}s audio file.')


    # Function Return
    return {
        'statusCode': 200,
        'body': metadata_json_output(result)
    }