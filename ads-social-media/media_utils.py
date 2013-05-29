import os
import sys
import re
import traceback
import site
site.addsitedir('/proj/ads/soft/python/lib/site-packages')
import datetime
import urllib
import urllib2
from config import config
# module to post to Delicious
from pydelicious import DeliciousAPI
# module to post to Twitter
import tweepy

today = datetime.datetime.now().strftime("%A")
this_year = datetime.datetime.now().strftime("%Y")

def get_title_string(bibcode):
    try:
        data = get_article_data(bibcode)
        return "%s: %s" % (data['first_author'], data['title'])
    except:
        return ''

def post_to_Facebook(bibcode, title):
    request_path = str(config.FACEBOOK_ID)+'/feed'
    post_data = {}
    post_data['access_token'] = config.FACEBOOK_ACCESS_TOKEN
    post_data['picture'] = ''
    post_data['caption'] = 'labs.adsabs.harvard.edu'
    post_data['link'] = config.BASE_URL % bibcode.strip()
    post_data['message'] = 'Article of the Day: %s' % title
    post_data = urllib.urlencode(post_data)
    host = 'https://graph.facebook.com/%s' % request_path
    req = urllib2.Request(host,post_data)
    response = urllib2.urlopen(req)
    result = response.read()

def post_to_Twitter(bibcode, header):
    try:
        short_bibcode = get_short_bibcode(bibcode)
    except:
        short_bibcode = bibcode
    url  = SHORT_URL % short_bibcode.strip()
    trailer = " %s %s" % (url,config.TWITTER_TAG)
    trailer_length = len(trailer)
    header_length = 140 - trailer_length - 5
    post = "%s[...]%s" % (header[:header_length],trailer)
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)
    api.update_status(post)

def post_to_Delicious(bibcode,title):
    a = DeliciousAPI(config.DELICIOUS_USER,config.DELICIOUS_PWD)
    arturl = config.BASE_URL % bibcode.strip()
    keywords = get_keywords(bibcode)
    keywords = uniq(keywords)
    entry_tags = ",".join(keywords)
    a.posts_add(arturl, title, extended=config.EXTENDED_DESCRIPTION, tags=entry_tags)

def post_to_private_library(bibcode):
    data = config.ADS_DATA % (bibcode.replace('&','%26'),this_year)
    headers = {'Cookie': config.ADS_COOKIE}
    req = urllib2.Request(config.ADS_URL,data,headers)
    f = urllib2.urlopen(req)

def save_article_of_the_day(bibcode):
    
def post_article(bibcode,**args):
    try:
        targets = args['targets'].split(',')
    except:
        targets = ['Facebook','Twitter','Delicious','private_library']