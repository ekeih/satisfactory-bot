FROM python:3.13-alpine

ARG BOT_VERSION_ARG
ENV BOT_VERSION=${BOT_VERSION_ARG:-0.0.0}

RUN apk add --no-cache gcc g++ musl-dev libffi-dev

WORKDIR /usr/src/app

COPY README.md requirements.txt setup.py ./
RUN pip3 --no-cache-dir --disable-pip-version-check install -r requirements.txt
RUN apk del gcc musl-dev libffi-dev

COPY satisfactory satisfactory
RUN pip3 --no-cache-dir --disable-pip-version-check install .

USER guest
ENTRYPOINT [ "satisfactory-bot" ]
