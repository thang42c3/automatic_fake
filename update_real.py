import psycopg2
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from datetime import datetime
from datetime import date
import schedule
from selenium.webdriver.common.keys import Keys
import csv
import pandas as pd
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config.config import configs
import time
import psycopg2
from ftplib import FTP
from datetime import datetime,timedelta
import pytz
import schedule
from selenium.common.exceptions import NoSuchElementException


import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import pymongo
df = pd.read_excel('./data/user_trading.xlsx', sheet_name=0,
                   converters={'ssi_username': str, 'ssi_pin_code': str, 'ssi_account': str})

from utility.utility import utility

config = configs()
utility= utility()

myclient = pymongo.MongoClient(config["URI_MONGO"], connect=False)
mydb = myclient[config['DATABASE']]
mycol_real = mydb["stock_trade_result_bb"]
mycol = mydb[config["COLLECTION"]]




def intWithPoints(x):
    if type(x) not in [type(0), type(0)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithPoints(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ".%03d%s" % (r, result)
    return "%d%s" % (x, result)

def find_previous_date(date_):
    date_ = datetime.strptime(date_, "%Y%m%d")
    if (date_.isoweekday() not in [1, 7]):
        date_ = date_ - timedelta(1)  # datetime.today().strftime("%Y%m%d")
        # now = datetime.today().strftime('%Y%m%d') code cu xu ly ngay hien tai
    elif (date_.isoweekday() == 1):  # Tinh huong roi vao thu 2
        date_ = date_ - timedelta(3)  # datetime.today().strftime("%Y%m%d")
    elif (date_.isoweekday() == 7):
        date_ = date_ - timedelta(2)
    date_ = date_.strftime("%Y%m%d")
    return date_

def find_next_date(date_):
    date_ = datetime.strptime(date_, "%Y%m%d")
    if (date_.isoweekday() in range(1,5)):
        date_ = date_+timedelta(1)  # datetime.today().strftime("%Y%m%d")
        #now = datetime.today().strftime('%Y%m%d') code cu xu ly ngay hien tai
    elif (date_.isoweekday() == 5):    # Tinh huong roi vao thu 2
        date_ = date_+timedelta(3)  # datetime.today().strftime("%Y%m%d")
    date_ = date_.strftime("%Y%m%d")
    return date_

def auto_login(driver, ssi_username, ssi_password, ssi_account):
    driver.get(config["ssi_web_link"])
    print('done')
    user = driver.find_element_by_id("name")
    user.send_keys(ssi_username)
    password = driver.find_element_by_id("txtPassword")
    _ssi_password = utility.get_passwd(ssi_password)
    password.send_keys(_ssi_password)
    driver.find_element_by_id("btnLogin").click()
    print("Da an xong nut")
    time.sleep(5)
    driver.find_element_by_xpath('//a[contains(@href,"javascript:onChangeAccount();")]').click()
    time.sleep(5)

    driver.find_element_by_id('multiAccount_{0}'.format(ssi_account)).click()
    time.sleep(3)
    driver.find_element_by_xpath('//a[contains(@onclick,"setDefaultAccount();")]').click()
    time.sleep(2)
    try:
        button = driver.find_element_by_id('popup_ok')
        button.click()
        print("Da doi account")
    except NoSuchElementException:
        print("Van giu nguyen account")

    time.sleep(3)
    ssi_account_changed = driver.find_element_by_id('spanAccountDefault').text
    print(ssi_account_changed)
    if ssi_account_changed == ssi_account:
        print("Da cap nhat tai khoan thanh cong")
    else:
        print("Tai khoan chuyen khong thanh cong")
    return ssi_account_changed

def update_real(date_):
    for i in df.index:
        driver = webdriver.Chrome()
        # Specify the Google browser path

        ssi_accout_changed = auto_login(driver, str(df['ssi_username'][i]), str(df['ssi_password'][i]),
                                        str(df['ssi_account'][i]))
        driver.get("https://webtrading.ssi.com.vn/#Portfolio_ListProperties")
        for i in range(0, 3):
            time.sleep(2)
            html = driver.page_source
            parse = BeautifulSoup(html, 'html.parser')
            body = parse.find(id="StockBody")
            rows = body.find_all('tr')
            lists = []
            print(rows)

            for row in rows:
                columns = row.find_all('td')
                list = []
                for column in columns:
                    list.append(column.text)

                print(list[1], list[18])
                symbol = list[1]

                query = mycol.find_one(
                    {"$and": [{"date": date_},
                              {symbol: {"$exists": True}}]})
                if query is not None:
                    ck_doi_ban = mycol.find_one({"date": date_})[symbol]['ck_doi_ban']
                    tong_tinh_toan = mycol.find_one({"date": date_})[symbol]['ck_tong']
                    kd_tinh_toan = mycol.find_one({"date": date_})[symbol]['ck_kha_dung']
                else:
                    ck_doi_ban = 0
                    tong_tinh_toan = list[2]
                    kd_tinh_toan = list[3]
                mycol_real.update({'date': date_}, {'$set': {'stocks_info.{0}.symbol'.format(symbol): symbol, 'stocks_info.{0}.ck_tong'.format(symbol): list[2],
                                                             'stocks_info.{0}.ck_kha_dung'.format(symbol): list[3],
                                                             'stocks_info.{0}.ck_cam_co'.format(symbol): list[4], 'stocks_info.{0}.muat0'.format(symbol): list[8],
                                                             'stocks_info.{0}.bant0'.format(symbol): list[9], 'stocks_info.{0}.muat1'.format(symbol): list[10],
                                                              'stocks_info.{0}.bant1'.format(symbol): list[11], 'stocks_info.{0}.muat2'.format(symbol): list[12],
                                                             'stocks_info.{0}.bant2'.format(symbol): list[13], 'stocks_info.{0}.gia_tb'.format(symbol): list[14],
                                                             'stocks_info.{0}.gia_tri'.format(symbol): list[15], 'stocks_info.{0}.gia_tt'.format(symbol): list[16],
                                                             'stocks_info.{0}.gia_tri_tt'.format(symbol): list[17], 'stocks_info.{0}.lai_lo'.format(symbol): list[18],
                                                             'stocks_info.{0}.ck_doi_ban'.format(symbol): ck_doi_ban, 'stocks_info.{0}.tong_tinh_toan'.format(symbol): tong_tinh_toan,
                                                             'stocks_info.{0}.kd_tinh_toan'.format(symbol): kd_tinh_toan}})




            driver.find_element_by_link_text('Kế tiếp').click()


        row_sum = parse.find(id="StockFoot").find('tr')
        column_sum = row_sum.find_all('td')
        list_sum = []
        for column in column_sum:
            list_sum.append(column.text)
        gia_tri = list_sum[0]; gia_tri_tt = list_sum[2]; lai_lo = list_sum[3]

        driver.get("https://webtrading.ssi.com.vn/#Portfolio_CapablityBuy")
        time.sleep(2)

        tong_tai_san = driver.find_element_by_id("0_FO_CM_PM_spanTotalAsset").text
        tong_tien_cotherut = driver.find_element_by_id("0_FO_CM_PM_spanWithdrawal").text
        tai_san_thuc_co= driver.find_element_by_id("0_FO_CM_PM_spanTotalEquity").text
        suc_mua_toi_thieu = driver.find_element_by_id("0_FO_CM_PM_spanEECreditLimit").text
        tien_ban_dau = 2500000000
        lai_lo_tong = int(tai_san_thuc_co.replace('.',""))-tien_ban_dau
        lai_lo_tong = str(intWithPoints(lai_lo_tong)) + "(" + str(round(lai_lo_tong*100/tien_ban_dau,2))+"%)"
        mycol_real.update({'date': date_}, {'$set': {'tong_tai_san': tong_tai_san, 'tong_tien_cotherut':tong_tien_cotherut,
                                                'tai_san_thuc_co':tai_san_thuc_co,'suc_mua_toi_thieu':suc_mua_toi_thieu,
                                                     'gia_tri': gia_tri, 'gia_tri_tt': gia_tri_tt, 'lai_lo': lai_lo, 'lai_lo_tong':lai_lo_tong}})
        driver.close()



def run_update_real():
    date_ = datetime.now()
    date_ = date_.strftime("%Y%m%d")

    query = mycol_real.find({"date": date_})
    if query is None:
        mycol_real.insert({'date': date_})
    else:
        mycol_real.remove({'date': date_})
        mycol_real.insert({'date': date_})
    update_real(date_)
if __name__ == "__main__":
    run_update_real()


'''
        chrome_options = Options()
        # Use headless Google browser mode
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        # This is very important, we must take the sandbox mode disabled, or will be error
        chrome_options.add_argument('--no-sandbox')
        chromedriver = "/usr/bin/chromedriver"
        driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
'''