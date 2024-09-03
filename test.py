from datetime import datetime, timedelta
import requests
import json
from google.cloud import firestore
import os
from google.cloud.firestore_v1 import FieldFilter
import apputils
import constants as cts
import updatefeedbubbles as dayfeedbubbles
# Path to your service account key file
service_account_key_path = 'nextaqua-firestore-key.json'
# Set the environment variable to specify the service account key file
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = service_account_key_path
# Initialize a client
db = firestore.Client.from_service_account_json(service_account_key_path)
# The JSON string you provided
# json_data = '''
# {
#   "uid": "",
#   "senderName": "AquaExchange",
#   "tableType": "dayfeedtable",
#   "tabledata": [
#     {
#         "crop_id": "",
#         "name": "",
#         "ax_pond_id": "",
#         "id": "",
#         "manual_feed": 0,
#         "smartscale_feed": 0,
#         "staticfeeder_feed": 0,
#         "aquabot_feed": 0,
#         "final_feed": 0,
#         "meals": {
#             "M1": [
#                 {
#                     "meal": 0,
#                     "verified_feed": 0,
#                     "dataFrom": "smartScale"
#                 },
#                 {
#                     "meal": 0,
#                     "dataFrom": "manual"
#                 },
#                 {
#                     "wie": 0,
#                     "weightToDisburse": 0,
#                     "dataFrom": "aquabot"
#                 }
#             ],
#             "NM": [
#                 {
#                     "meal": 0,
#                     "dataFrom": "staticfeeder"
#                 }
#             ]
#         }
#     }
#   ]
# }
# '''

# # Parse the JSON string into a Python dictionary
# parsed_data = json.loads(json_data)

# # Accessing elements within the parsed data
# print("UID:", parsed_data["uid"])
# print("Sender Name:", parsed_data["senderName"])
# print("Table Type:", parsed_data["tableType"])

# # Example: Accessing the first pond's data
# first_pond = parsed_data["tabledata"][0]
# print("First Pond ID:", first_pond["id"])
# print("First Pond Name:", first_pond["name"])

# # Example: Accessing meals for the first pond
# meals = first_pond["meals"]
# print("Meals in M1:", meals["M1"])
# meals.get("M1",[])

def testDayFeedAllSites():
    checktray_docs = (db.collection("checktraydata").where(filter=FieldFilter("isRealSite", "==", True)).get())
    for doc in checktray_docs:
        dayfeedbubbles.notifyFeedBubbleForSite(doc.id,isTestRun=False)
def testCOEFeedAllSites():
    sites = ["AXC2507247563A24","AXC2507244576A24","DSE2007242348A24","ESE2007245662A24","AXC2507249675A24","ESE2007243752A24"]
    #sites = ["ESE2007243752A24"]
    for site in sites:
        dayfeedbubbles.notifyFeedBubbleForSite(site,isTestRun=False)
