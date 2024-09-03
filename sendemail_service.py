from flask import Flask, request, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

app = Flask(__name__)

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
        part.set_payload(base64.b64decode(attachment_data))
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
        return "Email sent successfully", True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return f"Failed to send email: {e}", False

@app.route('/send_email', methods=['POST'])
def api_send_email():
    data = request.json
    subject = data.get('subject')
    body = data.get('body')
    to_emails = data.get('to_emails')
    cc_emails = data.get('cc_emails', [])
    from_email = data.get('from_email')
    appPassword = data.get('appPassword')
    attachment_name = data.get('attachment_name')
    attachment_data = data.get('attachment_data')  # Base64 encoded string
    attachment_type = data.get('attachment_type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    result = send_email(subject, body, to_emails, cc_emails, from_email, appPassword, attachment_name, attachment_data, attachment_type)
    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(debug=True)
