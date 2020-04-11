#!/bin/bash

# Django settings
export SECRET_KEY=''
export DEBUG=True
export TEMPLATE_DEBUG=DEBUG
export ALLOWED_HOSTS=0.0.0.0,127.0.0.1,localhost

# Database settings
export DB_NAME=''
export DB_USER=''
export DB_PASSWORD=''
export DB_HOST='127.0.0.1'
export DB_PORT='3306'

# Fyle Settings
export BASE_URL='https://staging.fyle.in'
export FYLE_BASE_URL='https://accounts.staging.fyle.in'
export CLIENT_ID=''
export CLIENT_SECRET=''
export AUTHORIZE_URI='{0}/app/developers/#/oauth/authorize'
export REDIRECT_URI='http://localhost:8000/main/callback/'
export TOKEN_URI='{0}/api/oauth/token'
export FYLE_JOBS_URL=''
export FYLE_JOBS_CALLBACK_URL='http://localhost:8000/fetcher/callback/'

export DOWNLOAD_PATH='/tmp/'
export CLOUD_STORAGE_PROVIDER='awss3'

# AWS settings
export AWS_ACCESS_KEY_ID=''
export AWS_SECRET_ACCESS_KEY=''
export S3_BUCKET_NAME=''
export S3_REGION_NAME=''
export PRESIGNED_URL_EXPIRY=3600

# Email settings
export SENDGRID_API_KEY=''
export SENDER_EMAIL_ID=''

# Creds for testing
export TEST_REFRESH_TOKEN=''
export TEST_FYLE_ORG_ID=''