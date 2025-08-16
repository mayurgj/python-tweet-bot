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
    current_time = datetime.datetime.now()
    current_date = current_time.strftime('%Y-%m-%d')
    current_timestamp = current_time.strftime('%Y-%m-%d %H:%M')
    
    post_made = False
    
    for row in reader:
        # Check if the tweet is scheduled for today and the exact time has passed
        tweet_timestamp = row.get('timestamp', '')
        tweet_date = row.get('date_to_post', '')
        
        # If no timestamp, fall back to date-only matching (legacy support)
        if not tweet_timestamp and tweet_date == current_date:
            try:
                api.update_status(row['text'])
                print(f"Tweet posted (date-based): {row['text']}")
                post_made = True
                break
            except tweepy.TweepError as e:
                print(f"Failed to post tweet: {e}")
        
        # If timestamp is available, use precise timestamp matching
        elif tweet_timestamp and tweet_timestamp <= current_timestamp and tweet_date == current_date:
            try:
                api.update_status(row['text'])
                print(f"Tweet posted (timestamp-based): {row['text']} at {tweet_timestamp}")
                post_made = True
                break
            except tweepy.TweepError as e:
                print(f"Failed to post tweet: {e}")
    
    if not post_made:
        print(f"No tweet scheduled for {current_timestamp} or already posted.")
