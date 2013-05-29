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

def uniq(items):
    """
    Returns a uniqued list.
    """
    unique = []
    unique_dict = {}
    for item in items:
        if item not in unique_dict:
            unique_dict[item] = None
            unique.append(item)
    return unique

def flatten(items):
    result = []
    for item in items:
        if hasattr(item, '__iter__'):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

def req(url, **kwargs):
    """
    Function to query Solr
    """
    kwargs['wt'] = 'json'
    query_params = urllib.urlencode(kwargs)
    r = requests.get(url, params=query_params)
    return r.json()

def get_publication_data(bibcode):
#    get the article of the day for today from MongoDB


def post_to_Facebook(art_data):
    request_path = str(config.FACEBOOK_ID)+'/feed'
    post_data = {}
    post_data['access_token'] = config.FACEBOOK_ACCESS_TOKEN
    post_data['picture'] = ''
    post_data['caption'] = 'labs.adsabs.harvard.edu'
    post_data['link'] = config.BASE_URL % art_data['bibcode'].strip()
    post_data['message'] = 'Article of the Day: %s' % art_data['title']
    post_data = urllib.urlencode(post_data)
    host = 'https://graph.facebook.com/%s' % request_path
    req = urllib2.Request(host,post_data)
    response = urllib2.urlopen(req)
    result = response.read()

def post_to_Twitter(art_data):
    try:
        short_bibcode = art_data['short_bibcode']
    except:
        short_bibcode = bibcode
    url  = SHORT_URL % short_bibcode.strip()
    trailer = " %s %s" % (url,config.TWITTER_TAG)
    trailer_length = len(trailer)
    header_length = 140 - trailer_length - 5
    post = "%s[...]%s" % (art_data['twitter_header'][:header_length],trailer)
    auth = tweepy.OAuthHandler(config.TWITTER_CONSUMER_KEY, config.TWITTER_CONSUMER_SECRET)
    auth.set_access_token(config.TWITTER_ACCESS_KEY, config.TWITTER_ACCESS_SECRET)
    api = tweepy.API(auth)
    api.update_status(post)

def post_to_Delicious(art_data):
    a = DeliciousAPI(config.DELICIOUS_USER,config.DELICIOUS_PWD)
    arturl = config.BASE_URL % art_data['bibcode'].strip()
    entry_tags = ",".join(art_data['keywords'])
    a.posts_add(arturl, art_data['title'], extended=config.EXTENDED_DESCRIPTION, tags=entry_tags)

def post_to_private_library(art_data):
    data = config.ADS_DATA % (art_data['bibcode'].replace('&','%26'),this_year)
    headers = {'Cookie': config.ADS_COOKIE}
    req = urllib2.Request(config.ADS_URL,data,headers)
    f = urllib2.urlopen(req)

def save_article_of_the_day(bibcode):
    
def post_article(bibcode,**args):
    try:
        targets = args['targets'].split(',')
    except:
        targets = ['Facebook','Twitter','Delicious','private_library']
    data = get_publication_data(bibcode)
    for target in targets:
        func = globals()["post_to_%s"%target]
        res = func(data)
#    res = save_article_of_the_day(bibcode)