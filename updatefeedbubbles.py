from datetime import datetime, timedelta
import requests
import json
from google.cloud import firestore
import os
from google.cloud.firestore_v1 import FieldFilter
import apputils
import constants as cts
# Path to your service account key file
service_account_key_path = 'nextaqua-firestore-key.json'
# Set the environment variable to specify the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
# Initialize a client
db = firestore.Client.from_service_account_json(service_account_key_path)
jango_api_headers = {"Authorization":"Token e50f000f342fe8453e714454abac13be07f18ac3"}
bubblerunning_time = 20
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
def getBubbleId(reqDate):
    return apputils.get_epoch_time_pm(reqDate,pmtime=bubblerunning_time)
def fetchChecktrayDocument(siteId):
    # fetch checkTray Document
    docPath = f'checktraydata/{siteId}'
    checktray_doc = db.document(docPath).get()
    if not checktray_doc.exists:
        print(f'No such checktray document: {docPath}')
        return
    return checktray_doc.to_dict()

def getCurrentCropId(pondId,checktrayData):
    chkPonds = checktrayData.get('ponds',[])
    for chkPond in chkPonds:
        if str(chkPond.get('ax_pond_id', '')) == str(pondId):
           return chkPond.get('currentCrop','')
    return None;        

def sendBubbleMessage(siteId, messageData,reqDate):
    # Prepare bubble message
    bubbleId = getBubbleId(reqDate)
    destPath = f'nextfarm_data/{siteId}/allcrops/messages/data/{bubbleId}'
    try:
        if messageData:
           # Attempt to set the document
           db.document(destPath).set(messageData)
           print(f"bubble sent successfully...{destPath}")
           return True
        else:
           print(f"No bubble message to send...{destPath}")
           return False
    except Exception as e:
        # Handle any errors that occur
        print(f"An error occurred: {e}")
        return False
    
def sendAllBubblesToTestCollection(siteId, messageData,reqDate):
    # Prepare bubble message
    bubbleId = apputils.get_epoch_time_pm(reqDate,pmtime=bubblerunning_time)
    destPath = f'dayfeedtesting/alllsites/feedbubbles/{siteId}/data/{bubbleId}'
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
    return {}

#fill Manual, SmartScale, Aquabot
def fillOtherFeedSourcesData(siteId,tableData,chkDoc,reqDate):
    #fetch All Feed bubbles from smartscale
    feedCollectionPath = f"nextfarm_data/{siteId}/allcrops/messages/data"
    feedcollection_ref = db.collection(feedCollectionPath)
    day_start_epoch,day_end_epoch = apputils.get_day_start_end_epoch(reqDate)
    feedBubbles = feedcollection_ref.where(filter=FieldFilter("tableType", "==", "feedtable")) \
                                    .where(filter=FieldFilter("time", ">=", day_start_epoch)) \
                                    .where(filter=FieldFilter("time", "<=", day_end_epoch)).get()
    if len(feedBubbles)==0:
        print(f"No fillOtherFeedSourcesData for the day:{reqDate}")
        return tableData
    # print("identified buubles")
    # for feedBubble in feedBubbles:
    #     print(feedBubble.id)
    for feedbubble in feedBubbles:
        feedData = feedbubble.to_dict()
        dataFrom = None
        if "dataFrom" in feedData:
            dataFrom = feedData.get("dataFrom", None)
        feedtabledata = feedData.get("tabledata",[])
        for pondfeed in feedtabledata:
            mealdata = pondfeed.get("mealdata",{})
            ax_pond_id = pondfeed.get(cts.kax_pond_id,None)
            if ax_pond_id==None:
               ax_pond_id = str(pondfeed.get('id',''))
            ax_pond_id = str(ax_pond_id)
            meal = mealdata.get("meal",0)
            type = mealdata.get("type","")
            mealType = mealdata.get("mealType","")
            #get existing pond from tabledata
            ponddata = getPondDataFromTable(ax_pond_id,tableData)
            pondmeals = ponddata.get("meals",{})#it is map
            if len(pondmeals)==0:
               ponddata[cts.kmeals] = pondmeals
            
            feed_verified = None
            # type = type.lower()
            if dataFrom and dataFrom.lower()=="smartscale":
                type = dataFrom
                feed_verified = mealdata.get("feed_verified",None)
            meal = round(float(meal),2)
            type = type.lower()
            pondmeal = {
                "meal": meal,
                "dataFrom": type
            }
            if feed_verified: 
               pondmeal["feed_verified"] = feed_verified
            if type == "aquabot":
               pondmeal["weightToDisburse"] = mealdata.get("weightToDisburse",0)
            #get exact meal with meal number
            exitingMealsUnderMealType = pondmeals.get(mealType,[])
            if len(exitingMealsUnderMealType)==0:
               pondmeals[mealType] = [pondmeal]
            exitingMealsUnderMealType.append(pondmeal)
            print(f"MealType::{mealType}")           

            
            # if type == "manual" or type == "checktray" or type == "":
            #    manualfeed = ponddata.get(cts.kmanual_feed,0)
            #    manualfeed += meal
            #    ponddata[cts.kmanual_feed] = manualfeed
            #    pondmeal[cts.kdataFrom] = "manual"
            #    print(f"Pond::{ax_pond_id} manual data found::{manualfeed}")
            # elif type == "smartscale":
            #      smartscalefeed = ponddata.get(cts.ksmartscale_feed,0)
            #      #get verified feed
            #      feed_verified = mealdata.get("feed_verified",0)
            #      smartscalefeed += round(float(feed_verified),2)
            #      ponddata[cts.ksmartscale_feed] = smartscalefeed
            #      pondmeal[cts.kdataFrom] = "smartScale"
            #      print(f"smartscale data found::{smartscalefeed}")                
            # elif type == "aquabot": 
            #       aquabotfeed = ponddata.get(cts.kaquabot_feed,0)
            #       aquabotfeed += meal
            #       ponddata[cts.kaquabot_feed] = aquabotfeed
            #       pondmeal[cts.kdataFrom] = "aquabot"
            #       print(f"aquabot data found::{aquabotfeed}")
            # else:
            #     print(f"Unknown feed type: {type}")
    for pondData in tableData:
        pondmeals = pondData.get(cts.kmeals,{})
        smartscalefeed = 0
        aquabotfeed = 0
        manualfeed = 0
        for mealType,mealdata in pondmeals.items():
            mFeed = 0
            for meal in mealdata:
                dataFrom = meal.get(cts.kdataFrom,None)
                if dataFrom and dataFrom == "manual":
                   feed = meal.get("meal",0)
                   if mFeed<=0:
                      mFeed = round(float(feed),2)
                      manualfeed += round(float(feed),2)
                elif dataFrom and dataFrom == "smartscale":
                   feed_verified = meal.get("feed_verified",0)
                   smartscalefeed += round(float(feed_verified),2)
                   if mFeed<=0:
                      feed = meal.get("meal",0)
                      mFeed = round(float(feed),2)
                      manualfeed += round(float(feed),2)
                elif dataFrom and dataFrom == "aquabot":
                     feed = meal.get("weightToDisburse",0)
                     aquabotfeed += round(float(feed),2)
                   
        #collecting pond meal is completed
        pondData[cts.kmanual_feed] = manualfeed
        pondData[cts.ksmartscale_feed] = smartscalefeed
        pondData[cts.kaquabot_feed] = aquabotfeed

    return tableData


def fillStaticFeederData(siteId,tableData,chkDoc,iotdevices,reqDate):
    #fetch All Static feed data from Elasticsearch
    axSiteId = chkDoc.get('axfarmid',None)
    if axSiteId==None and len(iotdevices)>0:
       firstPond = iotdevices[0]
       axSiteId = firstPond.get('axsite_id',None)
    if axSiteId==None:
       return tableData   
    isToday = apputils.check_date_isToday(reqDate)
    docPath = f'wifi_af_ver03_feeder_data/{axSiteId}/info/livedata'
    feedDoc = None
    if isToday:
       feedDoc = db.document(docPath).get()
    else:
       docPath = f'wifi_af_ver03_feeder_data/{axSiteId}/history'
       day_start_epoch,day_end_epoch = apputils.get_day_start_end_epoch(reqDate,is13digit=False)
       query = (db.collection(docPath)
             .where(filter=FieldFilter("lut", ">=", day_start_epoch))
             .where(filter=FieldFilter("lut", "<=", day_end_epoch))
             .order_by("lut", direction=firestore.Query.DESCENDING)
             .limit(1))
       feedDocs = query.get()
       if feedDocs:
          feedDoc = feedDocs[0]
      
    if feedDoc==None:
       return tableData
    if feedDoc.exists==False:
       return tableData
    
    feedDocData = feedDoc.to_dict()
    af_calibration_data = feedDocData.get('af_calibration_data',{})
    for ponddevices in iotdevices:
        staticfeeders = ponddevices.get('feeder_device_ids',[])
        devicePondID = ponddevices.get('pond_id','')
        if len(staticfeeders) > 0:
           deviceId = staticfeeders[0]
           devicedata = af_calibration_data.get(deviceId,{})
           epoch = devicedata.get('lut',1000)
           isDateSame = True
           if isDateSame:
              for actPond in tableData:
                  if str(actPond[cts.kax_pond_id]) == str(devicePondID):
                      todayfeed = devicedata.get('todayFeed',0)
                      actPond[cts.kstaticfeeder_feed] = round(float(todayfeed),2)
                      meals = actPond.get(cts.kmeals,{})
                      if len(meals) == 0:
                          actPond[cts.kmeals] = meals
                      meals["NM"] = [{
                            cts.kmeal: todayfeed,
                            cts.kdataFrom: cts.kstaticfeeder,
                            "deviceid": deviceId
                        }]
                      break

    return tableData

def insertStaticFeederFeedData(siteId,tableData,chkDoc,reqDate):
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
       fillStaticFeederData(siteId,tableData,chkDoc,iotdevices,reqDate)  # deviceId and pondid will be fetched from the IoT devices data.
    

    return tableData
def fillFinalFeed(tableData):
    for pondmeal in tableData:
        feed_smartscale = 0
        if cts.ksmartscale_feed in pondmeal:
            feed_smartscale = pondmeal[cts.ksmartscale_feed]
        feed_aquabot = 0
        if cts.kaquabot_feed in pondmeal:
            feed_aquabot = pondmeal[cts.kaquabot_feed]
        feed_staticfeeder = 0
        if cts.kstaticfeeder_feed in pondmeal:
            feed_staticfeeder = pondmeal[cts.kstaticfeeder_feed]
        manualfeed = 0
        if cts.kmanual_feed in pondmeal:
           manualfeed = pondmeal[cts.kmanual_feed]

        if feed_smartscale>0:
           pondmeal[cts.kfinal_feed] = feed_smartscale
        elif feed_staticfeeder>0:
            pondmeal[cts.kfinal_feed] = feed_staticfeeder
        elif feed_aquabot>0:
            pondmeal[cts.kfinal_feed] = feed_aquabot
        else:
            pondmeal[cts.kfinal_feed] = manualfeed

    return tableData

def prepareBubble(siteId,tableData,chkDocData,reqDate):
    if len(tableData) > 0:
        tabledata = fillOtherFeedSourcesData(siteId,tableData,chkDocData,reqDate)
        tabledata = insertStaticFeederFeedData(siteId,tableData,chkDocData,reqDate)
        #fillFinal Feed
        tabledata=fillFinalFeed(tableData)
        return {
            "tableType": apputils.TableTypes.DAY_FEED_TABLE.value,
            "tabledata": tabledata,
            "sentTime": apputils.get_today_date_time_in_ist(),
            "id": getBubbleId(reqDate),
            "time": getBubbleId(reqDate),
            "timeStamp": apputils.get_epoch_time_for_date_with_current_time(reqDate),
            "uid": str(apputils.get_epoch_time_for_date_with_current_time(reqDate)),
            "senderName": "Aquaexchange"
        }
    else:
        print(f'Not able to prepare feed data for: {siteId}')
        return None
def notifyFeedBubbleForSite(siteId,reqDate=None,isTestRun=False):
    #get Feed bubble for today, read it from feed collection
    try:
        if reqDate==None:
           #get today date
           reqDate = apputils.get_today_date_string()
        #check if reqDate is correct date or not
        isavlidDate = apputils.validate_date_format(reqDate)
        if isavlidDate == False:
           print(f'Invalid date format: {reqDate}')
           return f"failed to send feed data for site: {siteId} ,Invalid date format: {reqDate}"

        chkDoc = fetchChecktrayDocument(siteId)
        #prepare table here for current crop
        tabledata = []
        if chkDoc:
           tabledata = prepareTablePondsMetaData(chkDoc)
           if len(tabledata)==0:
              print(f"failed to prepare feed data for site: {siteId}, No data found in checktray document")
              return False
           bubbleData = prepareBubble(siteId,tabledata,chkDoc,reqDate)
           if isTestRun:
              sendAllBubblesToTestCollection(siteId,bubbleData,reqDate)
           else:
              sendBubbleMessage(siteId,bubbleData,reqDate)
           
    except Exception as e:
           print(f'Error occurred while fetching feed data for site: {siteId}, Error: {str(e)}')
           return f"failed to send feed data for site: {siteId}"
    return f"success in sending feed data for site: {siteId}"

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
#getFeedBubble("SAF308232051")
#getFeedBubble("19A1908249824FY24C3")
#getFeedBubble("TES1908246363FY24C3")
#test for few sites
#sites = ["AXC2507247563A24","AXC2507244576A24","DSE2007242348A24","ESE2007245662A24"]
#sites = ["2802708248509FY24C1"]
# sites = ["ESE2007243752A24"]
# for site in sites:
#     notifyFeedBubbleForSite(site,'29-08-2024')
