import boto3
import json
import numpy as np
import os
import wave
from deepspeech import Model
from timeit import default_timer as timer
from typing import Dict, Tuple, Any

from polyjuice_common import s3 as pjs3, sns as pjsns, common as pjcommon

from contract_parsing import metadata_json_output

TEMP_FILE_NAME = "/tmp/temp.json"
MODEL_PATH = "./deepspeech-0.9.3-models.pbmm"
SCORER_PATH = "./deepspeech-0.9.3-models.scorer"
get_starting_dir = lambda project_id: pjs3.get_project_path(project_id, "ml-audio-transcoded-16khz")
get_output_dir = lambda project_id: pjs3.get_project_path(project_id, "ml-audio-transcripts")

# Cache readers in memory to avoid downloading again
# Note that if using large number of models, you'll have to write an LRU cache as this map will overflow on memory.
MODEL_CACHE: Dict[str, Model] = {}
CACHE_KEY = 'MODEL'

def isPing(event):
    return 'isWarmerEvent' in event

s3 = boto3.client('s3')
s3_resource = boto3.resource('s3')

def get_audio_file(bucket_name: str, audio_s3_path: str) -> Tuple[float, Any]:
    response = s3.get_object(Bucket=bucket_name, Key=audio_s3_path)
    wav = wave.open(response['Body'])
    # TODO: Figure out how framerates are configured for the model.
    framerate = wav.getframerate()
    audio_length = wav.getnframes() * (1 / framerate)
    audio_buffer = np.frombuffer(wav.readframes(wav.getnframes()), np.int16)
    return audio_length, audio_buffer

# TODO: Should explore some of this writing too https://datatalks.club/blog/ml-deployment-lambda.html#future-enhancements-and-tradeoffs.
@pjcommon.decorate_log_event
@pjsns.unpack_sns_message
@pjs3.handle_s3_notification_events('sns_payload')
def lambda_handler(event, context, key: str, bucket_name: str, **kwargs):
    if isPing(event):
        print(f'------ cache was active: {CACHE_KEY in MODEL_CACHE} ------')
        if CACHE_KEY not in MODEL_CACHE:
            print(f"[lambda_handler] model not cached")
            MODEL_CACHE[CACHE_KEY] = Model(MODEL_PATH)
        print(f'------ cache is now active: {CACHE_KEY in MODEL_CACHE} ------')
        print(f'------ function is warm  ------')
        return

    # This function picks up transcoded audio drops within project directories
    project_id = pjs3.get_project_from_key(key)
    if not project_id or get_starting_dir(project_id) not in key:
        print(f"---- Won't transcribe key: {key} ----")
        return

    print(f'[lambda_handler] key', key)
    print(f'[lambda_handler] bucket_name', bucket_name)

    #
    # Load Audio File
    #
    audio_load_start = timer()
    (audio_length, audio_buffer) = get_audio_file(bucket_name, key)
    audio_load_duration = timer() - audio_load_start
    print(f"[lambda_handler] Loaded audio in {audio_load_duration:.3}s.")

    #
    # Load DeepSpeech Model and Scorer
    #
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

    #
    # Make Inference
    #
    inference_start = timer()
    result = model.sttWithMetadata(audio_buffer, 1)
    inference_duration = timer() - inference_start
    print(f'[lambda_handler] Inference took {inference_duration:.3}s for {audio_length:.3}s audio file.')

    #
    # Upload results to S3
    #
    json_output = metadata_json_output(result)
    (_, filename) = os.path.split(key)
    new_key = "/".join([get_output_dir(project_id), f"{filename}.json"])

    obj = s3_resource.Object(bucket_name, new_key)
    obj.put(Body=bytes(json_output.encode('UTF-8')))

    return { 'statusCode': 200 }
