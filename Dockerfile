FROM python:3.14-alpine

RUN apk add --no-cache gcc g++ musl-dev libffi-dev

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 --no-cache-dir --disable-pip-version-check install -r requirements.txt
RUN apk del gcc musl-dev libffi-dev

COPY main.py ./

USER guest
ENTRYPOINT [ "python3", "main.py" ]
