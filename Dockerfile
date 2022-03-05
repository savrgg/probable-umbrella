FROM python:3.7-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . . 

CMD [ "python3", "twitter_producer/main.py"]

