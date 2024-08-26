from datetime import datetime, timedelta
import requests
import logging
import json
from google.cloud import firestore
import os
from google.cloud.firestore_v1 import FieldFilter
import utils
import constants as cts
# Path to your service account key file
service_account_key_path = 'nextaqua-firestore-key.json'
# Set the environment variable to specify the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
# Initialize a client
db = firestore.Client.from_service_account_json(service_account_key_path)
jango_api_headers = {"Authorization":"Token e50f000f342fe8453e714454abac13be07f18ac3"}

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
def fetch_iot_devices(siteId):
    response = requests.get(f'https://app.aquaexchange.com/api/farmer/fetchdevices/?next_farm_section_id={siteId}',headers=jango_api_headers)
    if response.status_code == 200:
       try:
             data = response.json()
             return data
       except json.JSONDecodeError:
             print("Error decoding JSON response:---",siteId) 

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
    return None;        

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
def fetchCurrentCrop(pond):
    crops = pond.get('crops',[])
    currentCropId = pond.get('currentCrop',None)
    if crops:
       for crop in crops:
           if crop['id'] == currentCropId:
              return crop
    return None

def prepareTablePondsMetaData(chkData):
    # Prepare table data
    tableData = []
    ponds = chkData.get('ponds',[])
    for pond in ponds:
        currentCrop = fetchCurrentCrop(pond)
        if currentCrop and currentCrop.get('isActive',False):
           tableData.append({
                cts.kax_pond_id: pond.get(cts.kax_pond_id, ''),
                "name": pond.get('pond_name', ''),
                cts.kcrop_id: currentCrop.get('id','')
            })
        else:
            print(f"No current crop found for pond: {pond.get('ax_pond_id', '')}")
        
    return tableData
def getPondDataFromTable(pondid,tableData):
    for pond in tableData:
        if str(pond.get(cts.kax_pond_id, '')) == str(pondid):
           return pond
    return None

#fill Manual, SmartScale, Aquabot
def fillOtherFeedSourcesData(siteId,tableData,chkDoc):
    #fetch All Feed bubbles from smartscale
    feedCollectionPath = f"nextfarm_data/{siteId}/allcrops/messages/data"
    feedcollection_ref = db.collection(feedCollectionPath)
    day_start_epoch,day_end_epoch = utils.get_day_start_end_epoch_in_ist(utils.get_today_date_string_in_ist())
    feedBubbles = feedcollection_ref.where(filter=FieldFilter("tableType", "==", "feedtable")) \
                                    .where(filter=FieldFilter("time", ">=", day_start_epoch)) \
                                    .where(filter=FieldFilter("time", "<=", day_end_epoch)).get()
    for feedbubble in feedBubbles:
        feedData = feedbubble.to_dict()
        feedtabledata = feedData.get("tabledata",[])
        for pondfeed in feedtabledata:
            mealdata = pondfeed.get("mealdata",{})
            ax_pond_id = str(pondfeed.get(cts.kax_pond_id,""))
            meal = mealdata.get("meal",0)
            type = mealdata.get("type","")
            mealType = mealdata.get("mealType","")
            #get existing pond from tabledata
            ponddata = getPondDataFromTable(ax_pond_id,tableData)
            pondmeals = ponddata.get("meals",[])
            pondmeal = {
                "meal": meal,
                "mealType": mealType,
            }
            if len(pondmeals)==0:
               ponddata[cts.kmeals] = pondmeals
              
            if type.lower() == "manual" or type.lower() == "checktray":
               manualfeed = ponddata.get(cts.kmanual_feed,0)
               manualfeed += meal
               ponddata[cts.kmanual_feed] = manualfeed
               pondmeal[cts.kdataFrom] = "manual"
               print("manual data found")
            elif type.lower() == "smartscale":
                 smartscalefeed = ponddata.get(cts.ksmartscale_feed,0)
                 smartscalefeed += meal
                 ponddata[cts.ksmartscale_feed] = smartscalefeed
                 pondmeal[cts.kdataFrom] = "smartScale"
                 print("smartscale data found")                
            elif type.lower() == "aquabot": 
                  aquabotfeed = ponddata.get(cts.kaquabot_feed,0)
                  aquabotfeed += meal
                  ponddata[cts.kaquabot_feed] = smartscalefeed
                  pondmeal[cts.kdataFrom] = "aquabot"
                  print("aquabot data found")
            else:
                print(f"Unknown feed type: {type}")
                
            

        

    return tableData


def fillStaticFeederData(siteId,tableData,chkDoc,iotdevices):
    #fetch All Static feed data from Elasticsearch
    axSiteId = chkDoc.get('axfarmid',None)
    if axSiteId==None and len(iotdevices)>0:
       firstPond = iotdevices[0]
       axSiteId = firstPond.get('axsite_id',None)
    if axSiteId==None:
       return tableData   
    docPath = f'wifi_af_ver03_feeder_data/{axSiteId}/info/livedata'
    feedDoc = db.document(docPath).get()
    if feedDoc.exists==False:
       return tableData
    feedDocData = feedDoc.to_dict()
    af_calibration_data = feedDocData.get('af_calibration_data',{})
    for ponddevices in iotdevices:
        staticfeeders = ponddevices.get('feeder_device_ids',[])
        devicePondID = ponddevices.get('pond_id','')
        if len(staticfeeders)>0:
           deviceId = staticfeeders[0]
           devicedata = af_calibration_data.get(deviceId,{})
           epoch = devicedata.get('lut',1000)
           isToday = utils.check_epoch_isToday(epoch)
           if isToday:
              for actPond in tableData:
                  if str(actPond[cts.kax_pond_id]) == str(devicePondID):
                      todayfeed = devicedata.get('todayFeed',0)
                      actPond[cts.kstaticfeeder_feed] = todayfeed
                      meals = actPond.get(cts.kmeals,[])
                      if len(meals) == 0:
                          actPond[cts.kmeals] = meals
                      meals.append({
                            cts.kmeal: todayfeed,
                            cts.kmealType: "",
                            cts.kdataFrom: cts.kstaticfeeder
                        })
                      break

    return tableData

def insertFeedData(siteId,tableData,chkDoc):
    fillOtherFeedSourcesData(siteId,tableData,chkDoc)
    iotdevices = fetch_iot_devices(siteId)
    #smartScalesInSiteIdentified = False
    statisFeederIdentified = False
    for ponddevices in iotdevices:
        # smartscales = ponddevices.get('smart_scale_device_ids',[])
        # if len(smartscales)>0:
        #    smartScalesInSiteIdentified = True
        staticfeeders = ponddevices.get('feeder_device_ids',[])
        if len(staticfeeders)==1:
           statisFeederIdentified = True
           
    # if smartScalesInSiteIdentified:
    #    fillSmartScaleData(siteId,tableData) 
    if statisFeederIdentified:
       fillStaticFeederData(siteId,tableData,chkDoc,iotdevices)  # deviceId and pondid will be fetched from the IoT devices data.
    

    return tableData
def prepareBubble(siteId,tableData,chkDocData):
    if len(tableData) > 0:
        tabledata = insertFeedData(siteId,tableData,chkDocData)
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
        logging.error(f'Not able to prepare feed data for: {siteId}')
        return None
def getFeedBubble(siteId):
    #get Feed bubble for today, read it from feed collection
    chkDoc = fetchChecktrayDocument(siteId)
    #prepare table here for current crop
    tabledata = []
    if chkDoc:
       tabledata = prepareTablePondsMetaData(chkDoc)
       bubbleData = prepareBubble(siteId,tabledata,chkDoc)
       sendBubbleMessage(siteId,bubbleData)

# def getFeedBubble(siteId):
#     #get Feed bubble for today, read it from feed collection
#     feedCollectionPath = f"nextfarm_feed/{siteId}/allcrops/messages/data"
#     feedcollection_ref = db.collection(feedCollectionPath)
#     day_start_epoch,day_end_epoch = utils.get_day_start_end_epoch_in_ist(utils.get_today_date_string_in_ist())
#     query = feedcollection_ref.where(filter=FieldFilter("time", ">=", day_start_epoch)) \
#                               .where(filter=FieldFilter("time", "<=", day_end_epoch)) \
#                               .order_by("time", direction=firestore.Query.DESCENDING).limit(1)
#     docs = query.get()
#     for doc in docs:
#         print(f'Document ID: {doc.id}')
#         bubbledata = prepareBubble(doc,siteId)
#         if bubbledata:
#            sendBubbleMessage(siteId, bubbledata)
#         else:
#             logging.error(f'No bubble found for site: {siteId}')
#             return None
#SAF308232051
#Test case one ESE2007245662A24
getFeedBubble("SAF308232051")
#getFeedBubble("TES1908246363FY24C3")

