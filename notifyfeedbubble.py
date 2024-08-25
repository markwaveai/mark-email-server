from datetime import datetime, timedelta
import requests
import logging
import json
from google.cloud import firestore
import os
from google.cloud.firestore_v1 import FieldFilter
import utils
# Path to your service account key file
service_account_key_path = 'nextaqua-firestore-key.json'
# Set the environment variable to specify the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
# Initialize a client
db = firestore.Client.from_service_account_json(service_account_key_path)
# def send_fcm_notification(token, title, body):
#     # Function to send FCM notification
#     url = "https://fcm.googleapis.com/fcm/send"
#     headers = {
#         'Authorization': f'key={fcm_server_key}',
#         'Content-Type': 'application/json'
#     }
#     payload = {
#         "to": token,
#         "notification": {
#             "title": title,
#             "body": body,
#             "sound": "default"
#         },
#         "data": {
#             "extra_information": "Some extra information"  # Custom data if needed
#         }
#     }
    
#     try:
#         response = requests.post(url, headers=headers, data=json.dumps(payload))
#         response.raise_for_status()  # Raise an error for bad responses
#         print(f"FCM notification sent successfully: {response.status_code}")
#     except requests.exceptions.RequestException as e:
#         print(f"Failed to send FCM notification: {e}")
def fetchChecktrayDocument(siteId):
    # fetch checkTray Document
    docPath = f'checktraydata/{siteId}'
    checktray_doc = db.document(docPath).get()
    if not checktray_doc.exists:
        logging.error(f'No such checktray document: {docPath}')
        return
    return checktray_doc.to_dict()
def getCurrentCropId(pondId,checktrayData):
    chkPonds = checktrayData.get('ponds',[])
    for chkPond in chkPonds:
        if str(chkPond.get('ax_pond_id', '')) == str(pondId):
           return chkPond.get('currentCrop','')
    return '';        

def sendBubbleMessage(siteId, messageData):
    # Prepare bubble message
    bubbleId = utils.get_epoch_time_7pm()
    destPath = f'nextfarm_data/{siteId}/allcrops/messages/data/{bubbleId}'
    try:
        # Attempt to set the document
        db.document(destPath).set(messageData)
        print(f"bubble sent successfully...{destPath}")
        return True
    except Exception as e:
        # Handle any errors that occur
        print(f"An error occurred: {e}")
        return False

def prepareTableData(docData,chkData):
    # Prepare table data
    tableData = docData.get('tabledata', [])
    for pondData in tableData:
        pondid = pondData.get('id', None)
        pondData["ax_pond_id"] = pondid
        pondData["crop_id"] = getCurrentCropId(pondid,chkData)
    return tableData

def prepareBubble(doc,siteId):
    if doc.exists:
        data = doc.to_dict()
        timeStamp = data.get('time', None)
        print("Feed bubble identified Date: " + utils.get_date_time_ist(timeStamp))
        chkData = fetchChecktrayDocument(siteId)
        tabledata = prepareTableData(data,chkData)
        return {
            "tableType": utils.TableTypes.DAY_FEED_TABLE.value,
            "tabledata": tabledata,
            "sentTime": utils.get_today_date_time_in_ist(),
            "time": utils.get_epoch_time(),
            "timeStamp": utils.get_epoch_time(),
            "uid": str(utils.get_epoch_time()),
            "senderName": "server"
        }
    else:
        logging.error(f'No such document: {doc.id}')
        return None


def getFeedBubble(siteId):
    #get Feed bubble for today, read it from feed collection
    feedCollectionPath = f"nextfarm_feed/{siteId}/allcrops/messages/data"
    feedcollection_ref = db.collection(feedCollectionPath)
    day_start_epoch,day_end_epoch = utils.get_day_start_end_epoch_in_ist(utils.get_today_date_string_in_ist())
    query = feedcollection_ref.where(filter=FieldFilter("time", ">=", day_start_epoch)) \
                              .where(filter=FieldFilter("time", "<=", day_end_epoch)) \
                              .order_by("time", direction=firestore.Query.DESCENDING).limit(1)
    docs = query.get()
    for doc in docs:
        print(f'Document ID: {doc.id}')
        bubbledata = prepareBubble(doc,siteId)
        if bubbledata:
           sendBubbleMessage(siteId, bubbledata)
        else:
            logging.error(f'No bubble found for site: {siteId}')
            return None
    
    
#getFeedBubble("TES1908246363FY24C3")

