import json

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from google.cloud import pubsub_v1
import os
from dotenv import load_dotenv
import sys

# coding: utf-8
import datetime
import json
import time

import tweepy
from google.cloud import pubsub_v1
from tweepy.streaming import StreamListener

# Config
publisher = pubsub_v1.PublisherClient()



# Load in a json file with your Tweepy API credentials

try:
    # local
    load_dotenv(".env")
    with open("./basic.json") as json_data:
        account_data = json.load(json_data)
    topic_path = os.getenv('TOPIC_PATH')
    consumer_key = os.getenv('CONSUMER_KEY')
    consumer_secret = os.getenv('CONSUMER_SECRET')
    access_token = os.getenv('ACCESS_TOKEN')
    token_secret = os.getenv('TOKEN_SECRET')
except:
    print("fallo local")

try:
    # github
    account_data = json.loads(os.environ('BASICJSON'))
    topic_path = os.environ("TOPIC_PATH")
    consumer_key = os.environ('CONSUMER_KEY')
    consumer_secret = os.environ('CONSUMER_SECRET')
    access_token = os.environ('ACCESS_TOKEN')
    token_secret = os.environ('TOKEN_SECRET')
except:
    print("fallo github")

try:
    # azure
    account_data = json.loads(os.environ.get('BASICJSON'))
except:
    print("fallo azure")

# Select the account you want to listen with
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, token_secret)

api = tweepy.API(auth, wait_on_rate_limit=True)

# Define the list of terms to listen to
lst_hashtags = ["#bitcoin"]

# Method to push messages to pubsub
def write_to_pubsub(data):
    try:
        if data["lang"] == "en": 
            test = json.dumps({
                "id": data["id"],
                "lang": data["lang"],
                "created_at": data["created_at"],
                "text": data["text"],
                "retweet_count": data["retweet_count"]
            }).encode("utf-8")
            print(test)
            publisher.publish(topic_path, data=test)
        
    except Exception as e:
        raise

# Method to format a tweet from tweepy
def reformat_tweet(tweet):
    x = tweet
    processed_doc = {
        "id": x["id"],
        "lang": x["lang"],
        "created_at": time.mktime(time.strptime(x["created_at"], "%a %b %d %H:%M:%S +0000 %Y")),
        "text": x["text"] if "favorite_count" in x else 0,
        "retweet_count": x["retweet_count"] if "retweet_count" in x else 0
    }
    return processed_doc

# Custom listener class
class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just pushes tweets to pubsub
    """

    def __init__(self):
        super(StdOutListener, self).__init__()
        self._counter = 0

    def on_status(self, data):
        write_to_pubsub(reformat_tweet(data._json))
        self._counter += 1
        return True

    def on_error(self, status):
        if status == 420:
            print("rate limit active")
            return False


# Start listening
l = StdOutListener()
stream = tweepy.Stream(auth, l, tweet_mode='extended')
stream.filter(track=lst_hashtags)
