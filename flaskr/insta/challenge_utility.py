from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import bs4
import json
import pickle


path_chr = 'C:\\Users\\Administrator\\Desktop\\Instagram_Bot\\flaskr\\insta\\chromedriver.exe'

class Challenge():
    def __init__(self, username, password, link, code):

        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--lang=en-US")

        self.browser = webdriver.Chrome(path_chr, options=chrome_options)

        self.username = username
        self.password = password
        self.link = link
        self.code = code

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

    def challenge_sign_in(self):
        self.browser.get(self.link)

        time.sleep(3)
        user_name_elem = self.browser.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[2]/div/label/input")
        user_name_elem.clear()
        user_name_elem.send_keys(self.username)
        passworword_elem = self.browser.find_element_by_xpath("/html/body/div[1]/section/main/article/div[2]/div[1]/div/form/div[3]/div/label/input")
        passworword_elem.clear()
        passworword_elem.send_keys(self.password)
        passworword_elem.send_keys(Keys.RETURN)
        time.sleep(5)

        self.browser.find_element_by_xpath('/html/body/div[1]/section/div/div/div[3]/form/span/button').click()

        time.sleep(5)

        if self.code != '':
            code_inp = self.browser.find_element_by_xpath('/html/body/div[1]/section/div/div/div[2]/form/div/input')
            code_inp.clear()
            code_inp.send_keys(self.code)
            code_inp.send_keys(Keys.RETURN)
            time.sleep(10)
            if 'https://www.instagram.com' in self.browser.current_url and '/accounts/login/' not in self.browser.current_url and 'challenge' not in self.browser.current_url:
                pickle.dump(self.browser.get_cookies(), open(f"flaskr/insta/coockies/{self.username}.pkl", "wb"))
                return 0
        


    def close_browser(self):
        self.browser.close()
