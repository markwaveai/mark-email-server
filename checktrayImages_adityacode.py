from rest_framework.response import Response
from rest_framework.decorators import api_view
from General.serializers import *
from General.models import *
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from Crop.models import *
from Ticket.models import *
from Crop.serializers import *
from Farmer.models import *
from Farmer.serializers import *
from django.db import connection, DatabaseError
import jwt
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date, parse_datetime
import pandas as pd
from collections import defaultdict
import os
from datetime import datetime, timedelta
import pytz
from django.core.mail import send_mail
from django.core.mail import EmailMessage
import pandas as pd  # Import pandas for Excel creation
from io import BytesIO  # Import BytesIO to handle in-memory file
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings 
from django.http import HttpRequest, JsonResponse
import json
import traceback

# Email sending function using EmailMessage
def send_email_with_attachment(subject, html_content, recipient_list, attachment_name, attachment_data):
    """
    Send an email using Django's EmailMessage class with an attachment.
    """
    email = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    email.content_subtype = "html"  # Set the email content to HTML
    email.attach(attachment_name, attachment_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()

# Generate Excel File
def generate_excel_file(data):
    """
    Generate an Excel file from the data dictionary.
    """
    # Create a dictionary to store the aligned data
    aligned_data = {
        'Date': list(data['day_counts'].keys()),
        'Day Count': list(data['day_counts'].values()),
        'Week': list(data['week_counts'].keys()),
        'Week Count': list(data['week_counts'].values()),
        'Month': list(data['month_counts'].keys()),
        'Month Count': list(data['month_counts'].values())
    }

    # Find the maximum length among the lists
    max_length = max(len(aligned_data['Date']), len(aligned_data['Week']), len(aligned_data['Month']))

    # Function to align data to the max length
    def align_list(lst, fill_value=''):
        return lst + [fill_value] * (max_length - len(lst))

    # Align all lists
    for key in aligned_data:
        aligned_data[key] = align_list(aligned_data[key])

    # Create the DataFrame
    df = pd.DataFrame(aligned_data)

    # Add 'Total Count' and 'Yesterday Count' as separate rows
    total_row = pd.DataFrame({
        'Date': ['Total Count'],
        'Day Count': [data['total_count']],
        'Week': [''],
        'Week Count': [''],
        'Month': [''],
        'Month Count': ['']
    })

    yesterday_row = pd.DataFrame({
        'Date': ['Yesterday Count'],
        'Day Count': [data['yesterday_count']],
        'Week': [''],
        'Week Count': [''],
        'Month': [''],
        'Month Count': ['']
    })

    # Append these rows to the DataFrame
    df = pd.concat([df, total_row, yesterday_row], ignore_index=True)

    # Write the DataFrame to an Excel file
    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Counts')
    excel_file.seek(0)
    return excel_file.read()

# Main function to count images and send the report
def count_images():
    try:
        with connection.cursor() as cursor:
            cursor.execute('''
                SELECT "date", uploaded_count
                FROM public."General_checktary_images_count"
            ''')
            records = cursor.fetchall()

        day_counts = defaultdict(int)
        week_counts = defaultdict(int)
        month_counts = defaultdict(int)
        total_count = 0

        utc_now = datetime.utcnow()
        ist = pytz.timezone('Asia/Kolkata')
        ist_now = utc_now.replace(tzinfo=pytz.utc).astimezone(ist)

        today_ist = ist_now.strftime('%Y-%m-%d')
        yesterday_ist = (ist_now - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_count = 0

        for date_str, uploaded_count in records:
            date_obj = datetime.strptime(date_str, "%d-%m-%Y")
            day = date_obj.strftime('%Y-%m-%d')
            week = date_obj.strftime('%Y-%U')
            month = date_obj.strftime('%Y-%m')

            day_counts[day] += uploaded_count
            week_counts[week] += uploaded_count
            month_counts[month] += uploaded_count
            total_count += uploaded_count

            if day == yesterday_ist:
                yesterday_count += uploaded_count

        sorted_day_counts = dict(sorted(day_counts.items()))
        sorted_week_counts = dict(sorted(week_counts.items()))
        sorted_month_counts = dict(sorted(month_counts.items()))

        data = {
            'day_counts': sorted_day_counts,
            'week_counts': sorted_week_counts,
            'month_counts': sorted_month_counts,
            'total_count': total_count,
            'yesterday_count': yesterday_count,
        }

        checktray_json = json.dumps(data)

        with connection.cursor() as cursor:
            update_query = '''
                UPDATE public."General_checktray"
                SET count = %s, checktray_json = %s
                WHERE id = 1;
            '''
            cursor.execute(update_query, [total_count, checktray_json])

        email_subject = f"Checktray Image Count Report for {yesterday_ist}"
        email_content = f"""
        <p>Dear Team,</p>
        <p>Please find attached the Checktray image count report as of {today_ist}.</p>
        <p>Best regards,<br>Backend Team</p>
        """

        # Generate Excel file
        excel_attachment = generate_excel_file(data)

        # Send email with attachment
        send_email_with_attachment(
            subject=email_subject,
            html_content=email_content,
            recipient_list=['aditya@infiplus.xyz'],
            attachment_name='Checktray_Image_Count_Report.xlsx',
            attachment_data=excel_attachment,
        )

        return data

    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        return {'error': error_message}

# API view to insert or update image count and trigger the report
@api_view(['POST'])
@permission_classes([AllowAny])
def upsert_checktray_image_count(request):
    try:
        data = request.data  # Use request.data to access JSON data
        date = data.get('date')
        uploaded_count = data.get('uploadedCount')
        ml_count = data.get('mlCount')

        if not date or uploaded_count is None or ml_count is None:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        with connection.cursor() as cursor:
            # Check if the date already exists
            cursor.execute('SELECT id FROM public."General_checktary_images_count" WHERE "date" = %s', [date])
            record = cursor.fetchone()

            if record:
                # Update existing record
                cursor.execute('''
                    UPDATE public."General_checktary_images_count"
                    SET uploaded_count = %s, ml_count = %s, modified_date = NOW()
                    WHERE id = %s
                ''', [uploaded_count, ml_count, record[0]])
                message = 'Record updated successfully'
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO public."General_checktary_images_count" ("date", uploaded_count, ml_count, created_date, modified_date)
                    VALUES (%s, %s, %s, NOW(), NOW())
                ''', [date, uploaded_count, ml_count])
                message = 'Record created successfully'

        # Call the count_images function directly
        count_images_data = count_images()  # Returns the data dictionary

        if 'error' in count_images_data:
            return JsonResponse({'message': message, 'error': count_images_data['error']}, status=500)

        return JsonResponse({'message': message, 'count_images_data': count_images_data}, status=200)

    except Exception as e:
        error_message = f"{str(e)}\n{traceback.format_exc()}"
        return JsonResponse({'error': error_message}, status=500)