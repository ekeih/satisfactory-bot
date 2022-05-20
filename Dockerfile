FROM python:3.10-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /usr/src/app

COPY README.md requirements.txt setup.py ./
RUN pip3 --no-cache-dir --disable-pip-version-check install -r requirements.txt
RUN apk del gcc musl-dev libffi-dev

COPY satisfactory satisfactory
RUN pip3 --no-cache-dir --disable-pip-version-check install .

USER guest
ENTRYPOINT [ "satisfactory-bot" ]

