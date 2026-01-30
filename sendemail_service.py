import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def send_email_with_attachments(subject, body, to_emails, cc_emails=None, from_email=None, appPassword=None, attachments=None, attachment_name=None, attachment_data=None, attachment_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
    # Create the multipart message
    msg = MIMEMultipart()
    
    # Use environment variables if not provided
    if not from_email:
        from_email = os.getenv('emailaccount')
    if not appPassword:
        appPassword = os.getenv('app_password')
        
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails) if to_emails else ""

    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)
        to_emails = (to_emails or []) + cc_emails

    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'html'))

    # Handle multiple attachments if provided
    if attachments and isinstance(attachments, list):
        for attachment in attachments:
            if attachment.get('data') and attachment.get('name'):
                # Basic MIME type handling
                mime_type = attachment.get('type', 'application/octet-stream')
                if '/' in mime_type:
                    main_type, sub_type = mime_type.split('/', 1)
                else:
                    main_type, sub_type = 'application', 'octet-stream'
                
                part = MIMEBase(main_type, sub_type)
                part.set_payload(base64.b64decode(attachment.get('data')))
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={attachment.get("name")}')
                msg.attach(part)
    # Handle single attachment (legacy support)
    elif attachment_data and attachment_name:
        mime_type = attachment_type
        if '/' in mime_type:
            main_type, sub_type = mime_type.split('/', 1)
        else:
             main_type, sub_type = 'application', 'octet-stream'

        part = MIMEBase(main_type, sub_type)
        part.set_payload(base64.b64decode(attachment_data))
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={attachment_name}')
        msg.attach(part)

    # Send the email
    try:
        if not from_email or not appPassword:
             return "Missing email credentials", False

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, appPassword)
        text = msg.as_string()
        server.sendmail(from_email, to_emails, text)
        server.quit()
        print("Email sent successfully")
        return "Email sent successfully", True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return f"Failed to send email: {e}", False

def send_email(subject, body, to_emails, cc_emails=None, from_email=None, appPassword=None, attachment_name=None, attachment_data=None, attachment_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
    return send_email_with_attachments(
        subject, body, to_emails, cc_emails, from_email, appPassword, 
        attachments=None, 
        attachment_name=attachment_name, 
        attachment_data=attachment_data, 
        attachment_type=attachment_type
    )
