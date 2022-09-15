import sys
import time
import json
import utils
import config
import warnings
import datetime
import numpy as np
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
    
    def __init__(self, browser, username, password,user_id):
        self.page_no = 0
        self.browser = browser
        self.username = username
        self.password = password
        self.user_id = user_id

        self.user_login = False
        self.invalid_id = False

        self.pop_up_text = []
        # self.row = 3

    def login_to_site(self,user_id, username, password):
        print("Start user login..")
        try:
            self.browser.get(config.WEB_LINK)
            self.browser.find_element(By.ID,'txtUserName').send_keys(self.user_id)
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
            self.passport_df = utils.passport_data()
            student_df = utils.student_data()
            branch_code_df = utils.branchcode_data()
            for idx in range(len(self.passport_df)):
                print('\n\n\tProcessing for ID:', self.passport_df['id'][idx])
                if username not in branch_code_df['branch'][idx]:
                    print("continue ")
                    # self.row += 1
                    continue
                branch = int(branch_code_df['branch'][idx][5:])+1
                study_code = int(branch_code_df['code'][idx])
                self.browser.implicitly_wait(20)
                # print('== == == == == == == clicking on page number == = = =  ==  ==')
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
                    existing_msg= self.student_exist_or_not(idx)
                    if 'סטודנט זה כבר רשום במוסד אחר' in existing_msg:
                        self.pop_up_text.append([existing_msg, 'NO', '', self.passport_df['id'][idx]])
                        # self.append_data_to_sheet(self.passport_df, idx)
                        print("This student is already registered at another institution.")
                        
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_btnMOK'))).click()
                        continue
                    if "התלמיד כבר קיים במוסד ובסוג לימוד הבאים!" in existing_msg:
                        self.pop_up_text.append([existing_msg, 'NO', '', self.passport_df['id'][idx]])
                        # self.append_data_to_sheet(self.passport_df, idx)
                        time.sleep(5)
                        print('\n\t',{'Student Already Exist!!'})
                        WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ucMessagePopUp_divMessageBox"]/div[3]/div'))).click()
                        continue
                    else:    
                        time.sleep(3)
                        confirmation_msg =self.submission_form(idx, student_df, study_code)
                        print(confirmation_msg)
                        if confirmation_msg is None or confirmation_msg == '':
                            # self.pop_up_text.append([confirmation_msg, 'NO', ''])

                            continue
                        if confirmation_msg == "שמירת תלמיד בוצעה בהצלחה":
                            print('message for form that submit or not ===  === ')
                            time.sleep(5)
                            self.pop_up_text.append(['', 'YES', confirmation_msg, self.passport_df['id'][idx]])
                            WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID,'ucMessagePopUp_divbuttonwrapper'))).click()
                            print("* * & & % % === Successfully Submit Form === % % & & * *")
                        try:
                            pop_up_text = WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage')))

                            self.pop_up_text.append([pop_up_text.text, 'NO', '', self.passport_df['id'][idx]]) 
                        except:
                            pass                
                
                except Exception as err: 
                    if err:
                        print(f'{err} Occured!')
                    continue

        except Exception as err:
            print(f"{err} Occured!")
            try:
                WebDriverWait(self.browser,15).until(EC.element_to_be_clickable((By.ID,'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton2'))).click()
            except:
                pass
        self.push_data_to_sheet()              

    def student_exist_or_not(self, idx):
        if self.passport_df['id_type'][idx] == 'דרכון' or self.passport_df['id_type'][idx] == 'password':
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlPopIdentityType"]/option[3]'))).click()
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine'))).click()
                time.sleep(3)
                countries = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ddlCountryOfOrigine"]/option')))
                for country in countries:
                    try:
                        if country.text in self.passport_df['country'][idx]:
                            time.sleep(3)
                            country.click()
                            break
                        else:
                            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    except ElementClickInterceptedException:
                        print('Exception Occurred!')
                        pass
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_txtIdentifier'))).send_keys(self.passport_df['id'][idx])
                time.sleep(5)
                self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_ctlBirthDate_txtDate').value = '{self.passport_df['dob'][idx]}'")
        else:
            key = self.passport_df['id'][idx]
            input = WebDriverWait(self.browser, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/form/div[3]/div[5]/div[1]/div/div[6]/div[2]/div/div/div[2]/div[3]/div[5]/div/div/div/table/tbody/tr/td/table/tbody/tr[3]/td/input')))
            input.send_keys(key)
            
        try:
            WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton1"]'))).click()
        except:
            WebDriverWait(self.browser,10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnOk'))).click()

        try:
            invalid = self.browser.find_element(By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_cvalID').text
            if invalid == 'מספר זהות לא חוקי':
                self.pop_up_text.append([invalid, 'NO', '', self.passport_df['id'][idx]])
                print("\n\tInvalid ID, Skipping this ID")
                time.sleep(5)
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ContentPlaceHolder1_tabStudyTypeDetails_StudentList_ucStudentsSearchDetails_LinkButton2'))).click()
                self.invalid_id = True
        except NoSuchElementException:
            print('NoSuchElementException')
            pass
        if not self.invalid_id:
            self.continue_or_cancel(idx)
        self.invalid_id = False
        try:
            existing_msg = WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ucMessagePopUp_lblMessage'))).text
        except TimeoutException:
            existing_msg = ''
        return existing_msg
        
    def continue_or_cancel(self, idx):
        try:
            to_check =  WebDriverWait(self.browser,10).until(EC.visibility_of_element_located((By.ID, 'ucMessagePopUp_lblMessage'))).text
            """click on continue or cancel"""
            # time.sleep(900)
            if "תלמיד זה רשום כבר במוסד אחר." in to_check:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnOk'))).click() #continue
                time.sleep(5)
                self.pop_up_text.append([to_check, 'YES', '', self.passport_df['id'][idx]])
                success = WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_lblMessage'))).text
                if success == '':
                    pass
            if 'התלמיד נמצא בתהליך מעבר בין מוסדות אין אפשרות לקלוט אותו' in to_check:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click() #continue
                self.pop_up_text.append([to_check, 'NO', '', self.passport_df['id'][idx]])

            if 'הסטודנט כבר קיים במוסד ובסוג הלימוד הבאים!' in to_check:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click() #continue
                self.pop_up_text.append([to_check, 'NO', '', self.passport_df['id'][idx]]) 
            if 'אם לתלמיד קיימים לימודים של בוקר, אחה"צ, שירות אזרחי או יום שלם - הם יסתיימו החל מרגע זה' in to_check:
                WebDriverWait(self.browser, 10).until(EC.element_to_be_clickable((By.ID, 'ucMessagePopUp_spanBtnCancel'))).click() #continue
                self.pop_up_text.append([to_check, 'NO', '', self.passport_df['id'][idx]]) 
        except TimeoutException:
            print('i did not get any message inside continue or cancel function ==  = =')
            pass

    def submission_form(self, idx, student_df, study_code):
        time.sleep(4)
        current_url = self.browser.current_url
        if current_url == "https://talmud.edu.gov.il/Students/StudentsDetails.aspx?":
            print('[ == ** && $$ == I Am Going To Submit A Form == $$ && ** == ]')
            try:
                WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtFirstName'))).send_keys(self.passport_df['first_name'][idx])
                WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtLastName'))).send_keys(self.passport_df['last_name'][idx])
                if not student_df['father_name'][idx]:
                    print("Father's name not available, setting it to DEFAULT: [No Data Found]")
                    student_df['father_name'][idx] = 'לא נמצאו נתונים'
                else:
                    print("entering father name2")
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.ID,'ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_txtFatherName'))).send_keys(student_df['father_name'][idx])
                GENDER = utils.get_gender(student_df['gender'][idx])
                if not GENDER:
                    print("Gender Not Availabe setting DEFAULT : [MALE]")
                    time.sleep(4)
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlGender"]//option[2]'))).click()
                else:    
                    time.sleep(4)
                    WebDriverWait(self.browser, 10).until(EC.visibility_of_element_located((By.XPATH,f'//*[@id="ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ddlGender"]//option[{GENDER}]'))).click()
                STATUS = utils.get_marriege_status(student_df['marriege_status'][idx])
                time.sleep(4)
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
                    if not self.passport_df['dob'][idx]:
                        self.passport_df['dob'][idx] = '01/01/1990'
                    self.browser.execute_script(f"document.getElementById('ContentPlaceHolder1_TabsStudent_StudentDetails1_ucStudentDetails_ctlBirthDate_txtDate').value = '{self.passport_df['dob'][idx]}'")
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
            print("\tEither the ID is already exists or already registered with another instituin or Invalid ID")
            return ''

    def logout(self):
        try:
            self.user_login = False
            self.browser.find_element(By.ID,'ucTalmudHeader_ucLogOut_lnkLogOut').click(); time.sleep(3)
            self.browser.find_element(By.ID,'ucTalmudHeader_ucLogOut_btnOk').click(); time.sleep(3)
            print('Logged out user(%s) successfully!\n' %self.username)
            time.sleep(3)
        except:
            pass

    def push_data_to_sheet(self):
        print(f"\t\t[Pushing data to drive for user - {self.username}]")
        data_li = self.pop_up_text

        scrap_df = pd.DataFrame(data_li, columns=["POP MESSAGE", "SUCCESS", "POPUP WARNING", "ID"])
        sheet_df = utils.sheet_data_pop_up()
        sheet_df['ID'] = self.passport_df['id']
        j = 0
        for i in range(len(sheet_df['ID'])):
            if j < len(scrap_df['ID']):
            # sheet_df.loc[(sheet_df['SUCCESS'] == '') & (sheet_df['ID'].isin(scrap_df['ID'])), ["POP MESSAGE", "SUCCESS", "POPUP WARNING", "ID"]] = scrap_df[["POP MESSAGE", "SUCCESS", "POPUP WARNING", "ID"]]

                if (sheet_df['SUCCESS'][i] == '') & (sheet_df['ID'][i] == scrap_df['ID'][j]):
                    sheet_df['SUCCESS'][i] = scrap_df['SUCCESS'][j]
                    sheet_df['POP MESSAGE'][i] = scrap_df['POP MESSAGE'][j]
                    sheet_df['POPUP WARNING'][i] = scrap_df['POPUP WARNING'][j]
                    j += 1
        sheet_df = sheet_df.replace(np.nan, "'", regex=True)
        sheet_df = sheet_df.replace("'", "", regex=True)
        sheet_df = sheet_df.drop(columns=['ID'])
        print("now i am pushing the data in google sheet")
        GoogleSheetHandler(data=sheet_df.values.tolist()).appendsheet_records_x()
        # GoogleSheetHandler(data=sheet_df, sheet_name='STUDENTS').appendsheet_records_z()
        print("data insert ==== success  ====")

if __name__=='__main__':
    args = len(sys.argv)
    options = Options()

    if args > 1 and sys.argv[1].lower() == '--headless_mode=on':
        print('sys.argv:', sys.argv)
        """ Custom options for browser """ 
        options.headless = True
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    else:
        options.add_argument('--log-level=3')
        browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print(" * *  * *  * *  * *  * *  * * START  * *  * *  * *  * *  * * ")
    t= GoogleSheetHandler(data=None, sheet_name='STUDENTS')
    t.appendsheet_records_y()
    action = ActionChains(browser)
    users = utils.user_data()
    branch_code_df = utils.branchcode_data()
    pop_data  = len(utils.popup_data())
    for i, user in users.iterrows():
        username, password, user_id = user[0], user[2], user[1]
        scrapper = DataScrapping(browser, username, password,user_id)
        scrapper.login_to_site(user_id, username, password)
        if scrapper.user_login:
            print('===========================')

            while scrapper.get_page():
                scrapper.transfer_student()
            scrapper.push_data_to_sheet()
            scrapper.logout()

        print("End activity for user!\n\n")
    # browser.close()