# syntax=docker/dockerfile:1

FROM python:3.10-alpine

WORKDIR /app
COPY ./bots ./bots
COPY ./app.py ./
COPY requirements.txt ./

RUN set -ex \
    && apk add --no-cache git \
    && python3 -m pip install --upgrade pip \
    && pip install -r requirements.txt

ENTRYPOINT [ "python", "app.py" ]
