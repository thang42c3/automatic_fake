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
from update_real import run_update_real
from update_database import update_database

import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

df = pd.read_excel('./data/user_trading.xlsx', sheet_name=0,
                   converters={'ssi_username': str, 'ssi_pin_code': str, 'ssi_account': str})

from utility.utility import utility

config = configs()
utility= utility()


def path_string():
    date_ = datetime.now()
    if (datetime.now().isoweekday() not in [1, 7]):
        date_ = date_ - timedelta(1)  # datetime.today().strftime("%Y%m%d")
        # now = datetime.today().strftime('%Y%m%d') code cu xu ly ngay hien tai
    elif (datetime.now().isoweekday() == 1):  # Tinh huong roi vao thu 2
        date_ = date_ - timedelta(3)  # datetime.today().strftime("%Y%m%d")
    elif (datetime.now().isoweekday() == 7):
        date_ = date_ - timedelta(2)
    date_ = date_.strftime("%Y%m%d")
    return config["info_fpt"]["fpt_file_name"] + date_ + "_" + date_ + ".csv"

def stock_data(p_str_path):
    p_str_path=p_str_path+path_string()
    df = pd.read_csv(p_str_path)
    return df


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

    driver.find_element_by_id('txtDefaultAccounMargin').clear()
    driver.find_element_by_id("txtDefaultAccounMargin").send_keys(ssi_account)
    time.sleep(3)
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


def auto_trade(driver, symbol, volume, ssi_pin_code, error_trade):
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

def main():
    # Tam bo qua khong dung ftp
#    utility.ftp_file(config["info_fpt"]["ftp_ip"], config["info_fpt"]["ftp_user"], config["info_fpt"]["ftp_password"])
#    f_result = stock_data(config["info_fpt"]["ftp_file_path"])
    f_result = stock_data("")
    print(f_result)
    for i in df.index:
        driver = webdriver.Chrome()
        '''
        chrome_options = Options()
        # Use headless Google browser mode
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        # This is very important, we must take the sandbox mode disabled, or will be error
        chrome_options.add_argument('--no-sandbox')
        chromedriver = "/usr/bin/chromedriver"
        # Specify the Google browser path
        driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
        '''
        utility.log("Name: {0}".format(df["ssi_name"][i]))
        utility.log("Starting")
        ssi_accout_changed = auto_login(driver, str(df['ssi_username'][i]), str(df['ssi_password'][i]),
                                        str(df['ssi_account'][i]))
        if ssi_accout_changed != str(df['ssi_account'][i]):
            utility.log("Ðã nh?m tài kho?n nh?p")
            break

        buy = []
        sell = []
        email_content = ""
        error_trade = []
        for j in range(len(f_result)):
            if int(f_result['change'][j]) != 0:
                print(f_result['symbol'][j], f_result['change'][j])
                if int(f_result['change'][j]) > 0:
                    buy.append(auto_trade(driver, f_result['symbol'][j], str(f_result['change'][j]), str(df['ssi_pin_code'][i]), error_trade)[0])
                if int(f_result['change'][j]) < 0:
                    sell.append(auto_trade(driver, f_result['symbol'][j], str(f_result['change'][j]), str(df['ssi_pin_code'][i]), error_trade)[0])


        while error_trade != []:
            print("Dang chay doan bi loi")
            print(error_trade)
            for error in error_trade:
                if error[1] > 0:
                    buy.append(auto_trade(driver, error[0], error[1],
                                          str(df['ssi_pin_code'][i]), error_trade)[0])
                if error[1] < 0:
                    sell.append(auto_trade(driver, error[0], error[1],
                                           str(df['ssi_pin_code'][i]), error_trade)[0])

        email_arrays = buy + sell
        print("Các hàng là", email_arrays)
        for k in range(len(email_arrays)):
            print(k)
            email_content = email_content + str(k+1) + ". " + email_arrays[k] + "\n"

        print(email_content)
        print(str(df['ssi_email'][i]))
        utility.send_email(str(df['ssi_email'][i]), email_content)
        driver.close()
        utility.log("Done")
    utility.log("==================================================================\n")

if __name__ == "__main__":	
    main()
    hour = config["info_schedule"]["schedule_hour"]
    minute = config["info_schedule"]["schedule_minute"]
    hour, minute = utility.convert_hour(hour, minute)
    print("Bat dau trading")
    print(datetime.now())
    time_run = hour + ":" + minute
    print(time_run)
    try:
        schedule.every().monday.at(time_run).do(main)
        schedule.every().tuesday.at(time_run).do(main)
        schedule.every().wednesday.at(time_run).do(main)
        schedule.every().thursday.at(time_run).do(main)
        schedule.every().friday.at(time_run).do(main)
        while True:
            schedule.run_pending()
            time.sleep(20)
            print("waiting for running")
    except (Exception) as error:
        utility.log(str(error))

'''
        #       driver = webdriver.Chrome()
        """
        # ĐOẠN NÀY CHẠY CHROME TRÊN HEROKU
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        driver = webdriver.Chrome("chromedriver", chrome_options=options)
        # ĐOẠN NÀY CHẠY CHROME TRÊN UBUNTU

 chrome_options = Options()
        # Use headless Google browser mode
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        # This is very important, we must take the sandbox mode disabled, or will be error
        chrome_options.add_argument('--no-sandbox')
        chromedriver = "/usr/bin/chromedriver"
        # Specify the Google browser path
        driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)




    hour = config["info_schedule"]["schedule_hour"]
    minute = config["info_schedule"]["schedule_minute"]
    hour, minute = utility.convert_hour(hour, minute)
    print("Bat dau trading")
    print(datetime.now())
    time_run = hour + ":" + minute
    print(time_run)
    try:
        schedule.every().monday.at(time_run).do(main)
        schedule.every().tuesday.at(time_run).do(main)
        schedule.every().wednesday.at(time_run).do(main)
        schedule.every().thursday.at(time_run).do(main)
        schedule.every().friday.at(time_run).do(main)
	
        while True:
            schedule.run_pending()
            time.sleep(20)
            print("waiting for running")
    except (Exception) as error:
        utility.log(str(error))
        
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
print("Giờ hiện tại =", current_time)


    chrome_options = Options()
    # Use headless Google browser mode
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    # This is very important, we must take the sandbox mode disabled, or will be error
    chrome_options.add_argument('--no-sandbox')
    chromedriver = "/usr/bin/chromedriver"
    # Specify the Google browser path
    driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
'''
