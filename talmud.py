import sys
import time
import utils
import config
import warnings
import datetime
import pandas as pd
from cgitb import text
from tkinter import Button
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium. webdriver. common. keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from helpers.g_sheet_handler import GoogleSheetHandler
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
        
        self.invalid_id = False
        self.pop_up_text= {}

    def login_to_site(self):
        print("Start user login..")
        try:
            self.browser.get(config.WEB_LINK)
            self.browser.find_element(By.ID,'txtUserName').send_keys(self.username)
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
        try:
            passport_df = utils.passport_data()
            student_df = utils.student_data()
            branch_code_df = utils.branchcode_data()
            for idx in range(len(passport_df)):
                print('\n\n\tProcessing for ID:', passport_df['id'][idx])
                # print(branch_code_df['branch'][idx][5:])
                branch = int(branch_code_df['branch'][idx][5:])+1
                study_code = int(branch_code_df['code'][idx])
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
                self.browser.find_element(By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_tab').click()
                self.browser.implicitly_wait(10)
                try:
                    self.browser.find_element(By.ID, 'ContentPlaceHolder1_btnStudentAcceptence3').click()
                    self.browser.implicitly_wait(10); time.sleep(5)
                    existing_msg= self.student_exist_or_not(idx, passport_df)
                    if 'סטודנט זה כבר רשום במוסד אחר' in existing_msg:
                        print("This student is already registered at another institution.")
                        continue
                    if "התלמיד כבר קיים במוסד ובסוג לימוד הבאים!" in existing_msg:
                        time.sleep(5)
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ucMessagePopUp_divMessageBox"]/div[3]/div'))).click()
                        print('\n\n\t',{'message': 'Student Already Exist!!'})
                        continue
                    else:    
                        print('Going for Submission Form')
                        time.sleep(3)
                        confirmation_msg =self.submission_form(idx, passport_df, student_df, study_code)
                        if confirmation_msg is None or confirmation_msg == '':
                            continue
                        if confirmation_msg == "שמירת תלמיד בוצעה בהצלחה":
                            time.sleep(5)
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID,'ucMessagePopUp_divbuttonwrapper'))).click()
                            print("* * & & % % === Successfully Submit Form === % % & & * *")
                        try:
                            pop_up_text = WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage')))
                            self.pop_up_text[passport_df['id'][idx]] = pop_up_text.text  
                        except:
                            pass                
                        try:
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnOk'))).click()
                            GoogleSheetHandler(data=[[self.pop_up_text[passport_df['id'][idx]], 'OK']], sheet_name='STUDENTS').appendsheet_records_x()
                        except TimeoutException:
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click()
                            GoogleSheetHandler(data=[['NO', self.pop_up_text[passport_df['id'][idx]]]], sheet_name='STUDENTS').appendsheet_records_z()
                
                except Exception as err: 
                    if err:
                        print(f'{err} Occured!')
                        print('\n\n\tSkipping this ID')
                    continue
                    
            
        except Exception as err:
            print(f"{err} Occured!")
            WebDriverWait(self.browser,15).until(EC.element_to_be_clickable((By.ID,'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton2'))).click()
                
                   

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

    def student_exist_or_not(self, idx, passport_df):
        if passport_df['id_type'][idx] == 'דרכון':
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType"]/option[3]'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine'))).click()
                time.sleep(3)
                countries = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine"]/option')))
                for country in countries:
                    try:
                        if country.text in passport_df['country'][idx]:
                            time.sleep(3)
                            country.click()
                            break
                        else:
                            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    except ElementClickInterceptedException:
                        print('Exception Occurred!')
                        pass
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_txtIdentifier'))).send_keys(passport_df['id'][idx])
                # WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ctlBirthDate_txtDate')))
                time.sleep(5)
                self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ctlBirthDate_txtDate').value = '{passport_df['dob'][idx]}'")
        else:
            key = passport_df['id'][idx]
            input = WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/div[5]/div[1]/div/div[6]/div[2]/div/div/div[2]/div[3]/div[5]/div/div/div/table/tbody/tr/td/table/tbody/tr[3]/td/input')))
            input.send_keys(key)
        WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton1"]'))).click()
        try:
            invalid = self.browser.find_element(By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_cvalID').text
            if invalid == 'מספר זהות לא חוקי':
                print("\n\tInvalid ID, Skipping this ID")
                time.sleep(5)
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton2'))).click()
                self.invalid_id = True
        except NoSuchElementException:
            print('NoSuchElementException')
            pass
        if not self.invalid_id:
            self.continue_or_cancel()
        try:
    
            # existing_msg = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ucMessagePopUp_lblMessage'))).text
            existing_msg = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ucMessagePopUp_lblMessage'))).text
            print("existing_msg = ",existing_msg)
        except TimeoutException:
            existing_msg = ''
        return existing_msg

    def continue_or_cancel(self):
        try:
            to_check =  WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage'))).text
            to_confirm = WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage'))).text
            """click on continue or cancel"""
            if "תלמיד זה רשום כבר במוסד אחר." in to_check:
                # print("enter in to_check block")
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnOk'))).click() #continue
                # WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_btnMCancel'))).click() #cancel
                time.sleep(5)
                success = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_lblMessage'))).text
                # print("Enter Into Success block")
                print("This is first time that we are getting this popup box")
                if success == '':
                    pass
                # WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_btnMCancel'))).click() #success 
            if to_confirm == 'התלמיד נמצא בתהליך מעבר בין מוסדות אין אפשרות לקלוט אותו':
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click() #continue
        except TimeoutException:
            pass

    def submission_form(self, idx, passport_df, student_df, study_code):
        time.sleep(4)
        current_url = self.browser.current_url
        print(type(current_url))
        print("44455= = = ",current_url)
        if current_url == "https://talmud.edu.gov.il/Students/StudentsDetails.aspx?":
            try:
                WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtFirstName'))).send_keys(passport_df['first_name'][idx])
                WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtLastName'))).send_keys(passport_df['last_name'][idx])
                if not student_df['father_name'][idx]:
                    print("entering father name1")
                    print("Father's name not available, setting it to DEFAULT: [No Data Found]")
                    student_df['father_name'][idx] = 'לא נמצאו נתונים'
                else:
                    print("entering father name2")
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtFatherName'))).send_keys(student_df['father_name'][idx])
                GENDER = utils.get_gender(student_df['gender'][idx])
                if not GENDER:
                    print("gender not found")
                    print("Gender Not Availabe setting DEFAULT : [MALE]")
                    time.sleep(4)
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlGender"]//option[2]'))).click()
                else:    
                    print("gender  found")
                    time.sleep(4)
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlGender"]//option[{GENDER}]'))).click()
                print('status')
                STATUS = utils.get_marriege_status(student_df['marriege_status'][idx])
                time.sleep(4)
                print('status found')
                if not student_df['marriege_date'][idx]:
                    student_df['marriege_date'][idx] = '01/01/2020'
                if not STATUS:
                    if study_code == 300:
                        WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlFamilyStatus"]//option[2]'))).click()
                    else:
                        WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlFamilyStatus"]//option[3]'))).click()
                        time.sleep(5)
                        self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ctlMarriageDate_txtDate').value = '{student_df['marriege_date'][idx]}'")
                else:    
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlFamilyStatus"]//option[{STATUS}]'))).click()
                    time.sleep(5)
                    self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ctlMarriageDate_txtDate').value = '{student_df['marriege_date'][idx]}'")

                time.sleep(5)
                try:
                    if not passport_df['dob'][idx]:
                        passport_df['dob'][idx] = '01/01/1990'
                    self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ctlBirthDate_txtDate').value = '{passport_df['dob'][idx]}'")
                except Exception as err:
                    print(err)
                    pass
                if not student_df['immigration_date'][idx]:
                    student_df['immigration_date'][idx] = '23/04/2020'
                self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ctlImmigrationDate_txtDate').value = '{student_df['immigration_date'][idx]}'")
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID,'ContentPlaceHolder1_btnSave'))).click()
                
                confirmation_msg = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ucMessagePopUp_lblMessage'))).text
                return confirmation_msg
            except Exception as err:
                print("Error ===: ",err)   
        else:
            print("url not match")
            return ''




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
