# syntax=docker/dockerfile:1.7

FROM python:3.10-alpine

ENV PIP_DEFAULT_TIMEOUT=120 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN set -ex \
    && apk add --no-cache git

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    set -ex; \
    for attempt in 1 2 3; do \
        python3 -m pip install --retries 10 -r requirements.txt && exit 0; \
        if [ "${attempt}" -eq 3 ]; then exit 1; fi; \
        echo "pip install failed; retrying (${attempt}/3)"; \
    done

COPY ./bots ./bots
COPY ./app.py ./

ENTRYPOINT [ "python", "app.py" ]
