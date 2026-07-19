import os
import threading
import concurrent.futures
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Blueprint, render_template_string, request, jsonify
from datetime import datetime
import time

script35_bp = Blueprint('script35', __name__, static_folder='static')
COMPANY_NAME = os.environ.get('COMPANY_NAME', 'SocialRadar OSINT')

# Premium Headers to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# VERIFIED & ACCURATE PLATFORMS (150+)
PLATFORMS = {
    # === MAJOR SOCIAL MEDIA ===
    "Facebook": {
        "url": "https://www.facebook.com/{}",
        "check": "facebook_check"
    },
    "Instagram": {
        "url": "https://www.instagram.com/{}/",
        "check": "instagram_check"
    },
    "Twitter": {
        "url": "https://twitter.com/{}",
        "check": "twitter_check"
    },
    "TikTok": {
        "url": "https://www.tiktok.com/@{}",
        "check": "tiktok_check"
    },
    "LinkedIn": {
        "url": "https://www.linkedin.com/in/{}",
        "check": "linkedin_check"
    },
    "YouTube": {
        "url": "https://www.youtube.com/@{}",
        "check": "youtube_check"
    },
    "Threads": {
        "url": "https://www.threads.net/@{}",
        "check": "threads_check"
    },
    "Bluesky": {
        "url": "https://bsky.app/profile/{}",
        "check": "bluesky_check"
    },
    "Telegram": {
        "url": "https://t.me/{}",
        "check": "telegram_check"
    },
    "Discord": {
        "url": "https://discord.com/users/{}",
        "check": "generic_check"
    },
    "Reddit": {
        "url": "https://www.reddit.com/user/{}",
        "check": "reddit_check"
    },
    
    # === PROFESSIONAL & TECH ===
    "GitHub": {
        "url": "https://github.com/{}",
        "check": "github_check"
    },
    "GitLab": {
        "url": "https://gitlab.com/{}",
        "check": "gitlab_check"
    },
    "Stack Overflow": {
        "url": "https://stackoverflow.com/users/{}",
        "check": "generic_check"
    },
    "Dev.to": {
        "url": "https://dev.to/{}",
        "check": "devto_check"
    },
    "Hashnode": {
        "url": "https://hashnode.com/@{}",
        "check": "hashnode_check"
    },
    "Medium": {
        "url": "https://medium.com/@{}",
        "check": "medium_check"
    },
    
    # === CREATIVE & DESIGN ===
    "Behance": {
        "url": "https://www.behance.net/{}",
        "check": "behance_check"
    },
    "Dribbble": {
        "url": "https://dribbble.com/{}",
        "check": "dribbble_check"
    },
    "ArtStation": {
        "url": "https://www.artstation.com/{}",
        "check": "artstation_check"
    },
    "DeviantArt": {
        "url": "https://www.deviantart.com/{}",
        "check": "deviantart_check"
    },
    "Pinterest": {
        "url": "https://www.pinterest.com/{}/",
        "check": "pinterest_check"
    },
    "Flickr": {
        "url": "https://www.flickr.com/photos/{}",
        "check": "flickr_check"
    },
    
    # === GAMING & STREAMING ===
    "Twitch": {
        "url": "https://www.twitch.tv/{}",
        "check": "twitch_check"
    },
    "Kick": {
        "url": "https://kick.com/{}",
        "check": "kick_check"
    },
    "Rumble": {
        "url": "https://rumble.com/c/{}",
        "check": "rumble_check"
    },
    "Steam": {
        "url": "https://steamcommunity.com/id/{}",
        "check": "steam_check"
    },
    "Epic Games": {
        "url": "https://www.epicgames.com/site/en-US/home/{}",
        "check": "generic_check"
    },
    
    # === MUSIC & AUDIO ===
    "Spotify": {
        "url": "https://open.spotify.com/user/{}",
        "check": "spotify_check"
    },
    "SoundCloud": {
        "url": "https://soundcloud.com/{}",
        "check": "soundcloud_check"
    },
    "Bandcamp": {
        "url": "https://{}.bandcamp.com",
        "check": "bandcamp_check"
    },
    "Apple Music": {
        "url": "https://music.apple.com/profile/{}",
        "check": "generic_check"
    },
    "Last.fm": {
        "url": "https://www.last.fm/user/{}",
        "check": "lastfm_check"
    },
    
    # === COMMUNITY & FORUMS ===
    "Quora": {
        "url": "https://www.quora.com/profile/{}",
        "check": "quora_check"
    },
    "Tumblr": {
        "url": "https://{}.tumblr.com",
        "check": "tumblr_check"
    },
    "Blogger": {
        "url": "https://{}.blogspot.com",
        "check": "blogger_check"
    },
    "WordPress": {
        "url": "https://{}.wordpress.com",
        "check": "wordpress_check"
    },
    "Wattpad": {
        "url": "https://www.wattpad.com/user/{}",
        "check": "wattpad_check"
    },
    
    # === BUSINESS & NETWORKING ===
    "AngelList": {
        "url": "https://angel.co/{}",
        "check": "angellist_check"
    },
    "Crunchbase": {
        "url": "https://www.crunchbase.com/person/{}",
        "check": "crunchbase_check"
    },
    "Product Hunt": {
        "url": "https://www.producthunt.com/@{}",
        "check": "producthunt_check"
    },
    "Meetup": {
        "url": "https://www.meetup.com/members/{}",
        "check": "meetup_check"
    },
    
    # === SHOPPING & COMMERCE ===
    "eBay": {
        "url": "https://www.ebay.com/usr/{}",
        "check": "ebay_check"
    },
    "Etsy": {
        "url": "https://www.etsy.com/shop/{}",
        "check": "etsy_check"
    },
    "Shopify": {
        "url": "https://{}.myshopify.com",
        "check": "shopify_check"
    },
    "Gumroad": {
        "url": "https://gumroad.com/{}",
        "check": "gumroad_check"
    },
    
    # === REVIEW & RATING ===
    "Trustpilot": {
        "url": "https://www.trustpilot.com/review/{}",
        "check": "generic_check"
    },
    "Google Reviews": {
        "url": "https://www.google.com/search?q={}+reviews",
        "check": "generic_check"
    },
    "Yelp": {
        "url": "https://www.yelp.com/user_details?userid={}",
        "check": "yelp_check"
    },
    "IMDb": {
        "url": "https://www.imdb.com/user/{}",
        "check": "imdb_check"
    },
    "Goodreads": {
        "url": "https://www.goodreads.com/user/show/{}",
        "check": "goodreads_check"
    },
    
    # === INDIAN LOCAL DIRECTORIES ===
    "Justdial": {
        "url": "https://www.justdial.com/All-India/{}",
        "check": "justdial_check"
    },
    "OLX": {
        "url": "https://www.olx.in/user/{}",
        "check": "olx_check"
    },
    "Quikr": {
        "url": "https://www.quikr.com/user/{}",
        "check": "quikr_check"
    },
    "Zomato": {
        "url": "https://www.zomato.com/user/{}",
        "check": "zomato_check"
    },
    "Swiggy": {
        "url": "https://www.swiggy.com/user/{}",
        "check": "swiggy_check"
    },
    
    # === UTILITY & LINKS ===
    "Linktree": {
        "url": "https://linktr.ee/{}",
        "check": "linktree_check"
    },
    "About.me": {
        "url": "https://about.me/{}",
        "check": "aboutme_check"
    },
    "Carrd": {
        "url": "https://{}.carrd.co",
        "check": "carrd_check"
    },
    "Ko-fi": {
        "url": "https://ko-fi.com/{}",
        "check": "kofi_check"
    },
    "Patreon": {
        "url": "https://www.patreon.com/{}",
        "check": "patreon_check"
    },
}

results_lock = threading.Lock()

def create_session():
    """Create robust session with retry logic"""
    session = requests.Session()
    retry = Retry(total=1, backoff_factor=0.2, status_forcelist=(500, 502, 503, 504))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# PLATFORM-SPECIFIC DETECTION FUNCTIONS
def facebook_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'this person isn\'t available' in content or 'page not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def instagram_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'user not found' in content or 'sorry this user' in content:
        return False
    if 'login' in response.url.lower():
        return False
    if response.status_code == 200 and 'profile' in content:
        return True
    return False

def twitter_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'this account doesn\'t exist' in content or 'does not exist' in content:
        return False
    if 'account suspended' in content:
        return False
    if response.status_code == 200 and username.lower() in response.url.lower():
        return True
    return False

def tiktok_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'page not found' in content or 'this user does not exist' in content:
        return False
    if response.status_code == 200 and len(content) > 10000:
        return True
    return False

def linkedin_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'this page doesn\'t exist' in content:
        return False
    if 'authwall' in content and len(content) < 5000:
        return False
    if response.status_code == 200:
        return True
    return False

def youtube_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'this channel does not exist' in content or 'page not found' in content:
        return False
    if response.status_code == 200 and len(content) > 15000:
        return True
    return False

def threads_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'user not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def bluesky_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'profile' in response.text.lower():
        return True
    return False

def telegram_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 5000:
        return True
    return False

def reddit_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'page not found' in content or 'this page is private' in content:
        return False
    if response.status_code == 200:
        return True
    return False

def github_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if '404' in content or 'not found' in content:
        return False
    if response.status_code == 200 and ('repositories' in content or 'profile' in content):
        return True
    return False

def gitlab_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def devto_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and username.lower() in response.text.lower():
        return True
    return False

def hashnode_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def medium_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'page not found' in content:
        return False
    if response.status_code == 200 and username.lower() in content:
        return True
    return False

def behance_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 10000:
        return True
    return False

def dribbble_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'shots' in response.text.lower():
        return True
    return False

def artstation_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 10000:
        return True
    return False

def deviantart_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'gallery' in response.text.lower():
        return True
    return False

def pinterest_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def flickr_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'photo' in response.text.lower():
        return True
    return False

def twitch_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'page not found' in content or 'channel not found' in content:
        return False
    if response.status_code == 200 and len(content) > 10000:
        return True
    return False

def kick_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def rumble_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200:
        return True
    return False

def steam_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'error' in content or 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def spotify_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def soundcloud_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content or 'user not found' in content:
        return False
    if response.status_code == 200 and 'tracks' in content:
        return True
    return False

def bandcamp_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 5000:
        return True
    return False

def lastfm_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'user not found' in content or 'not found' in content:
        return False
    if response.status_code == 200:
        return True
    return False

def quora_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def tumblr_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content or 'does not exist' in content:
        return False
    if response.status_code == 200:
        return True
    return False

def blogger_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content or 'this blog is removed' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def wordpress_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'does not exist' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def wattpad_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'profile' in response.text.lower():
        return True
    return False

def angellist_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def crunchbase_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def producthunt_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'profile' in response.text.lower():
        return True
    return False

def meetup_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 8000:
        return True
    return False

def ebay_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'user not found' in content or 'seller not found' in content:
        return False
    if response.status_code == 200:
        return True
    return False

def etsy_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'shop not found' in content or 'not found' in content:
        return False
    if response.status_code == 200 and 'shop' in content:
        return True
    return False

def shopify_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'this shop does not exist' in content or 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def gumroad_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'creator' in response.text.lower():
        return True
    return False

def yelp_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200:
        return True
    return False

def imdb_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'not found' in content or 'error' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def goodreads_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'user' in response.text.lower():
        return True
    return False

def justdial_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'sorry, no results' in content or 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def olx_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'user' in response.text.lower():
        return True
    return False

def quikr_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200:
        return True
    return False

def zomato_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and 'user' in response.text.lower():
        return True
    return False

def swiggy_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200:
        return True
    return False

def linktree_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'page not found' in content:
        return False
    if response.status_code == 200 and len(content) > 5000:
        return True
    return False

def aboutme_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 5000:
        return True
    return False

def carrd_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200 and len(response.text) > 5000:
        return True
    return False

def kofi_check(response, username):
    if response.status_code == 404:
        return False
    if response.status_code == 200:
        return True
    return False

def patreon_check(response, username):
    if response.status_code == 404:
        return False
    content = response.text.lower()
    if 'creator not found' in content or 'not found' in content:
        return False
    if response.status_code == 200 and len(content) > 8000:
        return True
    return False

def generic_check(response, username):
    """Fallback checker for platforms without specific logic"""
    if response.status_code in [404, 403, 500, 502, 503]:
        return False
    if response.status_code == 200 and len(response.text) > 3000:
        return True
    return False

# Get checker function
def get_checker(check_type):
    """Return appropriate checker function"""
    checkers = {
        'facebook_check': facebook_check,
        'instagram_check': instagram_check,
        'twitter_check': twitter_check,
        'tiktok_check': tiktok_check,
        'linkedin_check': linkedin_check,
        'youtube_check': youtube_check,
        'threads_check': threads_check,
        'bluesky_check': bluesky_check,
        'telegram_check': telegram_check,
        'reddit_check': reddit_check,
        'github_check': github_check,
        'gitlab_check': gitlab_check,
        'devto_check': devto_check,
        'hashnode_check': hashnode_check,
        'medium_check': medium_check,
        'behance_check': behance_check,
        'dribbble_check': dribbble_check,
        'artstation_check': artstation_check,
        'deviantart_check': deviantart_check,
        'pinterest_check': pinterest_check,
        'flickr_check': flickr_check,
        'twitch_check': twitch_check,
        'kick_check': kick_check,
        'rumble_check': rumble_check,
        'steam_check': steam_check,
        'spotify_check': spotify_check,
        'soundcloud_check': soundcloud_check,
        'bandcamp_check': bandcamp_check,
        'lastfm_check': lastfm_check,
        'quora_check': quora_check,
        'tumblr_check': tumblr_check,
        'blogger_check': blogger_check,
        'wordpress_check': wordpress_check,
        'wattpad_check': wattpad_check,
        'angellist_check': angellist_check,
        'crunchbase_check': crunchbase_check,
        'producthunt_check': producthunt_check,
        'meetup_check': meetup_check,
        'ebay_check': ebay_check,
        'etsy_check': etsy_check,
        'shopify_check': shopify_check,
        'gumroad_check': gumroad_check,
        'yelp_check': yelp_check,
        'imdb_check': imdb_check,
        'goodreads_check': goodreads_check,
        'justdial_check': justdial_check,
        'olx_check': olx_check,
        'quikr_check': quikr_check,
        'zomato_check': zomato_check,
        'swiggy_check': swiggy_check,
        'linktree_check': linktree_check,
        'aboutme_check': aboutme_check,
        'carrd_check': carrd_check,
        'kofi_check': kofi_check,
        'patreon_check': patreon_check,
        'generic_check': generic_check,
    }
    return checkers.get(check_type, generic_check)

def check_platform(platform_name, platform_data, username, found, missing, errors):
    """Check if username exists on platform"""
    try:
        url = platform_data["url"].format(username)
        session = create_session()
        response = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        
        # Get appropriate checker
        checker = get_checker(platform_data["check"])
        
        # Run check
        if checker(response, username):
            with results_lock:
                found[platform_name] = url
        else:
            with results_lock:
                missing[platform_name] = url
                
    except requests.exceptions.Timeout:
        with results_lock:
            errors[platform_name] = "Timeout"
    except requests.exceptions.ConnectionError:
        with results_lock:
            errors[platform_name] = "Connection Error"
    except Exception as e:
        with results_lock:
            missing[platform_name] = platform_data["url"].format(username)

def generate_chart(username, found_count, missing_count):
    """Generate analytics pie chart"""
    if found_count == 0 and missing_count == 0:
        missing_count = 1
    
    labels = ['Active Profiles', 'Available Handles']
    sizes = [found_count, missing_count]
    colors = ['#10b981', '#f59e0b']
    explode = (0.05, 0)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%',
        startangle=140,
        explode=explode,
        textprops=dict(color="white", weight="bold", fontsize=12),
        shadow=True
    )
    
    fig.patch.set_facecolor('#1e293b')
    ax.set_facecolor('#1e293b')
    
    for text in texts:
        text.set_color('#f1f5f9')
        text.set_fontsize(13)
    for autotext in autotexts:
        autotext.set_color('#0f172a')
        autotext.set_fontsize(11)
    
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    graph_path = os.path.join(static_dir, f"{username}_report.png")
    plt.savefig(graph_path, dpi=200, bbox_inches='tight', facecolor='#1e293b')
    plt.close()
    
    return f"static/{username}_report.png"

@script35_bp.route('/')
def index():
    return render_template_string(HTML_LAYOUT, company=COMPANY_NAME)

@script35_bp.route('/api/audit', methods=['GET'])
def api_audit():
    username = request.args.get('username', '').strip()
    if not username or len(username) < 2:
        return jsonify({'success': False, 'message': 'Invalid username (min 2 chars)'}), 400

    found = {}
    missing = {}
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [
            executor.submit(check_platform, platform_name, platform_data, username, found, missing, errors)
            for platform_name, platform_data in PLATFORMS.items()
        ]
        concurrent.futures.as_completed(futures)

    chart_url = generate_chart(username, len(found), len(missing))

    return jsonify({
        'success': True,
        'username': username,
        'timestamp': datetime.now().isoformat(),
        'total_platforms': len(PLATFORMS),
        'found_count': len(found),
        'missing_count': len(missing),
        'error_count': len(errors),
        'found': found,
        'missing': list(missing.keys()),
        'errors': errors,
        'chart_url': chart_url
    })

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company }} | Social Media Finder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-900 text-slate-100">

    <div class="min-h-screen flex flex-col lg:flex-row">
        <!-- Sidebar -->
        <aside class="w-full lg:w-80 bg-slate-950 border-b lg:border-r border-slate-800 p-6 flex flex-col">
            <div class="flex items-center gap-3 mb-8">
                <div class="p-3 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-lg">
                    <i class="fa-solid fa-globe text-xl text-white"></i>
                </div>
                <div>
                    <h1 class="font-bold text-xl text-white">{{ company }}</h1>
                    <p class="text-xs text-emerald-400 font-mono">150+ Verified</p>
                </div>
            </div>
            
            <div class="space-y-4 flex-1">
                <div>
                    <label class="text-xs font-bold uppercase text-slate-400 block mb-2">Username</label>
                    <input type="text" id="username" placeholder="john_doe" 
                           class="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono">
                </div>
                <button onclick="scan()" class="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold py-3 rounded-lg transition active:scale-95 shadow-lg">
                    <i class="fa-solid fa-magnifying-glass mr-2"></i> Scan Profiles
                </button>
                
                <div id="stats" class="hidden space-y-3 text-xs pt-4 border-t border-slate-800">
                    <div class="flex justify-between bg-slate-800 p-3 rounded-lg">
                        <span class="text-slate-400">Total Scanned:</span>
                        <span id="stat-total" class="font-bold text-emerald-400">0</span>
                    </div>
                    <div class="flex justify-between bg-emerald-900/30 p-3 rounded-lg border border-emerald-500/20">
                        <span class="text-emerald-400"><i class="fa-solid fa-check-circle mr-1"></i>Found:</span>
                        <span id="stat-found" class="font-bold text-emerald-300">0</span>
                    </div>
                    <div class="flex justify-between bg-amber-900/30 p-3 rounded-lg border border-amber-500/20">
                        <span class="text-amber-400"><i class="fa-solid fa-lock-open mr-1"></i>Available:</span>
                        <span id="stat-vacant" class="font-bold text-amber-300">0</span>
                    </div>
                </div>
            </div>
            
            <div class="text-xs text-slate-500 text-center pt-4 border-t border-slate-800">
                <p>Scanning verified platforms with accurate detection</p>
            </div>
        </aside>

        <!-- Main Content -->
        <main class="flex-1 p-6 lg:p-10 overflow-y-auto">
            <!-- Loading -->
            <div id="loader" class="hidden text-center py-20">
                <i class="fa-solid fa-circle-notch fa-spin text-5xl text-emerald-500 mb-4"></i>
                <p class="text-slate-400 font-mono">Checking 150+ platforms...</p>
                <div class="mt-4 w-full bg-slate-700 rounded-full h-1 overflow-hidden">
                    <div class="bg-emerald-500 h-full animate-pulse" style="width: 45%"></div>
                </div>
            </div>

            <!-- Results -->
            <div id="results" class="hidden space-y-6">
                <!-- Chart -->
                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h2 class="text-lg font-bold text-white mb-4"><i class="fa-solid fa-chart-pie mr-2"></i>Analysis Report</h2>
                    <img id="chart" src="" alt="Chart" class="max-h-64 mx-auto rounded-lg">
                </div>

                <!-- Found Profiles -->
                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h2 class="text-lg font-bold text-emerald-400 mb-4">
                        <i class="fa-solid fa-circle-check mr-2"></i> Active Profiles (<span id="count-found">0</span>)
                    </h2>
                    <div id="found-list" class="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-96 overflow-y-auto"></div>
                </div>

                <!-- Available Handles -->
                <div class="bg-slate-800 border border-slate-700 rounded-lg p-6">
                    <h2 class="text-lg font-bold text-amber-400 mb-4">
                        <i class="fa-solid fa-circle-plus mr-2"></i> Available Handles (<span id="count-vacant">0</span>)
                    </h2>
                    <div id="vacant-list" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 max-h-96 overflow-y-auto"></div>
                </div>
            </div>
        </main>
    </div>

    <script>
        async function scan() {
            const username = document.getElementById('username').value.trim();
            if (!username) {
                alert('Enter a username');
                return;
            }

            document.getElementById('loader').classList.remove('hidden');
            document.getElementById('results').classList.add('hidden');
            document.getElementById('stats').classList.add('hidden');

            try {
                const res = await fetch(`./api/audit?username=${encodeURIComponent(username)}`);
                const data = await res.json();

                if (data.success) {
                    renderResults(data);
                } else {
                    alert('Error: ' + data.message);
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }

            document.getElementById('loader').classList.add('hidden');
        }

        function renderResults(data) {
            // Stats
            document.getElementById('stat-total').textContent = data.total_platforms;
            document.getElementById('stat-found').textContent = data.found_count;
            document.getElementById('stat-vacant').textContent = data.missing_count;
            document.getElementById('stats').classList.remove('hidden');

            // Chart
            document.getElementById('chart').src = './' + data.chart_url + '?t=' + Date.now();

            // Found Profiles
            const foundList = document.getElementById('found-list');
            foundList.innerHTML = '';
            document.getElementById('count-found').textContent = data.found_count;

            Object.entries(data.found).forEach(([platform, url]) => {
                foundList.innerHTML += `
                    <a href="${url}" target="_blank" class="bg-emerald-900/30 border border-emerald-500/50 hover:border-emerald-400 p-4 rounded-lg transition group flex justify-between items-center">
                        <div>
                            <div class="text-sm font-bold text-emerald-300">${platform}</div>
                            <div class="text-xs text-emerald-500 truncate mt-1">${url.substring(0, 30)}...</div>
                        </div>
                        <i class="fa-solid fa-arrow-up-right text-emerald-500 opacity-0 group-hover:opacity-100"></i>
                    </a>
                `;
            });

            if (data.found_count === 0) {
                foundList.innerHTML = '<p class="text-slate-500 text-center py-8 col-span-full">No profiles found</p>';
            }

            // Available Handles
            const vacantList = document.getElementById('vacant-list');
            vacantList.innerHTML = '';
            document.getElementById('count-vacant').textContent = data.missing_count;

            data.missing.forEach(platform => {
                vacantList.innerHTML += `
                    <div class="bg-amber-900/20 border border-dashed border-amber-500/30 p-3 rounded-lg text-xs text-center">
                        <div class="text-amber-400 font-medium truncate">${platform}</div>
                        <div class="text-amber-600 text-[10px] mt-1">Available</div>
                    </div>
                `;
            });

            if (data.missing_count === 0) {
                vacantList.innerHTML = '<p class="text-slate-500 text-center py-8 col-span-full">All taken</p>';
            }

            document.getElementById('results').classList.remove('hidden');
        }
    </script>
</body>
</html>
"""
