from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import bs4
import json
import pickle
import flaskr.insta.settings as setting
from requests import get
import sqlite3
from datetime import datetime


class Like():
    def __init__(self, username, section, hashtags_or_locations, post_number, follower_number, following_number, bio,
                 in_username, profiles_number):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument(f"user-agent={setting.user_agent}")
        chrome_options.add_argument("window-size=360,740")
        self.browser = webdriver.Chrome(
            setting.chrome_driver_path,
            options=chrome_options
        )

        self.username = username
        self.post_link = ''
        self.section = section
        self.hashtags_or_locations = hashtags_or_locations
        self.post_number = post_number
        self.follower_number = follower_number
        self.following_number = following_number
        self.bio = bio
        self.in_username = in_username
        self.profiles_number = profiles_number

        self.users_id = []
        self.users = []
        self.profiles_counter = 0
        self.hashtags_list = []
        self.count = 0

    def like(self, user):
        conn = sqlite3.connect(setting.db)
        cursor = conn.cursor()
        # take username
        self.browser.get(f"{user}?__a=1")
        time.sleep(2)
        try:
            elem = self.browser.find_element_by_tag_name("pre")
            content = elem.text
            print(content)
            j = json.loads(content)
        except Exception:
            j = -1

        if j != -1:
            username = j['graphql']['shortcode_media']['owner']['username']
            # take post numbers followers number and following number
            self.browser.get(f"https://www.instagram.com/{username}/?__a=1")
            time.sleep(2)
            try:
                elem = self.browser.find_element_by_tag_name("pre")
                content = elem.text
                print(content)
                j = json.loads(content)
            except Exception:
                j = -1

            if j != -1:
                full_name = j['graphql']['user']['full_name']
                x = j['graphql']['user']['edge_owner_to_timeline_media']['count']
                y = j['graphql']['user']['edge_followed_by']['count']
                z = j['graphql']['user']['edge_follow']['count']
                bio = j['graphql']['user']['biography']

                if int(x) >= int(self.post_number) and int(y) >= int(self.follower_number) and int(z) >= int(
                        self.following_number) and self.in_username in full_name and self.bio in bio:
                    # liking
                    self.browser.get(user)
                    time.sleep(3)
                    try:
                        self.post_link = self.browser.current_url
                        self.browser.find_element_by_xpath(
                            '//*[@id="react-root"]/section/main/div/div[1]/article/div[2]/section[1]/span[1]/button').click()
                        cursor.execute(
                            ' INSERT INTO liked_accounts(username, liked_post, timestamp)'
                            ' VALUES(?,?,?)',
                            (self.username, self.post_link, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)
                        )
                        conn.commit()
                    except Exception:
                        pass

    def get_users_by_locaton(self, id, slug):
        pic_hrefs = []
        self.browser.get(f"https://www.instagram.com/explore/locations/{id}/{slug}/?__a=1")

        time.sleep(2)

        id = slug = ''

        try:
            elem = self.browser.find_element_by_tag_name("pre")
            content = elem.text
            print(content)
            j = json.loads(content)
            id = j['location_list'][0]['id']
            slug = j['location_list'][0]['slug']
        except Exception:
            pass

        self.browser.get(f"https://www.instagram.com/explore/locations/{id}/{slug}/")

        time.sleep(2)

        for i in range(1, 3):
            try:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # get tags
                hrefs_in_view = self.browser.find_elements_by_tag_name('a')
                # finding relevant hrefs
                hrefs_in_view = [elem.get_attribute('href') for elem in hrefs_in_view
                                 if '.com/p/' in elem.get_attribute('href')]
                # building list of unique photos
                [pic_hrefs.append(href) for href in hrefs_in_view if href not in pic_hrefs]
                print(pic_hrefs)
            except Exception:
                continue

            return pic_hrefs

    def location(self):
        self.locations_list = str(self.hashtags_or_locations).split(' ')
        print(self.locations_list)

        conn = sqlite3.connect(setting.db)
        cur = conn.cursor()
        cont = 0

        for location in self.locations_list:
            city_id, city_slug = cur.execute(
                'SELECT id, slug'
                ' FROM city'
                ' WHERE name = ?',
                (location,)
            ).fetchone()

            self.users += self.get_users_by_locaton(city_id, city_slug)

        for user in self.users:
            if cont < int(self.profiles_number):
                self.like(user)
                cont += 1
            else:
                break

    def hashtag(self):
        self.hashtags_list = str(self.hashtags_or_locations).split(' ')
        print(self.hashtags_list)
        cont = 0
        for hashtag in self.hashtags_list:
            self.users = self.get_users(hashtag)

        print(self.users)

        for user in self.users:
            if cont < int(self.profiles_number):
                self.like(user)
                cont += 1
            else:
                break

    def get_users(self, hashtag_page):
        pic_hrefs = []
        self.browser.get(f"https://www.instagram.com/explore/tags/{hashtag_page}/")
        time.sleep(2)
        for i in range(1, 3):
            try:
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                # get tags
                hrefs_in_view = self.browser.find_elements_by_tag_name('a')
                # finding relevant hrefs
                hrefs_in_view = [elem.get_attribute('href') for elem in hrefs_in_view
                                 if '.com/p/' in elem.get_attribute('href')]
                # building list of unique photos
                [pic_hrefs.append(href) for href in hrefs_in_view if href not in pic_hrefs]
                print(pic_hrefs)
            except Exception:
                continue

            return pic_hrefs

    def login(self):
        self.browser.get('https://www.instagram.com/')

        for cookie in pickle.load(open(
                f"{setting.cookies_path}\\{self.username}.pkl",
                "rb")):
            if 'expiry' in cookie:
                del cookie['expiry']

            self.browser.add_cookie(cookie)

        self.browser.get('https://www.instagram.com')
        time.sleep(2)

        try:
            self.browser.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[2]').click()
            time.sleep(3)
        except Exception:
            pass

    def close_browser(self):
        self.browser.close()
