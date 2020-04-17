# Base image
FROM python:3.7.4-slim-buster

# Update and install required build dependencies

RUN apt-get update && apt-get install nginx vim -y --no-install-recommends git

COPY nginx.default /etc/nginx/sites-available/default

RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log

# Upgrade pip
RUN pip install --upgrade pip

# Set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install project dependencies
COPY requirements.txt /
RUN pip install -r requirements.txt

# Copy code
COPY . /code/

# Set work directory
WORKDIR /code

# listen on this port
EXPOSE 8000

# Migrate and start server in dev mode on port 80
EXPOSE 80

STOPSIGNAL SIGTERM

CMD bash run.sh
