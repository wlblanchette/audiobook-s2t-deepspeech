# script-to-audio
Backend for the twitter emotion map project

## To Deploy
First, make sure an AWS profile `audiobook-tools-dev` is configured.
1. `make ecr-login`
2. `make deploy`

## Uploading Models
### Downloading pre-trained Deepspeech models
A Make command can be used:
* `make download-models`

Original instructions can be found [here](https://deepspeech.readthedocs.io/en/r0.9/?badge=latest). For pre-trained English model files:
* `curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm`
* `curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer`

### Upload the models to S3
...