FROM python:latest

LABEL Maintainer="miguel1993"

RUN pip install requests websocket-client plexapi

WORKDIR /app

COPY stream_upgrader.py ./

CMD [ "python", "./stream_upgrader.py"]