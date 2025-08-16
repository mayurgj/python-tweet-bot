
import csv
import os
import datetime
import tweepy

# Twitter/X API authentication (replace with your tokens or set as repo secrets)
API_KEY = os.environ.get('X_API_KEY')
API_SECRET = os.environ.get('X_API_SECRET')
ACCESS_TOKEN = os.environ.get('X_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('X_ACCESS_TOKEN_SECRET')

auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

# Read tweets from CSV
with open('tweets.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    post_made = False
    for row in reader:
        if row['date_to_post'] == today:
            try:
                api.update_status(row['text'])
                print(f"Tweet posted: {row['text']}")
                post_made = True
                break
            except tweepy.TweepError as e:
                print(f"Failed to post tweet: {e}")
    if not post_made:
        print("No tweet scheduled for today or already posted.")
