import base64
import os
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

# Assuming these modules exist in the path
import sendemail_service

# Load environment variables
load_dotenv()

app = FastAPI()

# Setup templates
templates = Jinja2Templates(directory="templates")

# Pydantic models for request bodies
class EmailRequest(BaseModel):
    subject: str = "***subject***"
    msgbody: str = "***subject***" 
    to_emails: Optional[List[str]] = None
    cc_emails: Optional[List[str]] = None
    from_email: Optional[str] = None
    app_password: Optional[str] = None
    attachment_name: Optional[str] = None
    attachment_data: Optional[str] = None
    attachment_mime_type: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send_checktrayCount_email")
async def send_checktrayCount_email(request: Request):
    try:
        reqdata = await request.json()
    except Exception:
        return JSONResponse(content={"error": "Request body must be JSON"}, status_code=400)
    
    # We assume fetch_yesterday_count works as imported
    response_data = fetch_yesterday_count.sendCheckTrayEmailWithTarget(reqdata)
    return JSONResponse(content={"message": response_data}, status_code=200)

@app.post("/send_email_by_subject_body_attachment")
async def send_email(reqdata: EmailRequest):
    try:
        subject = reqdata.subject
        msgbody = reqdata.msgbody
        to_emails = reqdata.to_emails
        cc_emails = reqdata.cc_emails
        
        # Logic from original
        from_email = os.getenv('emailaccount')
        app_password = os.getenv('app_password')
        
        attachment_name = reqdata.attachment_name
        attachment_data = reqdata.attachment_data
        attachment_mime_type = reqdata.attachment_mime_type

        response, isSent = sendemail_service.send_email(
            subject, msgbody, to_emails, cc_emails, 
            from_email=from_email, appPassword=app_password,
            attachment_name=attachment_name, 
            attachment_data=attachment_data, 
            attachment_type=attachment_mime_type
        )
        
        if isSent:
           return JSONResponse(content={"message": response}, status_code=200)
        else:
           return JSONResponse(content={"error": response}, status_code=500)
    except Exception:
        # Generic error fallback
        return JSONResponse(content={"error": "Error sending email"}, status_code=500)

@app.post("/send_email_by_formdata")
async def send_email_by_formdata(
    subject: str = Form("***subject***"),
    msgbody: str = Form("***msgbody***"),
    to_emails: List[str] = Form(default=[]), 
    cc_emails: List[str] = Form(default=[]),
    attachment: Optional[UploadFile] = File(None)
):
    try:
        from_email = os.getenv('emailaccount')
        app_password = os.getenv('app_password')
        
        attachment_name = None
        attachment_data = None
        attachment_mime_type = None

        if attachment:
            attachment_name = attachment.filename
            content = await attachment.read()
            attachment_data = base64.b64encode(content).decode('utf-8')
            attachment_mime_type = attachment.content_type

        response, isSent = sendemail_service.send_email(
            subject, msgbody, to_emails, cc_emails, 
            from_email=from_email, appPassword=app_password,
            attachment_name=attachment_name, 
            attachment_data=attachment_data, 
            attachment_type=attachment_mime_type
        )

        if isSent:
            return JSONResponse(content={"message": response}, status_code=200)
        else:
            return JSONResponse(content={"error": response}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"Error sending email: {str(e)}"}, status_code=500)

@app.post("/send_email_by_multiple_attachments")
async def send_email_by_multiple_attachments(request: Request):
    try:
        # Access form data directly to handle arbitrary file keys and lists
        form = await request.form()
        
        subject = form.get('subject', "***subject***")
        msgbody = form.get('msgbody', "***msgbody***")
        to_emails = form.getlist('to_emails')
        cc_emails = form.getlist('cc_emails')
        
        from_email = os.getenv('emailaccount')
        app_password = os.getenv('app_password')
        
        attachments = []
        for key, value in form.items():
            if isinstance(value, UploadFile):
                attachment = value
                if attachment.filename:
                    content = await attachment.read()
                    attachments.append({
                        'name': attachment.filename,
                        'data': base64.b64encode(content).decode('utf-8'),
                        'type': attachment.content_type or 'application/octet-stream'
                    })
        
        response, isSent = sendemail_service.send_email_with_attachments(
            subject, msgbody, to_emails, cc_emails, 
            from_email=from_email, appPassword=app_password,
            attachments=attachments if attachments else None
        )

        if isSent:
            return JSONResponse(content={"message": response}, status_code=200)
        else:
            return JSONResponse(content={"error": response}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"error": f"Error sending email: {str(e)}"}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5000)
