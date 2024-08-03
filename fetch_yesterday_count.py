from datetime import datetime, timedelta
import pytz
import requests
import logging
import json
from google.cloud import storage
import os
from collections import defaultdict
import pandas as pd
from io import BytesIO

from sendemail import send_email  # Import BytesIO to handle in-memory file

# Path to your service account key file
service_account_key_path = 'nextaqua-firestore-key.json'

# Set the environment variable to specify the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path

# Initialize a client
storage_client = storage.Client()

# Set up logging
logging.basicConfig(level=logging.INFO)
def get_formatted_date(input_date_string):
    # Define the input format
    input_format = '%d-%m-%Y'
    # Parse the input date string to a datetime object
    date_obj = datetime.strptime(input_date_string, input_format)
    # Define the output format
    output_format = '%B %d, %Y'
    # Format the datetime object to the desired output format
    return date_obj.strftime(output_format)
def get_date_string():
    timezone = pytz.timezone('Asia/Kolkata')
    yesterday = datetime.now(timezone) - timedelta(days=1)
    return yesterday.strftime('%d-%m-%Y')
# Generate Excel File
def generate_excel_file(data):
    """
    Generate an Excel file from the data dictionary.
    """
    # Create a dictionary to store the aligned data
    aligned_data = {
        'Date': list(data['day_counts'].keys()),
        'Day Count': list(data['day_counts'].values()),
        'Week': list(data['week_counts'].keys()),
        'Week Count': list(data['week_counts'].values()),
        'Month': list(data['month_counts'].keys()),
        'Month Count': list(data['month_counts'].values())
    }

    # Find the maximum length among the lists
    max_length = max(len(aligned_data['Date']), len(aligned_data['Week']), len(aligned_data['Month']))

    # Function to align data to the max length
    def align_list(lst, fill_value=''):
        return lst + [fill_value] * (max_length - len(lst))

    # Align all lists
    for key in aligned_data:
        aligned_data[key] = align_list(aligned_data[key])

    # Create the DataFrame
    df = pd.DataFrame(aligned_data)

    # Add 'Total Count' and 'Yesterday Count' as separate rows
    total_row = pd.DataFrame({
        'Date': ['Total Count'],
        'Day Count': [data['total_count']],
        'Week': [''],
        'Week Count': [''],
        'Month': [''],
        'Month Count': ['']
    })

    yesterday_row = pd.DataFrame({
        'Date': ['Yesterday Count'],
        'Day Count': [data['yesterday_count']],
        'Week': [''],
        'Week Count': [''],
        'Month': [''],
        'Month Count': ['']
    })

    # Append these rows to the DataFrame
    df = pd.concat([df, total_row, yesterday_row], ignore_index=True)

    # Write the DataFrame to an Excel file
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Counts')
    excel_file.seek(0)
    return excel_file.read()
def sendCheckTrayImageEmail(total_count,yesterday_count,data,date):
    email_subject = f"Checktray Image Count Report: Total {total_count} as of {get_formatted_date(date)}"
    get_formatted_date
    
    email_content = f"""
    <p>Dear Team,</p>
    <p>The Checktray image count for yesterday ({get_formatted_date(date)}) is {yesterday_count}. Please find the attached report for more details.</p>
    <p>Best regards,<br>Backend Team</p>
    """
    # Generate Excel file
    excel_attachment = None#generate_excel_file(data)
    send_email(email_subject, email_content, ['rajesh@aquaexchange.com'],['kranthi@infiplus.xyz'],'developer@nextaqua.in','zdkc wler hovo jclu','Checktray_Image_Count_Report.xlsx',excel_attachment,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    #send_email(email_subject, email_content, ['pavan@aquaexchange.com','karthick@aquaexchange.com','kiran@aquaexchange.com'],['satyasri@aquaexchange.com','aditya@infiplus.xyz','rajesh@aquaexchange.com','kranthi@infiplus.xyz'],'developer@nextaqua.in','zdkc wler hovo jclu','Checktray_Image_Count_Report.xlsx',excel_attachment,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
def fetch_images(bucket_name, prefix):
    try:
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        total_count = 0
        for blob in blobs:
            if blob.name.endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                total_count += 1
        return {'totalCount': total_count}
    except Exception as e:
        logging.error(f"Error fetching images for prefix {prefix}:", exc_info=True)
        return {'totalCount': 0}

def update_check_tray_images_count():
    bucket_name = 'checktray-ml'
    str_date = get_date_string()
    try:
        uploaded = fetch_images(bucket_name, f'uploaded/{str_date}')
        processed = fetch_images(bucket_name, f'ml/{str_date}')

        data = {
            'date': str_date,
            'uploadedCount': uploaded['totalCount'],
            'mlCount': processed['totalCount']
        }

        logging.info('Updated checktray images count: %s', data)

        jango_url = 'https://app.aquaexchange.com/api/general/upsertChecktrayImageCount/'
        jango_api_headers = {"Authorization":"Token e50f000f342fe8453e714454abac13be07f18ac3"}
        response = requests.post(jango_url, json=data,headers=jango_api_headers)
        if response.status_code == 200:
           logging.info('Successfully updated checktray images count in Jango.')
           responsedata = response.json()
           totalCount = responsedata["total_count"]
           yesterdayCount = responsedata["yesterday_count"]
           #prepare Message body
           sendCheckTrayImageEmail(totalCount,yesterdayCount,responsedata['data'],str_date) 
           return data
        else:
           logging.error(f'Failed to update checktray images count in Jango. Status code: {response.status_code}')
           return None

    except Exception as e:
        logging.error('Error in update_check_tray_images_count function:', exc_info=True)
        return None

# Run the function
# if __name__ == '__main__':
#    update_check_tray_images_count()
