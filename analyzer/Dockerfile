FROM python:3.7

LABEL maintainer="s.lee@uu.nl"

WORKDIR /app

#Install dependencies
COPY . /app

RUN cd /app && pip3 install -r requirements.txt

EXPOSE 5000

