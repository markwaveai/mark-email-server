# import os
# import json
# import uuid
# from datetime import datetime
# from flask import Blueprint, request, jsonify

# # Create a Blueprint for the draft email API
# draft_email_bp = Blueprint('draft_email', __name__)

# # Directory to store draft emails
# DRAFTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'email_drafts')

# # Ensure the drafts directory exists
# if not os.path.exists(DRAFTS_DIR):
#     os.makedirs(DRAFTS_DIR)

# def get_draft_path(draft_id):
#     """Get the file path for a draft email."""
#     return os.path.join(DRAFTS_DIR, f"{draft_id}.json")

# @draft_email_bp.route('/drafts', methods=['POST'])
# def create_draft():
#     """Create a new email draft."""
#     try:
#         if not request.is_json:
#             return jsonify({"error": "Request body must be JSON"}), 400
        
#         data = request.get_json()
        
#         # Generate a unique ID for the draft
#         draft_id = str(uuid.uuid4())
        
#         # Create draft object with metadata
#         draft = {
#             "id": draft_id,
#             "created_at": datetime.now().isoformat(),
#             "updated_at": datetime.now().isoformat(),
#             "subject": data.get('subject', ''),
#             "body": data.get('body', ''),
#             "to_emails": data.get('to_emails', []),
#             "cc_emails": data.get('cc_emails', []),
#             "attachment_name": data.get('attachment_name'),
#             "attachment_data": data.get('attachment_data'),
#             "attachment_type": data.get('attachment_type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#         }
        
#         # Save the draft to a file
#         with open(get_draft_path(draft_id), 'w') as f:
#             json.dump(draft, f)
        
#         return jsonify({"message": "Draft created successfully", "draft_id": draft_id}), 201
    
#     except Exception as e:
#         return jsonify({"error": f"Error creating draft: {str(e)}"}), 500

# @draft_email_bp.route('/drafts/<draft_id>', methods=['GET'])
# def get_draft(draft_id):
#     """Get a specific email draft."""
#     try:
#         draft_path = get_draft_path(draft_id)
        
#         if not os.path.exists(draft_path):
#             return jsonify({"error": "Draft not found"}), 404
        
#         with open(draft_path, 'r') as f:
#             draft = json.load(f)
        
#         return jsonify(draft), 200
    
#     except Exception as e:
#         return jsonify({"error": f"Error retrieving draft: {str(e)}"}), 500

# @draft_email_bp.route('/drafts', methods=['GET'])
# def list_drafts():
#     """List all email drafts."""
#     try:
#         drafts = []
        
#         for filename in os.listdir(DRAFTS_DIR):
#             if filename.endswith('.json'):
#                 with open(os.path.join(DRAFTS_DIR, filename), 'r') as f:
#                     draft = json.load(f)
#                     # Include only metadata in the list view
#                     drafts.append({
#                         "id": draft["id"],
#                         "subject": draft["subject"],
#                         "created_at": draft["created_at"],
#                         "updated_at": draft["updated_at"],
#                         "to_emails": draft["to_emails"]
#                     })
        
#         # Sort drafts by updated_at (newest first)
#         drafts.sort(key=lambda x: x["updated_at"], reverse=True)
        
#         return jsonify({"drafts": drafts}), 200
    
#     except Exception as e:
#         return jsonify({"error": f"Error listing drafts: {str(e)}"}), 500

# @draft_email_bp.route('/drafts/<draft_id>', methods=['PUT'])
# def update_draft(draft_id):
#     """Update an existing email draft."""
#     try:
#         if not request.is_json:
#             return jsonify({"error": "Request body must be JSON"}), 400
        
#         draft_path = get_draft_path(draft_id)
        
#         if not os.path.exists(draft_path):
#             return jsonify({"error": "Draft not found"}), 404
        
#         # Load existing draft
#         with open(draft_path, 'r') as f:
#             draft = json.load(f)
        
#         # Update draft with new data
#         data = request.get_json()
#         draft.update({
#             "updated_at": datetime.now().isoformat(),
#             "subject": data.get('subject', draft.get('subject', '')),
#             "body": data.get('body', draft.get('body', '')),
#             "to_emails": data.get('to_emails', draft.get('to_emails', [])),
#             "cc_emails": data.get('cc_emails', draft.get('cc_emails', [])),
#             "attachment_name": data.get('attachment_name', draft.get('attachment_name')),
#             "attachment_data": data.get('attachment_data', draft.get('attachment_data')),
#             "attachment_type": data.get('attachment_type', draft.get('attachment_type'))
#         })
        
#         # Save updated draft
#         with open(draft_path, 'w') as f:
#             json.dump(draft, f)
        
#         return jsonify({"message": "Draft updated successfully", "draft_id": draft_id}), 200
    
#     except Exception as e:
#         return jsonify({"error": f"Error updating draft: {str(e)}"}), 500

# @draft_email_bp.route('/drafts/<draft_id>', methods=['DELETE'])
# def delete_draft(draft_id):
#     """Delete an email draft."""
#     try:
#         draft_path = get_draft_path(draft_id)
        
#         if not os.path.exists(draft_path):
#             return jsonify({"error": "Draft not found"}), 404
        
#         # Delete the draft file
#         os.remove(draft_path)
        
#         return jsonify({"message": "Draft deleted successfully"}), 200
    
#     except Exception as e:
#         return jsonify({"error": f"Error deleting draft: {str(e)}"}), 500

# @draft_email_bp.route('/drafts/<draft_id>/send', methods=['POST'])
# def send_draft(draft_id):
#     """Send an email from a draft."""
#     try:
#         draft_path = get_draft_path(draft_id)
        
#         if not os.path.exists(draft_path):
#             return jsonify({"error": "Draft not found"}), 404
        
#         # Load the draft
#         with open(draft_path, 'r') as f:
#             draft = json.load(f)
        
#         # Import the send_email function from sendemail_service
#         from sendemail_service import send_email
        
#         # Get email credentials from environment variables
#         from_email = os.getenv('emailaccount')
#         app_password = os.getenv('app_password')
        
#         # Send the email
#         response, is_sent = send_email(
#             subject=draft['subject'],
#             body=draft['body'],
#             to_emails=draft['to_emails'],
#             cc_emails=draft.get('cc_emails', []),
#             from_email=from_email,
#             appPassword=app_password,
#             attachment_name=draft.get('attachment_name'),
#             attachment_data=draft.get('attachment_data'),
#             attachment_type=draft.get('attachment_type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#         )
        
#         if is_sent:
#             # Optionally delete the draft after sending
#             # os.remove(draft_path)
#             return jsonify({"message": "Email sent successfully", "draft_id": draft_id}), 200
#         else:
#             return jsonify({"error": response}), 500
    
#     except Exception as e:
#         return jsonify({"error": f"Error sending draft: {str(e)}"}), 500
