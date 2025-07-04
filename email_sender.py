'''# email_sender.py
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()
EMAIL_HOST = os.getenv('EMAIL_HOST','smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT',465))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')'''

#email_sender.py

import smtplib
from email.mime.text import MIMEText


def send_email(to_email: str, subject: str, body: str, from_email: str, email_password: str):
     """Send via Gmail SMTP using exactly the credentials passed in."""
     msg = MIMEText(body)
     msg['Subject'] = subject
     msg['From']    = from_email
     msg['To']      = to_email
 
     # Connect to Gmail's SMTP server on port 587 (TLS)
     with smtplib.SMTP("smtp.gmail.com", 587) as server:
         server.starttls()
         server.login(from_email, email_password)
         server.sendmail(from_email, to_email, msg.as_string())