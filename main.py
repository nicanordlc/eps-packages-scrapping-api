from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from datetime import datetime
from configparser import ConfigParser, NoOptionError
from functools import lru_cache

import requests

#{{{ init fast api
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#}}}

#{{{ configparser
@lru_cache
def get_config():
    """
    Retrieves configuration and parse it
    """
    config = ConfigParser()

    config.read('config.ini')

    def config_get(section_option, default=''):
        section, option = section_option.split('.')
        try:
            return config.get(section, option)
        except NoOptionError:
            return default

    config['user']['name'] = config_get('user.name')
    config['user']['password'] = config_get('user.password')

    return config

#}}}

#{{{ init session
config_ini = get_config()
username = config_ini.get('user', 'name')
password = config_ini.get('user', 'password')

URLS = {
        'login': 'https://app.eps-int.com/login',
        'home': 'https://app.eps-int.com/TrackingPaquetes#filter=*',
        }

# start the session
session = requests.Session()

# create the payload
payload = {
        'username': username,
        'password': password,
        }

# login into the session
session.post(URLS['login'], data=payload)
#}}}

#{{{ constants
INITIAL_STATE = {
        'items': [],
        'logged_in': False,
        }

CACHE = {
        'home': '',
        'last_update': 0,
        }
#}}}

#{{{ routes
@app.get('/')
def packages():
    """
    Returns a list of packages from EPS.com

    This endpoint updates every hour
    """
    return get_packages()

@app.get('/now')
def now():
    """
    Returns a list of packages from EPS.com

    This will update every time you request this endpoint
    """
    return get_packages(use_cache=False)
#}}}

#{{{ utils
def get_packages(use_cache=True):
    """
    Fetch packages from EPS.com into a JSON format
    """
    clear = False
    minutes_threshold = 1
    epoch = datetime.now().timestamp()

    # elapsed minutes
    epoch_difference_minutes = abs((CACHE['last_update'] - epoch) / 60)

    # if more an hour has passed clean the counter
    if epoch_difference_minutes > minutes_threshold:
        CACHE['last_update'] = epoch
        clear = True

    # empty the cache every hour
    if clear and use_cache:
        CACHE['home'] = ''

    # fetch home
    if CACHE['home'] and use_cache:
        eps_home = CACHE['home']
    else:
        eps_home = session.get(URLS['home'])
        CACHE['home'] = eps_home
        CACHE['last_update'] = epoch

    # if you're not logged it is a redirect, just return default state
    is_logged_out = bool(eps_home.history)
    if is_logged_out:
        return INITIAL_STATE

    # parse html
    soup = BeautifulSoup(eps_home.text, 'html.parser')

    soup_packages = soup.select('#fTrackingPaquetes [data-groups]')

    package_list = list(map(transform_package, soup_packages))

    return {
            'items': package_list,
            'logged_in': True,
            }

def transform_package(soup):
    """
    Parse eps html item into a structure
    """
    status_mapper = {
            'status1': 'origin',
            'status2': 'air line / ship',
            'status3': 'customs',
            'status4': 'distribution center',
            'status6': 'transit',
            'status5': 'available',
            }

    try:
        # attributes
        groups = soup['data-groups']
        _, status, status_label = groups.split()
        condition = soup.find(class_='packagecondition').contents[0]
        tracking_number = soup.find(class_='trackingnumber').contents[0]
        content = soup.find(class_='packagecontent').contents[0]
        sender = soup.find(class_='packagesender').contents[0]
        weight = soup.find(class_='packageweight').contents[0]
    except:
        # return empty item
        return {}

    # return item
    return {
            'condition': condition,
            'trackingNumber': tracking_number,
            'content': content,
            'sender': sender,
            'weight': weight,
            'status': status,
            'statusLabel': status_label,
            'statusFormatted': status_mapper[status],
            }
#}}}
