FROM python:3.8-alpine

RUN apk add build-base libffi-dev libressl-dev

COPY compose/requirements.txt /var/lib/network-api/compose/requirements.txt
RUN pip install -r /var/lib/network-api/compose/requirements.txt

COPY src /var/lib/network-api/src
WORKDIR /var/lib/network-api/src

CMD uvicorn network_api.asgi:app --host 0.0.0.0 --port ${SERVICE_PORT:-8080} --reload
