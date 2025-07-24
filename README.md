# CheckTrayEmailServer

A Flask-based email server with draft email functionality.

## Features

- Send emails with attachments
- Create, update, and manage email drafts
- Send emails from saved drafts
- API endpoints for email operations

## Draft Email API

The Draft Email API allows you to create, manage, and send email drafts.

### API Endpoints

#### Create a Draft

```
POST /api/drafts
```

Request body:
```json
{
  "subject": "Email Subject",
  "body": "Email body content (supports HTML)",
  "to_emails": ["recipient@example.com"],
  "cc_emails": ["cc@example.com"],
  "attachment_name": "filename.xlsx",
  "attachment_data": "base64_encoded_data",
  "attachment_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

Response:
```json
{
  "message": "Draft created successfully",
  "draft_id": "uuid-string"
}
```

#### Get a Draft

```
GET /api/drafts/{draft_id}
```

Response:
```json
{
  "id": "uuid-string",
  "created_at": "ISO datetime",
  "updated_at": "ISO datetime",
  "subject": "Email Subject",
  "body": "Email body content",
  "to_emails": ["recipient@example.com"],
  "cc_emails": ["cc@example.com"],
  "attachment_name": "filename.xlsx",
  "attachment_data": "base64_encoded_data",
  "attachment_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
}
```

#### List All Drafts

```
GET /api/drafts
```

Response:
```json
{
  "drafts": [
    {
      "id": "uuid-string",
      "subject": "Email Subject",
      "created_at": "ISO datetime",
      "updated_at": "ISO datetime",
      "to_emails": ["recipient@example.com"]
    },
    ...
  ]
}
```

#### Update a Draft

```
PUT /api/drafts/{draft_id}
```

Request body:
```json
{
  "subject": "Updated Subject",
  "body": "Updated body content",
  "to_emails": ["new_recipient@example.com"],
  "cc_emails": ["new_cc@example.com"]
}
```

Response:
```json
{
  "message": "Draft updated successfully",
  "draft_id": "uuid-string"
}
```

#### Delete a Draft

```
DELETE /api/drafts/{draft_id}
```

Response:
```json
{
  "message": "Draft deleted successfully"
}
```

#### Send a Draft

```
POST /api/drafts/{draft_id}/send
```

Response:
```json
{
  "message": "Email sent successfully",
  "draft_id": "uuid-string"
}
```

## Setup

1. Create a `.env` file with your email credentials:
```
emailaccount=your_email@gmail.com
app_password=your_app_password
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the server:
```
python main.py
```

The server will start on http://localhost:5000
