#!/usr/bin/python3

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import requests
import json
import pyinputplus


headers = {
    'Accept': 'application/json',
    'Authorization': 'Basic aG5vOkQhQDEwZw==',
}


headers={'Content-Type': 'application/vnd.newtec.conf-v1+json', 'Accept': 'application/json'}
x_h=pyinputplus.inputPassword(prompt="Enter the credentials for hno user: ",mask="*")
auth1=("hno",x_h)

# From and To date for which you need the data date. Uses the ISO8601 format (yyyy-MM-ddTHH:mm:ss.SSSZ)

params = (
    ('from', '2020-03-21'),
    ('to', '2020-03-22'),
)


# Here we have considreded Kacific_SVNO for other vnos replace the Kacific_SVNO with the vno name configured in dailog

rsp = requests.get('http://10.0.10.27/qm/rest/accounting/json/Kacific_SVNO', headers=headers, auth=auth1,params=params)
data=rsp.text
data=json.loads(data)["csv"]
#print(data["csv"])
with open(r"C:\scripts\volume.csv", mode="w") as fs:
	fs.write(data)


smtp_ssl_host = 'smtp.gmail.com'  # smtp.mail.yahoo.com
smtp_ssl_port = 465

# Enter your email credentials replace xxxxx with your credentials
username = r'xxxxxx'
password = r'xxxxxx'
sender = 'ramkumarbalaguru@gmail.com'
targets = ['ramkumarbalaguru@gmail.com',]

msg = MIMEMultipart()
msg['Subject'] = 'VNO Volume CSV Files'
msg['From'] = sender
msg['To'] = ', '.join(targets)



txt = MIMEText('I have attached volume info for Kacific SVNO')
msg.attach(txt)

filepath = r'C:\scripts\volume.csv'
with open(filepath, 'r') as f:
    img = MIMEImage(f.read(),_subtype="CSV")

img.add_header('Content-Disposition',
               'attachment',
               filename=os.path.basename(filepath))
msg.attach(img)

server = smtplib.SMTP_SSL(smtp_ssl_host, smtp_ssl_port)
server.login(username, password)
server.sendmail(sender, targets, msg.as_string())
server.quit()