import sys
import time
import warnings
import pandas as pd
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

import config
import utils
from helpers.g_sheet_handler import GoogleSheetHandler

warnings.filterwarnings("ignore")

ELEMENT_ID_INITIAL = 'ContentPlaceHolder1_tabInstituteDetails_InsDetails1_ucInstitutesDetails'
STATUS_MODE = "מאושר לתמיכה"

class DataScrapping():
    
    def __init__(self, browser, username, password):
        self.page_no = 0
        self.browser = browser
        self.username = username
        self.password = password
        self.user_login = False
        
        self.pop_up_text= {}

    def login_to_site(self):
        print("Start user login..")
        try:
            self.browser.get(config.WEB_LINK)
            self.browser.find_element_by_id('txtUserName').send_keys(self.username)
          
            self.browser.find_element_by_id('txtPassword').send_keys(self.password)
            self.browser.find_element_by_id('LoginButton').click()
            print("  Login Successful !!")
            self.user_login = True
        except:
            print("  Login Failed !!\n")
            time.sleep(3)
    
    def  Absorption(self):
        data = GoogleSheetHandler(sheet_name='STUDENTS').getsheet_records()
        data = data[2:]
        df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
        df.rename(columns={'0':'dob', '2':'id_ type', '4':'id'}, inplace=True)

        self.browser.implicitly_wait(20)
        self.browser.find_element_by_id(f'ucTalmudSideBar_tvTalmudn{self.page_no}').click()
        self.browser.implicitly_wait(20)
        self.browser.find_element_by_id('ucTalmudSideBar_tvTalmudt5').click()
        for x in range(2):
            print(x)
            self.browser.implicitly_wait(20)
            self.browser.find_element_by_id('ContentPlaceHolder1_tabStudyTypeDetails_StudentList_tab').click()
            self.browser.implicitly_wait(20)
            self.browser.find_element_by_id('ContentPlaceHolder1_btnStudentAcceptence3').click()
            self.browser.implicitly_wait(20); time.sleep(5)
            input = WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/div[5]/div[1]/div/div[6]/div[2]/div/div/div[2]/div[3]/div[5]/div/div/div/table/tbody/tr/td/table/tbody/tr[3]/td/input')))
            key = df['id'][x]
            print('===============',key)
            input.send_keys(key)
            # self.browser.find_element_by_xpath('//*[@id="ContentPlaceHoldter1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_txtIdentifier"]').send_keys('12345')
            # self.browser.implicitly_wait(20)
            # /self.browser.find_element_by_id('ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton1').click()
            WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton1"]'))).click()
            pop_up_text = WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage')))
            # pop_up_text = self.browser.find_element_by_id('ucMessagePopUp_lblMessage')
            # ucMessagePopUp_lblMessage
            # pprint(self.browser.page_source)
            print(pop_up_text.text)
            self.pop_up_text[self.page_no] = pop_up_text.text            
            
            try:
                self.browser.find_element_by_id('ucMessagePopUp_spanBtnOk').click()#ucMessagePopUp_spanBtnCancel
            except:
                self.browser.find_element_by_id('ucMessagePopUp_spanBtnCancel').click()

        print(self.pop_up_text)
        self.browser.get(config.WEB_LINK)
        
    def logout(self):
        self.user_login = False
        self.browser.find_element_by_id('ucTalmudHeader_ucLogOut_lnkLogOut').click(); time.sleep(3)
        self.browser.find_element_by_id('ucTalmudHeader_ucLogOut_btnOk').click(); time.sleep(3)
        print('Logged out user(%s) successfully!\n' %self.username)
        time.sleep(3)

    def get_page(self):
        if self.user_login:
            self.page_no += 1
            try:
                print("\n\t = = = = = = = = = = [PAGE-NO: ", self.page_no, "] = = = = = = = = = =")
                self.page = self.browser.find_element_by_id(f'ucTalmudSideBar_tvTalmudt{self.page_no}')
                self.page.click()
                return True
            except:
                print('No more pages!')
            return False

    def push_data_to_drive(self):
        print(f"\t\t[Pushing data to drive for user - {self.username}]")
        data = utils.flattened_data(self)
        GoogleSheetHandler(data=data, sheet_name='STDUENTS').appendsheet_records()

if __name__=='__main__':
    args = len(sys.argv)
    options = Options()

    if args > 1 and sys.argv[1].lower() == '--headless_mode=on':
        print('sys.argv:', sys.argv)
        """ Custom options for browser """ 
        options.headless = True
        browser = webdriver.Chrome(executable_path=config.DRIVER_PATH, options=options)
    else:
        browser = webdriver.Chrome(executable_path=config.DRIVER_PATH)

    print(" * *  * *  * *  * *  * *  * * START  * *  * *  * *  * *  * * ")
    action = ActionChains(browser)
    users = GoogleSheetHandler(sheet_name='USERS').get_user_password()
    for user in users[1:]:
        print('===========================')
        username, password = user[0], user[1]
        print("Start scrapping for user: %s" %username)
        scrapper = DataScrapping(browser, username, password)
        scrapper.login_to_site()

        if scrapper.user_login:
            print('===========================')

            while scrapper.get_page():
                scrapper.Absorption()
            scrapper.push_data_to_drive()
            scrapper.logout()

        print("End activity for user!\n\n")
    browser.close()
