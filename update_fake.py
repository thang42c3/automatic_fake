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
price_mongo = mydb["price_9h_30"]



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



def auto_trade(driver, symbol, volume, ssi_pin_code, error_trade):
    time.sleep(3)
    print(volume)
    if int(volume) > 0:
        driver.find_element_by_id("btnOrderBuy").click()
    elif int(volume) < 0:
        driver.find_element_by_id("btnOrderSell").click()
    code_stock = driver.find_element_by_id("txtStockSymbol")
    code_stock.send_keys(symbol)
    volume_stock = driver.find_element_by_id("txtOrderUnits")
    volume = int(volume)
    volume_abs = abs(volume) * 100
    volume_stock.send_keys(volume_abs)
    pin_stock = driver.find_element_by_id("txtSecureCode")
    pin_stock.send_keys(ssi_pin_code)
    time.sleep(5)
    price = driver.find_element_by_id('orderMatchedPrice').text
    #price = driver.find_element_by_id('orderPriorClosePrice').text  # Cái này thử nghiệm, phải xóa đi
    info_stock_exchange = driver.find_element_by_id("orderFullName").text
    print(info_stock_exchange)
    stock_exchange = utility.get_stock_exchange(info_stock_exchange)
    try:
        for error in error_trade:
            if error[0] == symbol:
                error_trade.remove(error)
        price = price.replace(",", ".")
        print(symbol, price)
        price_input = float(price)
        if int(volume) > 0:
            order_type = "BUY"
        else:
            order_type = "SELL"

        upcom_delta = float(config["upcom_delta"])
        price_stock_send_key = utility.input_price_style(stock_exchange, price_input, upcom_delta, order_type)
        print(price_stock_send_key)
        price_stock = driver.find_element_by_id("txtOrderPrice")
        price_stock.send_keys(price_stock_send_key)

        time.sleep(5)
        driver.find_element_by_id("btnOrder").click()
        time.sleep(5)
        time_run = utility.convert_date(datetime.today().strftime("%Y/%m/%d %H:%M:%S"), "Asia/Jakarta", 'Asia/Jakarta')
        if int(volume) > 0:
            pop_up = symbol + " (" + stock_exchange + ")" + time_run + " :" + " mua " + str(volume_abs) + " giá " + str(
                price) + ":  " + driver.find_element_by_id('popup_message').text
        elif int(volume) < 0:
            pop_up = symbol + " (" + stock_exchange + ")" + time_run + " :" + " bán " + str(volume_abs) + " giá " + str(
                price) + ":  " + driver.find_element_by_id('popup_message').text
        button = driver.find_element_by_id('popup_ok')
        button.click()
        try:
            wrong_ssi_pincode = driver.find_element_by_id('orderNotice').text
        except NoSuchElementException:
            wrong_ssi_pincode =""
        pop_up = pop_up + ". " + wrong_ssi_pincode
        utility.log(pop_up)
        email_content = pop_up
        time.sleep(2)
    except:
        if [symbol, volume] in error_trade:
            pass
        else:
            error_trade.append([symbol, volume])
        print("Loi mat roi")
        email_content = ""
    if int(volume) > 0:
        driver.find_element_by_id("btnOrderBuy").click()
    elif int(volume) < 0:
        driver.find_element_by_id("btnOrderSell").click()
    return email_content, price, error_trade

def get_price(date_, symbol):
    '''
    driver = webdriver.Chrome()
    for i in df.index:
        utility.log("Name: {0}".format(df["ssi_name"][i]))
        utility.log("Starting")
        ssi_accout_changed = auto_login(driver, str(df['ssi_username'][i]), str(df['ssi_password'][i]),
                                        str(df['ssi_account'][i]))
        error_trade = []


        price = auto_trade(driver, symbol, 10, str(df['ssi_pin_code'][i]), error_trade)[1]
        driver.close()

    print(symbol)
    '''
    date_ = date_[:4] + "-" + date_[4:6] + "-" + date_[6:]
    price = price_mongo.find_one({"$and": [{'date': date_}, {'code': symbol}]})['price']

    return price


def get_symbol(date_, symbol):
    print(symbol)
    cusor = mycol.find_one({'date': date_})[symbol]
    print(cusor)
    if cusor['ck_tong'] != '-':
        ck_tong = cusor['ck_tong']
    else:
        ck_tong = 0

    if cusor['ck_kha_dung'] != '-':
        ck_kha_dung = cusor['ck_kha_dung']
    else:
        ck_kha_dung = 0

    if cusor['muat0'] != '-':
        muat0 = cusor['muat0']
    else:
        muat0 = 0

    if cusor['muat1'] != '-':
        muat1 = cusor['muat1']
    else:
        muat1 = 0

    if cusor['muat2'] != '-':
        muat2 = cusor['muat2']
    else:
        muat2 = 0

    if cusor['bant0'] != '-':
        bant0 = cusor['bant0']
    else:
        bant0 = 0

    if cusor['bant1'] != '-':
        bant1 = cusor['bant1']
    else:
        bant1 = 0

    if cusor['bant2'] != '-':
        bant2 = cusor['bant2']
    else:
        bant2 = 0

    if cusor['gia_tb'] != '-':
        gia_tb = cusor['gia_tb']
    else:
        gia_tb = 0
    ck_doi_ban = cusor['ck_doi_ban']
    change = cusor['change']
    gia_tt =get_price(date_,symbol)

    if change <= 0:
        gia_tb = gia_tb
    if change > 0 :
        gia_tb = ((int(ck_tong)-int(change)*100)*float(gia_tb) + int(change)*100*float(gia_tt))/int(ck_tong)

    gia_tri = int(gia_tb*ck_tong)*1000
    gia_tri_tt = int(float(gia_tt)*ck_tong)*1000
    print(gia_tri_tt)
    print(gia_tri)
    if gia_tri == 0:
        lai_lo = "0"
    else:
        lai_lo = intWithPoints(gia_tri_tt-gia_tri) +"(" + str(round((gia_tri_tt-gia_tri)*100/gia_tri,2))+"%)"
    mycol_real.update({'date': date_}, {'$set': {'stocks_info.{0}.symbol'.format(symbol): symbol, 'stocks_info.{0}.ck_tong'.format(symbol): ck_tong,
                                                             'stocks_info.{0}.ck_kha_dung'.format(symbol): ck_kha_dung,
                                                             'stocks_info.{0}.muat0'.format(symbol): muat0,
                                                             'stocks_info.{0}.bant0'.format(symbol): bant0,
                                                            'stocks_info.{0}.muat1'.format(symbol): muat1,
                                                              'stocks_info.{0}.bant1'.format(symbol): bant1,
                                                            'stocks_info.{0}.muat2'.format(symbol): muat2,
                                                             'stocks_info.{0}.bant2'.format(symbol):bant2,
                                                                'stocks_info.{0}.gia_tb'.format(symbol):gia_tb,
                                                             'stocks_info.{0}.gia_tri'.format(symbol): intWithPoints(gia_tri),
                                                        'stocks_info.{0}.gia_tt'.format(symbol): gia_tt,
                                                             'stocks_info.{0}.gia_tri_tt'.format(symbol): intWithPoints(gia_tri_tt),
                                                 'stocks_info.{0}.lai_lo'.format(symbol): lai_lo,
                                                             'stocks_info.{0}.ck_doi_ban'.format(symbol): ck_doi_ban}})
    return gia_tri, gia_tri_tt, muat0, bant0, float(gia_tt)


def update_real(date_):
    cusor = mycol.find_one({'date': date_})
    gia_tri = 0
    gia_tri_tt = 0
    tong_mua = 0
    tong_ban = 0

    for symbol in cusor:
        if symbol in ['date', '_id', 'tien_kd']:
            continue
        else:
            gia_tri_symbol, gia_tri_tt_symbol, muat0, bant0, gia_tt = get_symbol(date_, symbol)
            gia_tri = gia_tri + gia_tri_symbol
            gia_tri_tt = gia_tri_tt + gia_tri_tt_symbol
            tong_mua = tong_mua + muat0 * gia_tt*1000
            tong_ban = tong_ban + bant0*gia_tt*1000


    tien_kd = cusor['tien_kd']
    tong_tai_san =tien_kd + tong_ban -tong_mua + gia_tri_tt
    print('Tong ban', tong_ban)
    print('Tong mua', tong_mua)
    tien_ban_dau = 2500000000
    lai_lo_tong = tong_tai_san - tien_ban_dau
    print(lai_lo_tong)

    lai_lo_tong = str(intWithPoints(int(lai_lo_tong))) + "(" + str(round(float(lai_lo_tong * 100 / tien_ban_dau), 2)) + "%)"

    lai_lo = intWithPoints(gia_tri_tt - gia_tri) + "(" + str(round((gia_tri_tt - gia_tri) * 100 / gia_tri, 2)) + "%)"
    mycol_real.update({'date': date_}, {'$set': {'gia_tri': intWithPoints(gia_tri), 'gia_tri_tt': intWithPoints(gia_tri_tt), 'lai_lo': lai_lo,
                                                 'tong_tai_san': tong_tai_san, 'lai_lo_tong':lai_lo_tong}})


def run_update_real():

    date_ = datetime.now()
    date_ = date_.strftime("%Y%m%d")

    query = mycol_real.find({"date": date_})

    print(query)
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