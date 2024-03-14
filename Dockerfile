FROM  python:3.10 as Builder

WORKDIR /app

COPY . .

RUN set -xe \
    && apt-get update\
    && apt-get install -y --no-install-recommends ffmpeg\
    && pip3 install --upgrade pip \
    && pip3 install pipenv==2023.6.26 \
    && pipenv install --system --deploy

CMD python main.py

