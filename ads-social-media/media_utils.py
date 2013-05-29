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
from multiprocessing import Pool, current_process
from multiprocessing import Manager
# memory mapped data
manager = Manager()
ads_data = manager.dict()
# module to post to Delicious
from pydelicious import DeliciousAPI
# module to post to Twitter
import tweepy
# module for retrieving data from MongoDB
site.addsitedir('/proj/adsx/adsdata')
import adsdata
# initiate MongoDB session
session = adsdata.get_session()

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
    fl = 'first_author_norm,title,pubdate'
    q = 'bibcode:%s' % bibcode
    rsp = req(config.SOLR_URL, q=q, fl=fl, rows=config.MAX_HITS)
    publication_data.append(rsp['response']['docs'])

def get_mongo_data(bbc):
    doc = session.get_doc(bbc)
    try:
        doc.pop("full", None)
    except:
        pass
    try:
        ads_data[bbc] = doc
    except:
        pass

def get_batch_data(**args):
    # first establish the date of the current index
    dirs = os.listdir(config.ASTdir)
    for entry in dirs:
        subdir = "%s/%s" % (ASTdir,entry)
        if os.path.islink(subdir):
            if entry == "current":
                cur_dir = os.path.realpath(subdir)
                batch_data['cur_date'] = os.path.basename(cur_dir).replace('-','')
    # record the previous Articles of the Day
    batch_data['previous'] = get_previous_articles_of_the_day()
    return batch_data

def get_recent_astronomy_publications(batch_data):
    bib2accno = "%s/current/bib2accno.list" % config.ASTdir
    fh = open(bib2accno)
    batch_data['candidates'] = []
    for line in fh:
        entries = line.strip().split('\t')
        if len(entries) != 4:
            continue
        if entries[3] == batch_data['cur_date']:
            bibc = entries[0]
            # ignore all papers older than CUTOFF_YEAR, that were an Article of the Day previously,
            # or whose bibstem is in the list of publications to ignore
            if int(bibc[:4]) > config.CUTOFF_YEAR and bibc not in batch_data['previous'] and bibc[4:9] not in config.IGNORE_PUBS and bib[10:13] != 'tmp':
                batch_data['candidates'].append(bibc)
    return batch_data

def rank_candidates(batch_data, ads_data):
    candidates = []
    for bibcode in batch_data['candidates']:
        candidates.append((bibcode,float(ads_data[bibcode]['citations']*ads_data[bibcode]['reads'])*invAuth))
    candidates = sorted(candidates, key=operator.itemgetter(1),reverse=True)
    return candidates

def select_finalists(candidates):
    clusters = []
    bibstems = []
    finalists= []
    for candidate in candidates:
        bibstem = candidate[0][4:9]
        if config.USE_CLUSTERS:
            paper_cluster = get_paper_cluster(candidate[0])
        if bibstem not in bibstems:
            if not config.USE_CLUSTERS:
                finalists.append("%s:%s"%(candidate[0],"NA"))
                bibstems.append(bibstem)
            else:
                if paper_cluster not in clusters:
                    finalists.append("%s:%s"%(candidate[0],paper_cluster))
                    bibstems.append(bibstem)
                    clusters.append(paper_cluster)
    return finalists

def get_keywords(bibcode):
    """"
    Get all citations (bibcodes) for given set of papers
    """
    keywords = []
    fl = 'keyword'
    q = 'bibcode:%s OR references(bibcode:%s)' % (bibcode,bibcode)
    rsp = req(SOLR_URL, q=q, fl=fl, rows=MAX_HITS)
    keywords = flatten(map(lambda b: b['keyword'],
           filter(lambda a: 'keyword' in a ,rsp['response']['docs'])))
    return uniq(filter(lambda a: a in config.IDENTIFIERS, keywords))

def save_articles_of_the_day(finalists):
    for pub in finalists[:config.AOD_LIMIT]:
        pub_data = get_publication_data(pub[0])
        doc = {}
        doc['publication'] = pub[0]
        doc['cluster'] = pub[1]
        doc['publication_date'] = 
        doc['keywords'] = get_keywords(pub[0])
        doc['first_author'] = pub_data['first_author_norm']
        doc['title'] = pub_data['title']
        doc['short_bibcode'] =
        doc['post_date'] =
        aod_collection.insert(doc)

def get_article_of_the_day_data(bibcode):
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