import pandas as pd
import numpy as np
import datetime as dt
from datetime import datetime
from bs4 import BeautifulSoup
from helpers.g_sheet_handler import GoogleSheetHandler


MONTH_DICT = {
    '01':'Jan', 
    '02':'Feb', 
    '03':'Mar', 
    '04':'Apr', 
    '05':'May', 
    '06':'Jun', 
    '07':'Jul', 
    '08':'Aug', 
    '09':'Sep', 
    '10':'Oct', 
    '11':'Nov', 
    '12':'Dec'
}

GENDER_DICT = {
    'choice' :1,
    'male' : 2,
    'female' : 3
}

MARRIEGE_DICT = {
    'choice' : 1,
    'Single': 2,
    'married' : 3,
    'Polygamous': 4,
    'divorce': 5,
    'widowed': 6
 }

def get_table_df(page_source, table_id):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find('table', attrs={"id":table_id})
    df = pd.read_html(str(tables))[0].dropna(how='all')
    return df.fillna('')

def passport_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_passport_records()
    data = data[2:]
    df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
    df.rename(columns={'2':'dob', '4':'id_type', '5': 'country', '6':'id','0':'first_name' ,'1':'last_name','empty':'3'}, inplace=True)
    return df

def student_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_student_detail()
    for i in data:
        if len(i)<5:
            for j in range(5-len(i)):
                i.append('')
    data = data[1:]
    df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
    df.rename(columns={'0':'father_name', '3':'immigration_date', '4': 'gender', '2':'marriege_date','1':'marriege_status'}, inplace=True)
    return df 
    

def branchcode_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_branch_records()           
    for i in data:
        if len(i)<2:
            for j in range(2-len(i)):
                i.append('')
    data = data[1:]
    df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
    df.rename(columns={'0':'branch', '3':'code'}, inplace=True)
    return df

def user_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_user_password()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df
   
def get_calendar_selected_date(from_month):
    return MONTH_DICT.get(from_month)

def get_gender(gender):
    return GENDER_DICT.get(gender)   

def get_marriege_status(status):
    return MARRIEGE_DICT.get(status)  

def popup_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_popup_records()
    for i in data:
        if len(i)<3:
            i.append(''*(3-len(i)))      
    df = pd.DataFrame(data[1:], columns=data[0])
    return df
    
def sheet_data_pop_up():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_sheet_pop_up_records()
    # data.replace('', np.nan)
    return data
