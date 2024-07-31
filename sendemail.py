import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(subject, body, to_emails, cc_emails=None, from_email=None, appPassword=None, attachment_name=None, attachment_data=None, attachment_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'):
    # Create the multipart message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ", ".join(to_emails)  # Join the list of emails into a single string

    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)  # Join the list of CC emails into a single string
        to_emails += cc_emails  # Include CC emails in the recipients list

    msg['Subject'] = subject

    # Attach the body with the msg instance
    msg.attach(MIMEText(body, 'html'))

    # Attach the file
    if attachment_data and attachment_name:
        part = MIMEBase(attachment_type.split('/')[0], attachment_type.split('/')[1])
        part.set_payload(attachment_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={attachment_name}')
        msg.attach(part)

    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, appPassword)
        text = msg.as_string()
        server.sendmail(from_email, to_emails, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Example usage
# send_email(
#     subject="Test Email with Attachment",
#     body="This is a test email with an attachment.",
#     to_emails=["recipient1@example.com"],
#     cc_emails=["cc_recipient@example.com"],
#     from_email="your_email@example.com",
#     appPassword="your_app_password",
#     attachment_name="test_attachment.xlsx",
#     attachment_data=open("path/to/your/attachment.xlsx", "rb").read()
# )
