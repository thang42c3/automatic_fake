# -*- coding: utf-8 -*-
from datetime import datetime
import pytz
import psycopg2
from ftplib import FTP
import smtplib
#from email.mime.multipart import MIMEMultipart
#from email.mime.text import MIMEText
from email.message import EmailMessage
# now it can reach class A of file_a.py in folder a
# by relative import
#import sys
#sys.path.append('..\\..\\auto_trade_magin')
from config.config import configs
#config = configs('../config/config.json')
from cryptography.fernet import Fernet
config = configs()
from datetime import datetime,timedelta
class utility:

    def convert_date(self,dt, tz1, tz2):
        tz1 = pytz.timezone(tz1)
        tz2 = pytz.timezone(tz2)
        dt = datetime.strptime(dt,"%Y/%m/%d %H:%M:%S")
        dt = tz1.localize(dt)
        dt = dt.astimezone(tz2)
        dt = dt.strftime("%Y/%m/%d %H:%M:%S")
        return dt

    def convert_hour(self,hour, minute):
        time_run = datetime.today().strftime('%Y/%m/%d')+ " " + str(hour) + ":" + str(minute) + ":" + "00"
        time_run = self.convert_date(time_run, 'Asia/Jakarta', "Asia/Jakarta") #UTC neu muon chuyen sang UTC
        print("Thoi gian chay hang ngay {0}".format(time_run[11:16]))
        hour = time_run[11:13]
        minute = time_run[14:16]
        return hour, minute
    def ftp_file(self,ip,user,passwd):
        print("Bat dau")
        ftp_client = FTP(ip)
        ftp_client.login(user=user, passwd=passwd)
        print("abc")
        ftp_client.cwd("/export")
        date_ = datetime.now()
        if (datetime.now().isoweekday() not in [1, 6, 7]):
            date_ = date_ - timedelta(1)  # datetime.today().strftime("%Y%m%d")
            # now = datetime.today().strftime('%Y%m%d') code cu xu ly ngay hien tai
        elif (datetime.now().isoweekday() == 1):  # Tinh huong roi vao thu 2
            date_ = date_ - timedelta(3)  # datetime.today().strftime("%Y%m%d")
        date_ = date_.strftime("%Y%m%d")
        file_name = "EMA20_B30_" + date_ + "_" + date_ + ".csv"
        file_stream = open(file_name, "wb")  # read file to send to byte
        ftp_client.retrbinary('RETR {}'.format(file_name), file_stream.write, 1024)
        file_stream.close()
        print("Download OK")
        ftp_client.close

        ftp_client.close


    def send_email(self, receiver_address, mail_content):
        msg = EmailMessage()

        my_address = "autotradestock@gmail.com"  # sender address

        app_generated_password = "epgzrymjtiiqsarc"  # gmail generated password
        sender_address = config["info_sys_email"]["email_address"]
        sender_pass = config["info_sys_email"]["email_pass"]

        _subject='Kết quả giao dịch ngày: {0}'.format(datetime.today().strftime('%Y%m%d'))  # email subject
        msg["Subject"] =_subject

        msg["From"] = sender_address  # sender address

        msg["To"] = receiver_address  # reciver address

        msg.set_content(mail_content)  # message body

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(my_address, app_generated_password)  # login gmail account

            print("sending mail")
            smtp.send_message(msg)  # send message
            print("mail has sent")
# Key to enscrypt and descrypt
    def generate_key(self):
            """
            Generates a key and save it into a file
            """
            key = Fernet.generate_key()
            with open("secret.key", "wb") as key_file:
                key_file.write(key)
    def load_key(self):
            """
            Load the previously generated key
            """
            return open("secret.key", "rb").read()
    def encrypt_message(self,message):
            """
            Encrypts a message
            """
            key = self.load_key()
            encoded_message = message.encode()
            f = Fernet(key)
            encrypted_message = f.encrypt(encoded_message)
            print(encrypted_message)
    def decrypt_message(self,encrypted_message):
            """
            Decrypts an encrypted message
            """
            key = self.load_key()
            f = Fernet(key)
            decrypted_message = f.decrypt(encrypted_message)
            #print(decrypted_message.decode())
            return decrypted_message.decode()
    def get_passwd(self, passwd):
        b=bytes(passwd, encoding='utf-8')
        return self.decrypt_message(b)
    def log(self,p_result):
        f = open("log.txt", "a", encoding="utf-8")
        f.write(p_result+"\n")
        f.close()

    def get_stock_exchange(self,name):
            stock_exchange=""
            if name.find("(UPCOM)") != -1:
                stock_exchange="UPCOM"
            elif name.find("(HNX)") != -1:
                stock_exchange="HNX"
            elif name.find("(HSX)") != -1:
                stock_exchange="HSX"
            return stock_exchange

    def input_price_style(self, stock_exchange, price_input, upcom_delta, order_type):
            if stock_exchange == "HSX":
                price_input="MP"
            elif stock_exchange == "HNX":
                price_input="MTL"
            else:
                if order_type == "BUY":
                    price_input = str(round((float(price_input) + upcom_delta), 1))
                else:
                    price_input = str(round((float(price_input) - upcom_delta), 1))
            return price_input

