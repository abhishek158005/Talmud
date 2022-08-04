import config
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
        print(data)
        self.sheet_name = sheet_name
        

    
          

    def get_user_password(self):

        """Fetching Username & Password """
        result = self.sheet.values().get(spreadsheetId = '1KvNOLBRAhCBDo-cgZUsh4XnBZDAdfDC4MqqdqSwZedE',# config.SAMPLE_SPREADSHEET_ID, 
                                        range ="USERS!B1:C3").execute()
        get_values = result.get('values' , [])
        print(get_values)
        print('Username & Password Fetched Successfully!')
        return get_values

    def getsheet_id(self):
        result = self.sheet.values().get(spreadsheetId = config.SAMPLE_SPREADSHEET_ID,
                                    range = "STUDENTS!G3:T3").execute()
        get_values = result.get('values', [])
        print(f"GoogleSheet[{self.sheet_name}]: id Fetched Successfully")
        return get_values
        
        

    def getsheet_records(self):
        
        """ Fetching the records from Google Sheet """
        
        result = self.sheet.values().get(spreadsheetId = '1KvNOLBRAhCBDo-cgZUsh4XnBZDAdfDC4MqqdqSwZedE',#config.SAMPLE_SPREADSHEET_ID,
                                    range = F'{self.sheet_name}!G:C' ).execute()
        get_values = result.get('values', [])
        print(get_values)
        print(f"GoogleSheet[{self.sheet_name}]: Records Fetched Successfully")
        return get_values

    def updatesheet_records(self):
        
        
        """ Updating the record in Google Sheet """
       
        records_to_update = self.data
        request = self.sheet.values().update(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range= self.sheet_name, 
        valueInputOption="USER_ENTERED", body={"values":records_to_update}).execute()
        print('Records Updated Successfully!')
        return request

    def appendsheet_records(self):
        
        """ Appending/Inserting record in Google Sheet """

        request = self.sheet.values().append(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range=F'{self.sheet_name}!Z:X', 
            valueInputOption="USER_ENTERED", body={"values":self.data}).execute()
        
        print("Record Inserted Successfully!")
        return request

    def clearsheet_records(self):
        
        """ Clearing records from Google Sheet """
        request = self.sheet.values().clear(spreadsheetId = config.SAMPLE_SPREADSHEET_ID, range="Sheet1!A3:C9").execute()
        print("Records Cleared Successfully!")
        return request




obj = GoogleSheetHandler(sheet_name='STUDENTS')
print(obj.get_user_password())
obj.getsheet_records()
print(obj.appendsheet_records())
print(obj.updatesheet_records())

data = GoogleSheetHandler(sheet_name='STUDENTS').getsheet_records()
data = data[2:]
print("====")
# print(data)
import pandas as pd
df = pd.DataFrame(data, columns=[str(x) for x in range(len(data[0]))])
df.rename(columns={'0':'dob', '2':'id_ type', '4':'id'}, inplace=True)

print(df['id'][0])
# print(df['0'])
# print(df['2'])
# print(df['4'])