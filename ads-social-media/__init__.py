# function to generate a new batch of Articles of the Day
from media_utils import get_articles_of_the_day
# functions to post the Article of the Day
from media_utils import post_article

_basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IDENTIFIER_FILE = _basedir + '/data/ASTkeywords.set'
try:
    IDENTIFIERS = open(IDENTIFIER_FILE).read().strip().split('\n')
except:
    IDENTIFIERS = []