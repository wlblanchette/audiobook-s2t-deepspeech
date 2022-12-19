# Pull the base image with python 3.8 as a runtime for your Lambda
FROM public.ecr.aws/lambda/python:3.8

# Copy the dir into container
COPY ./ ./

# RUN cat /etc/os-release
RUN yum install -y git

# Install the python requirements from requirements.txt
RUN python3.8 -m pip install -r requirements.txt

# Set the CMD to your handler
CMD ["app.lambda_handler"]
