#!/usr/bin/env python3
"""
Twitter Bot Script - posts scheduled tweets from CSV file
Requires Twitter API v2 free tier access
"""

import csv
import os
import logging
import tweepy
from datetime import datetime, timezone
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tweet_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TwitterBot:
    def __init__(self):
        """Initialize Twitter Bot with API credentials"""
        self.api = None
        self.csv_file = 'tweets.csv'
        
        # Get Twitter API credentials from environment variables
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.consumer_key = os.getenv('TWITTER_API_KEY')
        self.consumer_secret = os.getenv('TWITTER_API_SECRET')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not all([self.bearer_token, self.consumer_key, self.consumer_secret, 
                   self.access_token, self.access_token_secret]):
            logger.error("Missing required Twitter API credentials in environment variables")
            raise ValueError("Missing Twitter API credentials")
    
    def authenticate(self):
        """Authenticate with Twitter API"""
        try:
            # Create client for Twitter API v2
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.consumer_key,
                consumer_secret=self.consumer_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Test authentication
            me = self.client.get_me()
            if me.data:
                logger.info(f"Successfully authenticated as @{me.data.username}")
                return True
            else:
                logger.error("Authentication failed - unable to get user info")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def read_tweets_from_csv(self):
        """Read tweets from CSV file"""
        tweets = []
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    tweets.append({
                        'id': int(row['id']),
                        'text': row['text'],
                        'date_to_post': row['date_to_post'],
                        'posted': row.get('posted', 'False').lower() == 'true'
                    })
            logger.info(f"Loaded {len(tweets)} tweets from {self.csv_file}")
        except FileNotFoundError:
            logger.error(f"CSV file {self.csv_file} not found")
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}")
        
        return tweets
    
    def update_csv_posted_status(self, tweet_id):
        """Update CSV to mark tweet as posted"""
        try:
            tweets = []
            # Read all tweets
            with open(self.csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if int(row['id']) == tweet_id:
                        row['posted'] = 'True'
                    tweets.append(row)
            
            # Write back to CSV
            with open(self.csv_file, 'w', encoding='utf-8', newline='') as file:
                fieldnames = ['id', 'text', 'date_to_post', 'posted']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(tweets)
            
            logger.info(f"Updated tweet {tweet_id} status to posted")
            
        except Exception as e:
            logger.error(f"Error updating CSV file: {str(e)}")
    
    def get_next_scheduled_tweet(self):
        """Get the next tweet that should be posted"""
        tweets = self.read_tweets_from_csv()
        current_time = datetime.now(timezone.utc)
        
        for tweet in tweets:
            if tweet['posted']:
                continue
                
            try:
                # Parse the scheduled date
                tweet_date = datetime.fromisoformat(tweet['date_to_post'].replace('Z', '+00:00'))
                
                # Check if it's time to post this tweet
                if tweet_date <= current_time:
                    return tweet
                    
            except ValueError as e:
                logger.error(f"Error parsing date for tweet {tweet['id']}: {str(e)}")
                continue
        
        return None
    
    def post_tweet(self, tweet_text):
        """Post a tweet with error handling"""
        try:
            # Check tweet length (280 character limit)
            if len(tweet_text) > 280:
                logger.warning(f"Tweet too long ({len(tweet_text)} chars), truncating...")
                tweet_text = tweet_text[:277] + "..."
            
            # Post the tweet
            response = self.client.create_tweet(text=tweet_text)
            
            if response.data:
                logger.info(f"Successfully posted tweet: {response.data['id']}")
                return True, response.data['id']
            else:
                logger.error("Failed to post tweet - no response data")
                return False, None
                
        except tweepy.TooManyRequests:
            logger.error("Rate limit exceeded - too many requests")
            return False, None
        except tweepy.Forbidden as e:
            logger.error(f"Tweet posting forbidden: {str(e)}")
            return False, None
        except tweepy.BadRequest as e:
            logger.error(f"Bad request when posting tweet: {str(e)}")
            return False, None
        except Exception as e:
            logger.error(f"Unexpected error posting tweet: {str(e)}")
            return False, None
    
    def run(self):
        """Main execution function"""
        logger.info("Starting Twitter Bot...")
        
        # Authenticate
        if not self.authenticate():
            logger.error("Authentication failed, exiting")
            return False
        
        # Get next scheduled tweet
        next_tweet = self.get_next_scheduled_tweet()
        
        if not next_tweet:
            logger.info("No tweets scheduled for posting at this time")
            return True
        
        logger.info(f"Found tweet to post: ID {next_tweet['id']}")
        logger.info(f"Tweet text: {next_tweet['text'][:50]}...")
        
        # Post the tweet
        success, tweet_id = self.post_tweet(next_tweet['text'])
        
        if success:
            # Update CSV to mark as posted
            self.update_csv_posted_status(next_tweet['id'])
            logger.info(f"Tweet posted successfully with ID: {tweet_id}")
            return True
        else:
            logger.error("Failed to post tweet")
            return False

def main():
    """Main function"""
    try:
        bot = TwitterBot()
        success = bot.run()
        
        if success:
            logger.info("Bot execution completed successfully")
            sys.exit(0)
        else:
            logger.error("Bot execution failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
