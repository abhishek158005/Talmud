import sys
import time
import utils
import config
import warnings
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium. webdriver. common. keys import Keys
from selenium.webdriver.chrome.options import Options
from helpers.g_sheet_handler import GoogleSheetHandler
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException


warnings.filterwarnings("ignore")

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
            self.browser.find_element(By.ID,'txtUserName').send_keys(self.username)
            # print("44444")
            self.browser.find_element(By.ID,'txtPassword').send_keys(self.password)
            self.browser.find_element(By.ID,'LoginButton').click()
            print("  Login Successful !!")
            self.user_login = True
        except:
            print("  Login Failed !!\n")
            time.sleep(3)
    
    def get_page(self):
        if self.user_login:
            self.page_no += 1
            if self.page_no >=2:
                return False
            try:
                print("\n\t = = = = = = = = = = [PAGE-NO: ", self.page_no, "] = = = = = = = = = =")
                self.page = self.browser.find_element(By.ID, f'ucTalmudSideBar_tvTalmudt{self.page_no}')
                self.page.click()
                return True
            except:
                print('No more pages!')
            return False

    def transfer_student(self):
        passport_df = utils.passport_data()
        branch_code_df = utils.branchcode_data()

        for idx in range(len(passport_df)):
            branch = int(branch_code_df['branch'][idx][5:])+1
            self.browser.implicitly_wait(20)
            self.browser.find_element(By.ID,f'ucTalmudSideBar_tvTalmudn{branch}').click()
            self.browser.implicitly_wait(20)
            code_idx=4
            while True:
                try:
                    ele = self.browser.find_element(By.ID,f'ucTalmudSideBar_tvTalmudt{code_idx}')
                    if branch_code_df['code'][idx] in ele.text:
                        ele.click()
                        break
                    code_idx += 1
                except NoSuchElementException:
                    code_idx += 1
        
            self.browser.implicitly_wait(20)
            self.browser.find_element(By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_tab').click()
            self.browser.implicitly_wait(20)
            self.browser.find_element(By.ID, 'ContentPlaceHolder1_btnStudentAcceptence3').click()
            self.browser.implicitly_wait(20); time.sleep(5)
            if passport_df['id_type'][idx] == 'דרכון':
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType"]/option[3]'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine'))).click()
                time.sleep(3)
                countries = WebDriverWait(self.browser, 10).until(EC.visibility_of_all_elements_located((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine')))
                for country in countries:
                    try:
                        if country.text == passport_df['country'][idx]:
                            time.sleep(3)
                            country.click()
                            break
                        else:
                            country.send_keys(Keys.PAGE_DOWN)
                    except ElementClickInterceptedException:
                        print('Exception Occurred!')
                        pass
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_txtIdentifier'))).send_keys(passport_df['id'][idx])
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ctlBirthDate_txtDate'))).send_keys(passport_df['dob'][idx])
            else:    
                key = passport_df['id'][idx]
                input = WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/div[5]/div[1]/div/div[6]/div[2]/div/div/div[2]/div[3]/div[5]/div/div/div/table/tbody/tr/td/table/tbody/tr[3]/td/input')))
                input.send_keys(key)
            WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton1"]'))).click()
            try:
                invalid = self.browser.find_element(By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_cvalID').text
                if invalid == 'מספר זהות לא חוקי':
                    WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton2'))).click()
            except NoSuchElementException:
                pass

            pop_up_text = WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage')))
            print(pop_up_text.text)
            self.pop_up_text[passport_df['id'][idx]] = pop_up_text.text            
                
            try:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnOk'))).click()
                GoogleSheetHandler(data=[[self.pop_up_text[passport_df['id'][idx]], 'OK']], sheet_name='STUDENTS').appendsheet_records_x()
            except TimeoutException:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click()
                GoogleSheetHandler(data=[['NO', self.pop_up_text[passport_df['id'][idx]]]], sheet_name='STUDENTS').appendsheet_records_z()


    def logout(self):
        self.user_login = False
        self.browser.find_element(By.ID,'ucTalmudHeader_ucLogOut_lnkLogOut').click(); time.sleep(3)
        self.browser.find_element(By.ID,'ucTalmudHeader_ucLogOut_btnOk').click(); time.sleep(3)
        print('Logged out user(%s) successfully!\n' %self.username)
        time.sleep(3)


    def push_data_to_drive(self):
        print(f"\t\t[Pushing data to drive for user - {self.username}]")
        data = utils.flattened_data(self)
        GoogleSheetHandler(data=data, sheet_name=config.SHEET_NAME).appendsheet_records()

if __name__=='__main__':
    args = len(sys.argv)
    options = Options()

    if args > 1 and sys.argv[1].lower() == '--headless_mode=on':
        print('sys.argv:', sys.argv)
        """ Custom options for browser """ 
        options.headless = True
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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
                scrapper.transfer_student()
            # scrapper.push_data_to_drive()
            scrapper.logout()

        print("End activity for user!\n\n")
    browser.close()
