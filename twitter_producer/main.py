import json

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from google.cloud import pubsub_v1
import os
from dotenv import load_dotenv
import sys

load_dotenv()
# coding: utf-8
import datetime
import json
import time

import tweepy
from google.cloud import pubsub_v1
from tweepy.streaming import StreamListener

# Config
publisher = pubsub_v1.PublisherClient()
topic_path = 'projects/sonorous-guide-343021/topics/bitcoin-sentiment'


# Load in a json file with your Tweepy API credentials
with open("./basic.json") as json_data:
    account_data = json.load(json_data)

# Select the account you want to listen with
auth = tweepy.OAuthHandler(os.getenv('CONSUMER_KEY'), os.getenv('CONSUMER_SECRET'))
auth.set_access_token(os.getenv('ACCESS_TOKEN'), os.getenv('TOKEN_SECRET'))

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
