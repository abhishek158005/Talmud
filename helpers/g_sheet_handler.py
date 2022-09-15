import config
import pandas as pd
import numpy as np
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import service_account



class GoogleSheetHandler:

    creds = None
    creds = service_account.Credentials.from_service_account_file(config.SERVICE_ACCOUNT_FILE, scopes = config.SCOPES)

    # Call the Sheets API
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()


    def __init__(self, data=None, sheet_name=None):
        self.data = data
        self.sheet_name = sheet_name          

    def get_user_password(self):

        """Fetching Username & Password """
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, 
                                        range ="USERS!A:C").execute()
        get_values = result.get('values' , [])
        print('Username & Password Fetched Successfully!')
        print(get_values)
        return get_values


    def get_student_detail(self):

        """Fetching Student Details """
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, 
                                        range ="STUDENTS!AA:AE").execute()
        get_values = result.get('values' , [])
        # print(get_values)
        print('Student Details Successfully Fetched')
        # print(get_values)
        return get_values        


    def getsheet_id(self):
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = "STUDENTS!G3:T3").execute()
        get_values = result.get('values', [])
        print(f"GoogleSheet[{self.sheet_name}]: id Fetched Successfully")
        return get_values
        

    def get_passport_records(self):
        
        """ Fetching the records from Google Sheet """
        
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = F'{self.sheet_name}!G:A' ).execute()
        get_values = result.get('values', [])
        print(f"GoogleSheet[{self.sheet_name}]: Records Fetched Successfully")
        return get_values

    def get_branch_records(self):
        
        """ Fetching the records from Google Sheet """
        
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = F'{self.sheet_name}!T:W' ).execute()
        get_values = result.get('values', [])
        print(f"GoogleSheet[{self.sheet_name}]: Records Fetched Successfully")
        return get_values

    def updatesheet_records(self):
        
        """ Updating the record in Google Sheet """
       
        records_to_update = self.data
        request = self.sheet.values().update(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range=self.sheet_name, 
        valueInputOption="USER_ENTERED", body={"values":records_to_update}).execute()
        print('Records Updated Successfully!')
        return request

    def appendsheet_records_x(self):
        print("this is our data for saving ======\n\n",self.data)
        
        """ Appending/Inserting record in Google Sheet """
        request = self.sheet.values().update(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range=f'STUDENTS!X3:Z', 
            valueInputOption="USER_ENTERED", body={"values":self.data}).execute()
        
        print("Record Inserted Successfully!")
        return request

    def appendsheet_records_y(self):
        max_length = len(self.get_passport_records())
        self.data = [["'"]]
        request = self.sheet.values().update(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range=f'STUDENTS!X{max_length-1}:Z', 
            valueInputOption="USER_ENTERED", body={"values":self.data}).execute()
        return request    

    def get_popup_records(self):
        
        """ Fetching the records from Google Sheet """
        
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = F'{self.sheet_name}!X:Z' ).execute()
        get_values = result.get('values', [])
        return get_values  
    
    def get_sheet_pop_up_records(self):
        
        """ Fetching the records from Google Sheet """
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = f'STUDENTS!X:Z' ).execute()
        get_values = result.get('values', [])
        max_length = self.get_passport_records()
        k = 0
        print(len(get_values))
        for j in range(len(max_length)):
            # if len(get_values[j]) != len(max_length[j]):
                # for i in range(len(max_length[i]) - len(get_values[i])):
            if len(get_values) > j :    
                print(get_values[j])    
                print(len(get_values[j]))  
                if len(get_values[j]) < 3:
                    for i in range(3 - len(get_values[j])):
                        get_values[j].append('')
            else:
                get_values.append(["","",""])            
        # print(get_values)            
        df = pd.DataFrame(get_values[2:], columns = get_values[0])
        # print('df:', df)
        return df
   

    def appendsheet_records_z(self):
        
        """ Appending/Inserting record in Google Sheet """

        request = self.sheet.values().append(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range=f'{self.sheet_name}!Y3:AA3', 
            valueInputOption="USER_ENTERED", body={"values":self.data}).execute()
        print("Record Inserted Successfully!")
        return request

    def clearsheet_records(self):
        
        """ Clearing records from Google Sheet """
        request = self.sheet.values().clear(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range="").execute()
        print("Records Cleared Successfully!")
        return request


# t= GoogleSheetHandler(data=None, sheet_name='STUDENTS')
# t.get_sheet_pop_up_records()