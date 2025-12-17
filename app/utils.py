import random, smtplib, os, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings


EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD


def send_verification_email(email: str, verification_code: str):
    """Send a verification email with the provided code."""
    # Create the email content
    subject = "Your Verification Code"
    body = f"Your verification code is: {verification_code}"

    # Set up the email server
    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.send_message(msg)

def send_verification_sms(phone_number: str, verification_code: str):
        api_key = settings.TEXT_SMS_API_KEY
        api_sender_id =  settings.TEXT_SMS_SENDER_ID
        api_partner_id =  settings.TEXT_SMS_PARTNER_ID
        base_url =  settings.TEXT_SMS_API_URL
        message = f"Your verification code is: {verification_code}"
        
        params = {
            "apikey": api_key,
            "partnerID": api_partner_id,
            "shortcode": api_sender_id,
            "mobile": phone_number,
            "message": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        response = requests.post(base_url, json=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": response.json()["error"]}

def generate_verification_code()->str:
        verification_code = str(random.randint(100000, 999999))
        return verification_code