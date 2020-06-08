#!/bin/bash

# Django settings
export SECRET_KEY='YOUR SECRET_KEY'
export DEBUG=True
export TEMPLATE_DEBUG=DEBUG
export ALLOWED_HOSTS='ALLOWED_HOSTS'

# Database settings
export DB_NAME='YOUR DB_NAME'
export DB_USER='YOUR DB_USER'
export DB_PASSWORD='YOUR DB_PASSWORD'
export DB_HOST='YOUR DB_HOST'
export DB_PORT='YOUR DB_PORT'
export DB_SCHEMA='public'

# Fyle Settings
export BASE_URL='YOUR BASE_URL'
export FYLE_BASE_URL='YOUR FYLE_BASE_URL'
export FYLE_CLIENT_ID='YOUR FYLE_CLIENT_ID'
export FYLE_CLIENT_SECRET='YOUR FYLE_CLIENT_SECRET'
export FYLE_AUTHORIZE_URI='YOUR FYLE_AUTHORIZE_URI'
export FYLE_CALLBACK_URI='YOUR FYLE_CALLBACK_URI'
export FYLE_TOKEN_URI='YOUR FYLE_TOKEN_URI'
export FYLE_JOBS_URL='YOUR FYLE_JOBS_URL'
export FYLE_JOBS_CALLBACK_URL='YOUR FYLE_JOBS_CALLBACK_URL'
export DOWNLOAD_PATH='/tmp/'

# Creds for testing
export TEST_REFRESH_TOKEN=''
export TEST_FYLE_ORG_ID=''
