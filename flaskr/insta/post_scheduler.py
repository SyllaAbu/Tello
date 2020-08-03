import schedule as schedule
import time
from time import sleep
import datetime
import autoit
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import bs4
import json
import pickle
import flaskr.insta.settings as settings


create_app = 'C:\\Users\\Administrator\\Desktop\\Instagram_Bot\\flaskr\\static\\photos_storage'


def check():
    time_pub = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M')
    conn = sqlite3.connect('..\\..\\instance\\flaskr.sqlite')
    cursor = conn.cursor()

    accounts = cursor.execute(
        'SELECT username, time_to_post, photo, caption, is_posted, post_scheduling.account_id'
        ' FROM accounts INNER JOIN post_scheduling ON accounts.account_id = post_scheduling.account_id'
        ' WHERE is_posted = ? AND time_to_post = ?',
        (0, time_pub,)
    ).fetchall()

    for account in accounts:
        print(account)
        ps = PostScheduler(account[0], account[2], account[3])
        ps.login()
        ps.post()
        cursor.execute(
            ' UPDATE post_scheduling SET is_posted = ?'
            ' WHERE time_to_post = ?',
            (1,time_pub)
        )
        conn.commit()

    conn.close()


class PostScheduler:
    def __init__(self, username, path, caption):
        chrome_options = Options()
        chrome_options.add_argument("--lang=en-US")
        chrome_options.add_argument(f"user-agent={settings.user_agent}")
        chrome_options.add_argument("window-size=360,740")
        self.browser = webdriver.Chrome(
            settings.chrome_driver_path,
            options=chrome_options
        )

        self.username = username
        self.path = path
        self.caption = caption

    def login(self):
        self.browser.get('https://www.instagram.com/')

        for cookie in pickle.load(open(f"coockies/{self.username}.pkl", "rb")):
            if 'expiry' in cookie:
                del cookie['expiry']

            self.browser.add_cookie(cookie)

        self.browser.get('https://www.instagram.com')
        time.sleep(2)

        try:
            self.browser.find_element_by_xpath('/html/body/div[4]/div/div/div/div[3]/button[2]').click()
        except:
            pass

        try:
            self.browser.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[2]').click()
            time.sleep(3)
        except:
            pass

    def post(self):
        try:
            self.browser.find_element_by_xpath("/html/body/div[1]/section/main/div/button").click()
            time.sleep(5)
            self.browser.find_element_by_xpath("/html/body/div[1]/section/nav[2]/div/div/div[2]/div/div/div[3]").click()
    
        except:
            self.browser.find_element_by_xpath("/html/body/div[1]/section/nav[2]/div/div/div[2]/div/div/div[3]").click()
    
        time.sleep(3)
    
        autoit.win_active("Open")
        sleep(4)

        autoit.control_send("Open", "Edit1", f'{create_app}\{self.path}')
        sleep(3)

        try:
            autoit.control_send("Open", "Edit1", "{ENTER}")
            autoit.control_send("Open", "Edit1", "{ENTER}")

            sleep(5)

            self.browser.find_element_by_xpath("/html/body/div[1]/section/div[1]/header/div/div[2]/button").click()

            sleep(5)

            caption_field = self.browser.find_element_by_xpath("/html/body/div[1]/section/div[2]/section[1]/div[1]/textarea")

            caption_field.send_keys(self.caption)

            time.sleep(5)

            self.browser.find_element_by_xpath("/html/body/div[1]/section/div[1]/header/div/div[2]/button").click()

            print('Pubblicato')
            sleep(5)

            self.browser.close()
        except Exception:
            pass


schedule.every().minute.at(':00').do(check)

while 1:
    schedule.run_pending()
    time.sleep(10)
