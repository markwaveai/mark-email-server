from flask import Flask, jsonify, render_template, request
import fetch_yesterday_count
import sendemail_service as sendemail_service
#import updatefeedbubbles

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_checktrayCount_email', methods=['POST'])
def send_checktrayCount_email():
    if not request.is_json:
        return jsonify({"error": "Request body must be JSON"}), 400
    
    reqdata = request.get_json()
    
    response_data = fetch_yesterday_count.update_check_tray_images_count(reqdata)
    return jsonify({"message": response_data}),200
@app.route('/send_email_by_subject_body_attachment', methods=['POST'])
def send_email():
    try:
        if not request.is_json:
            return jsonify({"error": "Request body must be JSON"}), 400
        
        reqdata = request.get_json()
        subject = reqdata.get('subject',"***subject***")
        msgbody = reqdata.get('msgbody',"***subject***")
        to_emails = reqdata.get('to_emails',None)
        cc_emails = reqdata.get('cc_emails',None)
        from_email = reqdata.get('from_email','developer@nextaqua.in')
        app_password = reqdata.get('app_password','zdkc wler hovo jclu')
        attachment_name=reqdata.get('attachment_name',None)
        attachment_data=reqdata.get('attachment_data',None)
        attachment_mime_type=reqdata.get('attachment_mime_type',None)
        response,isSent=sendemail_service.send_email(subject,msgbody,to_emails,cc_emails,from_email=from_email,appPassword=app_password,
                                    attachment_name=attachment_name,attachment_data=attachment_data,attachment_type=attachment_mime_type)
        if isSent:
           return jsonify({"message": response}),200
        else:
           return jsonify({"error": response}),500
    except Exception:
            return jsonify({"error": "Error sending email"}), 500
    

# @app.route('/notify_day_feed_bubble', methods=['POST'])
# def notifyDayFeedBubble():
#     print("calling...notifyDayFeedBubble")
#     if not request.is_json:
#         return jsonify({"error": "Request body must be JSON"}), 400
#     reqdata = request.get_json()
#     response = {}
#     for site in reqdata:
#         result = updatefeedbubbles.notifyFeedBubbleForSite(site)
#         response[site] = result
#     return jsonify(response),200

if __name__ == '__main__':
    app.run(debug=True)
