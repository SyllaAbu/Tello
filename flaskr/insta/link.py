from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import bs4
import json
import pickle


path_chr = 'C:\\Users\\Administrator\\Desktop\\Instagram_Bot\\flaskr\\insta\\chromedriver.exe'

class InstagramBot():
    def __init__(self, username, password):

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--lang=en-US")

        self.browser = webdriver.Chrome(path_chr, options=chrome_options)

        self.username = username
        self.password = password

    def get_data(self):
        self.browser.get(f'https://www.instagram.com/{self.username}?__a=1')

        try:
            elem = self.browser.find_element_by_tag_name("pre")
            content = elem.text
            print(content)
            j = json.loads(content)

            return j
        except Exception:
            return -1

    def sign_in(self):
        self.browser.get('https://www.instagram.com/accounts/login?hl=en')

        time.sleep(2)
        user_name_elem = self.browser.find_element_by_xpath("/html/body/div[1]/section/main/div/article/div/div[1]/div/form/div[2]/div/label/input")
        user_name_elem.clear()
        user_name_elem.send_keys(self.username)
        passworword_elem = self.browser.find_element_by_xpath("/html/body/div[1]/section/main/div/article/div/div[1]/div/form/div[3]/div/label/input")
        passworword_elem.clear()
        passworword_elem.send_keys(self.password)
        passworword_elem.send_keys(Keys.RETURN)
        time.sleep(5)

        print(self.browser.current_url)

        if '/onetap/' in self.browser.current_url:
            self.browser.find_element_by_xpath('/html/body/div[1]/section/main/div/div/div/section/div/button').click()

        time.sleep(2)

        if 'https://www.instagram.com' in self.browser.current_url and '/accounts/login/' not in self.browser.current_url and 'challenge' not in self.browser.current_url:
            pickle.dump(self.browser.get_cookies(), open(f"flaskr/insta/coockies/{self.username}.pkl", "wb"))
            return 0
        
        elif '/challenge/' in self.browser.current_url:
            split = str(self.browser.current_url).split('/')
            return split[4], split[5], -2
                 
        else:
            return -1

    def close_browser(self):
        self.browser.close()
