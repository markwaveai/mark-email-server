import base64
import os
import json
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Assuming these modules exist in the path
import sendemail_service
# import fetch_yesterday_count # Module appears to be missing

# Load environment variables
load_dotenv()
app = FastAPI(
    title="Email Service API",
    description="API for sending emails with various configurations including attachments, form data, and HTML bodies.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Pydantic models for request bodies
class EmailRequest(BaseModel):
    subject: str = Field(default="***subject***", description="Subject of the email")
    msgbody: str = Field(default="***subject***", description="HTML body content of the email")
    to_emails: Optional[List[str]] = Field(default=None, description="List of recipient email addresses")
    cc_emails: Optional[List[str]] = Field(default=None, description="List of CC email addresses")
    from_email: Optional[str] = Field(default=None, description="Sender email address (overrides env var if provided)")
    app_password: Optional[str] = Field(default=None, description="App password for sender (overrides env var if provided)")
    attachment_name: Optional[str] = Field(default=None, description="Name of the attachment file")
    attachment_data: Optional[str] = Field(default=None, description="Base64 encoded content of the attachment")
    attachment_mime_type: Optional[str] = Field(default=None, description="MIME type of the attachment")

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def index(request: Request):
    """
    Serves the main HTML page for the Email Service.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send_checktrayCount_email", tags=["Specialized"])
async def send_checktrayCount_email(request: Request):
    """
    Endpoint to send check tray count emails.
    
    **Note**: This endpoint currently relies on a missing module `fetch_yesterday_count` and will return an error or mock response.
    """
    try:
        reqdata = await request.json()
    except Exception:
        return JSONResponse(content={"error": "Request body must be JSON"}, status_code=400)
    
    # We assume fetch_yesterday_count works as imported
    # response_data = fetch_yesterday_count.sendCheckTrayEmailWithTarget(reqdata)
    response_data = "Functionality unavailable: fetch_yesterday_count module missing."
    return JSONResponse(content={"message": response_data}, status_code=200)

@app.post("/send_email_by_subject_body_attachment", tags=["Email"], response_model=Dict[str, Any])
async def send_email(reqdata: EmailRequest):
    """
    Send an email with a subject, HTML body, and an optional single attachment via JSON payload.
    """
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

@app.post("/send_email_by_formdata", tags=["Email"])
async def send_email_by_formdata(
    subject: str = Form(default="***subject***", description="Email subject"),
    msgbody: str = Form(default="***msgbody***", description="Email HTML body"),
    to_emails: List[str] = Form(default=[], description="List of recipient emails"), 
    cc_emails: List[str] = Form(default=[], description="List of CC emails"),
    attachment: Optional[UploadFile] = File(None, description="Optional file attachment")
):
    """
    Send an email using standard Form Data, supporting file upload.
    """
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

@app.post("/send_email_by_multiple_attachments", tags=["Email"])
async def send_email_by_multiple_attachments(request: Request):
    """
    Send an email with multiple attachments.
    
    **Note**: Accepts arbitrary form fields for file uploads. Each file field in the form data will be treated as an attachment.
    Standard fields: `subject`, `msgbody`, `to_emails`, `cc_emails`.
    """
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
