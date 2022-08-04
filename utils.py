import pandas as pd
from bs4 import BeautifulSoup
import threading
import time
from datetime import datetime

def get_table_df(page_source, table_id):
    soup = BeautifulSoup(page_source, 'html.parser')
    tables = soup.find('table', attrs={"id":table_id})
    df = pd.read_html(str(tables))[0].dropna(how='all')
    return df.fillna('')

def flattened_data(scrapper):
    result = []
    for page in range(1, scrapper.page_no):
        try:
            row = [datetime.now().strftime("%Y-%m-%d, %H:%M:%S")] +\
                    scrapper.pop_up_text[page]
            print(row)

            result.append(row)
        except KeyError:
            continue
    return result
