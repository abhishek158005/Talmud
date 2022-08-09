import pandas as pd
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime
from helpers.g_sheet_handler import GoogleSheetHandler


def get_table_df(page_source, table_id):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find('table', attrs={"id":table_id})
    df = pd.read_html(str(tables))[0].dropna(how='all')
    return df.fillna('')

def passport_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_passport_records()
    data = data[2:]
    df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
    df.rename(columns={'0':'dob', '2':'id_type', '3': 'country', '4':'id'}, inplace=True)
    return df

def branchcode_data():
    data = GoogleSheetHandler(sheet_name='STUDENTS').get_branch_records()
    data = data[2:]
    df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
    df.rename(columns={'0':'branch', '3':'code'}, inplace=True)
    return df