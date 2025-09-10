import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from api_helper import ShoonyaApiPy
from downloadMasters_v0 import downloadFileMaster, getNFExpiry, getBNExpiry
import pyotp
import threading
from datetime import time
from retrying import retry
import requests
import json
import time
import calendar
import glob
import subprocess
from logger import child2WSLogger, master1WSLogger, child3WSLogger,child4WSLogger, applicationLogger
import pandas as pd
from datetime import datetime as dt, timedelta
from findexpiry import *
import csv
from collections import defaultdict
import os
#################CodeLog#############
'''
1. Added Individual Websocket for all four accounts_
2. Added a select stroke and a drop down list in front of it
3.Added lot of screen parts
4. GUI almost complete


5.  Add strike price websocket
6. Add exit button for individual account
'''

exchange = 'NFO'
price_type = 'LMT'
retention = 'DAY'
activeChild2 = 'false'
activeChild3 = 'false'
activeChild4 = 'false'
ordernumber1 = ''
ordernumber2 = ''
ordernumber3 = ''
ordernumber4 = ''
sordernumber1 = ''
sordernumber2 = ''
sordernumber3 = ''
sordernumber4 = ''

order_place = ''
sorder_place = ''
qty1 = ''
qty2 = ''
qty3 = ''
qty4 = ''
previousToken = ''



#################CodeLog#############
# Telegram Message
def tg_log(bot_message, chat_id):
    try:
        bot_token = '7396087608:AAE7doVtDmCBwGjvdFyH9M3og1qXBuRG38g'
        send_text = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&parse_mode=Markdown&text={bot_message}'
        response = requests.get(send_text)
    except Exception as e:
        print(f"Error in sending Telegram message: {e}")

# Telegram for SOS
def tg_log_sos(bot_message):
    tg_log(bot_message, '-1002187975609')

###########MASTER1 Credentials##############
with open('credentials1.json', 'r') as file:
    master_credentials = json.load(file)

userid1 = master_credentials['username']
password1 = master_credentials['pwd']
QR_Code1 = master_credentials['factor2']
vendor_code1 = master_credentials['vc']
api_secret1 = master_credentials['app_key']
imei1 = master_credentials['imei']

###########Child2 Credentials##############
with open('credentials2.json', 'r') as file:
    master_credentials = json.load(file)

userid2 = master_credentials['username']
password2 = master_credentials['pwd']
QR_Code2 = master_credentials['factor2']
vendor_code2 = master_credentials['vc']
api_secret2 = master_credentials['app_key']
imei2 = master_credentials['imei']

###########Child3 Credentials##############
with open('credentials3.json', 'r') as file:
    master_credentials = json.load(file)

userid3 = master_credentials['username']
password3 = master_credentials['pwd']
QR_Code3 = master_credentials['factor2']
vendor_code3 = master_credentials['vc']
api_secret3 = master_credentials['app_key']
imei3 = master_credentials['imei']

###########Child4 Credentials##############
with open('credentials4.json', 'r') as file:
    master_credentials = json.load(file)

userid4 = master_credentials['username']
password4 = master_credentials['pwd']
QR_Code4 = master_credentials['factor2']
vendor_code4 = master_credentials['vc']
api_secret4 = master_credentials['app_key']
imei4 = master_credentials['imei']

########Generate OTP 2FA #################

twoFA1 = pyotp.TOTP(QR_Code1).now()
twoFA2 = pyotp.TOTP(QR_Code2).now()
twoFA3 = pyotp.TOTP(QR_Code3).now()
twoFA4 = pyotp.TOTP(QR_Code4).now()

api1 = ShoonyaApiPy()  # Master Account
api2 = ShoonyaApiPy()  # Child2 Account
api3 = ShoonyaApiPy()  # Child3 Account
api4 = ShoonyaApiPy()  # Child4 Account


#downloadFileMaster()

############# LOGIN ####################


# Login Function for Master Account
@retry(stop_max_attempt_number=2, wait_fixed=10000)  # 10-second delay between retries
def shoonya_login1():
    global api1
    try:
        login_status = api1.login(
            userid=userid1,
            password=password1,
            twoFA=twoFA1,
            vendor_code=vendor_code1,
            api_secret=api_secret1,
            imei=imei1
        )
        client_name = login_status.get('uname')
        print(f"Login Successful!, Welcome {client_name} - Master ACCOUNT")
        connectFeed1()

        return True, client_name
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        raise
    except Exception as e:
        # Handle wrong credentials or other errors

        raise


# Login Function for Child2 Account
@retry(stop_max_attempt_number=2, wait_fixed=10000)  # 20-second delay between retries
def shoonya_login2():
    global api2
    global activeChild2
    try:
        login_status = api2.login(
            userid=userid2,
            password=password2,
            twoFA=twoFA2,
            vendor_code=vendor_code2,
            api_secret=api_secret2,
            imei=imei2
        )
        client_name = login_status.get('uname')
        print(f"Login Successful!, Welcome {client_name} - Child2 ACCOUNT")
        connectFeed2()
        activeChild2 = 'true'
        enable_order_buttons()
        login_button2.config(bg="#90EE90")
        check_and_enable_buttons()
        return True, client_name
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        login_button2.config(bg="red")
        raise
    except Exception as e:
        # Handle wrong credentials or other errors
        login_button2.config(bg="red")
        raise


# Login Function for Child3 Account
@retry(stop_max_attempt_number=2, wait_fixed=10000)  # 30-second delay between retries
def shoonya_login3():
    global api3
    global activeChild3
    try:
        login_status = api3.login(
            userid=userid3,
            password=password3,
            twoFA=twoFA3,
            vendor_code=vendor_code3,
            api_secret=api_secret3,
            imei=imei3
        )
        client_name = login_status.get('uname')
        print(f"Login Successful!, Welcome {client_name} - Child3 ACCOUNT")
        connectFeed3()
        activeChild3 = 'true'
        enable_order_buttons()
        print("active child = true")
        login_button3.config(bg="#90EE90")
        return True, client_name
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        login_button3.config(bg="red")
        raise
    except Exception as e:
        # Handle wrong credentials or other errors
        login_button3.config(bg="red")
        raise


# Login Function for Child4 Account
@retry(stop_max_attempt_number=2, wait_fixed=10000)  # 40-sec


# ond delay between retries
def shoonya_login4():
    global api4
    global activeChild4
    try:
        login_status = api4.login(
            userid=userid4,
            password=password4,
            twoFA=twoFA4,
            vendor_code=vendor_code4,
            api_secret=api_secret4,
            imei=imei4
        )
        client_name = login_status.get('uname')
        print(f"Login Successful!, Welcome {client_name} - Child4 ACCOUNT")
        connectFeed4()
        activeChild4 = 'true'
        enable_order_buttons()
        login_button4.config(bg="#90EE90")
        return True, client_name
    except requests.exceptions.RequestException as e:
        # Handle connection errors
        login_button4.config(bg="red")
        raise
    except Exception as e:
        # Handle wrong credentials or other errors
        login_button4.config(bg="red")
        raise
#########       webSocket        ##############
def user1_socket_order_update(tick_data):
    # Run the processing logic in a separate thread.
    # tg_log_master("MASTER ACCOUNT")
    master1WSLogger.info(tick_data)
    thread = threading.Thread(target=processMaster1TickData, args=(tick_data,))
    thread.start()


def user1_socket_quote_update(tick_data):
    print(f"Quote Received for User1: {tick_data}")
    price = tick_data.get('lp')
    premium_price_button.config(text=price)


def user1_socket_open():
    print("WebSocket is now open for Master1:")


def user2_socket_order_update(tick_data):
    # Run the processing logic in a separate thread.
    child2WSLogger.info(tick_data)
    thread = threading.Thread(target=processchild2TickData, args=(tick_data,))
    thread.start()


def user2_socket_quote_update(tick_data):
    print(f"Quote Received for Child2: {tick_data}")


def user2_socket_open():
    print("WebSocket is now open for Child2:")


def user3_socket_order_update(tick_data):
    # Run the processing logic in a separate thread.
    child3WSLogger.info(tick_data)
    thread = threading.Thread(target=processChild3TickData, args=(tick_data,))
    thread.start()


def user3_socket_quote_update(tick_data):
    print(f"Quote Received for Child3: {tick_data}")


def user3_socket_open():
    print("WebSocket is now open for Child3:")


def user4_socket_order_update(tick_data):
    # Run the processing logic in a separate thread.
    child4WSLogger.info(tick_data)
    thread = threading.Thread(target=processChild4TickData, args=(tick_data,))
    thread.start()


def user4_socket_quote_update(tick_data):
    print(f"Quote Received for Child4: {tick_data}")


def user4_socket_open():
    print("WebSocket is now open for Child4:")

def connectFeed1():
    api1.start_websocket(
        order_update_callback=user1_socket_order_update,
        subscribe_callback=user1_socket_quote_update,
        socket_open_callback=user1_socket_open
    )
    # time.sleep(1)


def connectFeed2():
    api2.start_websocket(
        order_update_callback=user2_socket_order_update,
        subscribe_callback=user2_socket_quote_update,
        socket_open_callback=user2_socket_open
    )
    time.sleep(1)


def connectFeed3():
    api3.start_websocket(
        order_update_callback=user3_socket_order_update,
        subscribe_callback=user3_socket_quote_update,
        socket_open_callback=user3_socket_open
    )
    # time.sleep(1)


def connectFeed4():
    api4.start_websocket(
        order_update_callback=user4_socket_order_update,
        subscribe_callback=user4_socket_quote_update,
        socket_open_callback=user4_socket_open
    )
    time.sleep(1)

############ Process TICK DATA #################

def log_and_config_button(button, color, text, log_message):
    button.config(bg=color, text=text)
    applicationLogger.info(log_message)

def     process_order(tick_data, entity, button):
    print(f" WS {entity} Data = {tick_data}")
    globals()[f"{entity.lower()}WSLogger"].info(f" WS {entity} Data = {tick_data}")

    if (
            tick_data.get('status') == 'PENDING' and
            tick_data.get('exch') == 'NFO'
    ):
        if tick_data.get('trantype') == 'B':
            if tick_data.get('reporttype') == 'NewAck':
                applicationLogger.info(f"PLACE BUY ORDER for {entity}")
            elif tick_data.get('reporttype') == 'ModAck':
                applicationLogger.info(f"MODIFY BUY ORDER for {entity}")
            elif tick_data.get('reporttype') == 'PendingCancel':
                applicationLogger.info(f"Cancel BUY Order for {entity}")
        elif tick_data.get('trantype') == 'S':
            if tick_data.get('reporttype') == 'NewAck':
                applicationLogger.info(f"PLACE SELL ORDER for {entity}")
            elif tick_data.get('reporttype') == 'ModAck':
                applicationLogger.info(f"MODIFY SELL ORDER for {entity}")
            elif tick_data.get('reporttype') == 'PendingCancel':
                applicationLogger.info(f"Cancel SELL Order for {entity}")

    elif (
            tick_data.get('status') == 'OPEN' and
            tick_data.get('exch') == 'NFO'
    ):
        if tick_data.get('trantype') == 'B':
            if tick_data.get('reporttype') == 'New':
                log_and_config_button(button, "#007bff", "Buy Open", f"Buy Order OPEN for {entity}")
            elif tick_data.get('reporttype') == 'Replaced':
                log_and_config_button(button, "#90EE90", "Buy Modified", f"BUY ORDER: OPEN/REPLACED for {entity}")
        elif tick_data.get('trantype') == 'S':
            if tick_data.get('reporttype') == 'New':
                log_and_config_button(button, "#90EE90", "Sell Open", f"SELL Order OPEN for {entity}")
            elif tick_data.get('reporttype') == 'Replaced':
                log_and_config_button(button, "#90EE90", "Sell Modified", f"SELL ORDER OPEN/REPLACED for {entity}")

    elif (
            tick_data.get('status') == 'COMPLETE' and
            tick_data.get('exch') == 'NFO'
    ):
        if tick_data.get('trantype') == 'B' and tick_data.get('reporttype') == 'Fill':
            log_and_config_button(button, "#fd7e14", "Buy Filled", f"BUY ORDER FILLED for {entity}")
            price = tick_data.get('prc')
            tg_log_sos(f"Buy Order Filled @{price}")

        elif tick_data.get('trantype') == 'S' and tick_data.get('reporttype') == 'Fill':
            log_and_config_button(button, "#90EE90", "Sell Complete", f"SELL ORDER FILLED for {entity}")
            price = tick_data.get('prc')
            tg_log_sos(f"Sell Order Filled @{price}")

    elif (
            tick_data.get('status') == 'CANCELED' and
            tick_data.get('exch') == 'NFO'
    ):
        if tick_data.get('trantype') == 'B' and tick_data.get('reporttype') == 'Canceled':
            log_and_config_button(button, "#90EE90", "Buy Cancelled", f"BUY ORDER Cancelled for {entity}")
        elif tick_data.get('trantype') == 'S' and tick_data.get('reporttype') == 'Canceled':
            log_and_config_button(button, "red", "Sell Cancelled", f"SELL ORDER Cancelled for {entity}")

    elif tick_data.get('trantype') == 'B' and tick_data.get('reporttype') == 'Rejected':
        log_and_config_button(button, "#dc3545", "Buy Rejected", f"BUY ORDER Rejected for {entity}")

    elif tick_data.get('trantype') == 'S' and tick_data.get('reporttype') == 'Rejected':
        log_and_config_button(button, "#dc3545", "Sell Rejected", f"SELL ORDER Rejected for {entity}")



def processMaster1TickData(tick_data):
    process_order(tick_data, "MASTER1", box1_button)
    handle_order(tick_data)

def processchild2TickData(tick_data):
    process_order(tick_data, "Child2", box5_button)
    handle_order(tick_data)

def processChild3TickData(tick_data):
    process_order(tick_data, "Child3", box9_button)
    handle_order(tick_data)

def processChild4TickData(tick_data):
    process_order(tick_data, "Child4", box13_button)
    handle_order(tick_data)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
order_data = {}
# File path for saving the order data
file_path = "orders.csv"

# Check if the file exists; if not, create an empty DataFrame with the relevant columns
if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
    try:
        df_orders = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        # In case the file is empty, create an empty DataFrame
        print(f"{file_path} is empty, initializing an empty DataFrame.")
        df_orders = pd.DataFrame(columns=['norenordno', 'uid', 'actid', 'exch', 'tsym', 'trantype',
                                          'qty', 'prc', 'pcode', 'remarks', 'status', 'reporttype',
                                          'prctyp', 'ret', 'exchordid', 'dscqty', 'rejreason'])
else:
    # If the file doesn't exist or is empty, create an empty DataFrame
    print(f"{file_path} does not exist or is empty, initializing an empty DataFrame.")
    df_orders = pd.DataFrame(columns=['norenordno', 'uid', 'actid', 'exch', 'tsym', 'trantype',
                                      'qty', 'prc', 'pcode', 'remarks', 'status', 'reporttype',
                                      'prctyp', 'ret', 'exchordid', 'dscqty', 'rejreason'])



def handle_order(order):
    global df_orders
    order_number = order['norenordno']

    # Check if the order already exists in the DataFrame
    if order_number in df_orders['norenordno'].values:
        # Update the existing order
        logging.info(f"Updating order {order_number}")
        df_orders.update(pd.DataFrame([order]))
    else:
        # Add the new order
        logging.info(f"New order received: {order_number}")
        df_orders = pd.concat([df_orders, pd.DataFrame([order])], ignore_index=True)

    # Write the updated DataFrame to a CSV file
    df_orders.to_csv(file_path, index=False)
    logging.info(f"Order data saved to {file_path}")


def fetch_price():
    # Placeholder for fetching price
    return "Placeholder Price"

# Function to update the text box with fetched price
def update_price():
    price_value.set(fetch_price())

# Function to perform the sell action
def cancel_order(api, order_no):
    api.cancel_order(orderno=order_no)

def cancel_buy_order():
    global ordernumber1, ordernumber2, ordernumber3, ordernumber4
    orderno = [ordernumber1, ordernumber2, ordernumber3, ordernumber4]
    apis = [api1, api2, api3, api4]
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']

    threads = []
    for i in range(len(orderno)):
        if active_children[i]:  # Only cancel orders for active children
            t = threading.Thread(target=cancel_order, args=(apis[i], orderno[i]))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()  # Wait for all threads to complete

def cancel_sell_order():
    global sordernumber1, sordernumber2, sordernumber3, sordernumber4
    sorderno = [sordernumber1, sordernumber2, sordernumber3, sordernumber4]
    apis = [api1, api2, api3, api4]
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']

    threads = []
    for i in range(len(sorderno)):
        if active_children[i]:  # Only cancel orders for active children
            t = threading.Thread(target=cancel_order, args=(apis[i], sorderno[i]))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()  # Wait for all threads to complete

# Define the modify_order function that can be used by other functions

def placeBuyOrders():
    global tysm
    global ordernumber1, ordernumber2, ordernumber3, ordernumber4
    global qty1, qty2, qty3, qty4

    buy_button.state(['pressed', 'disabled'])

    # Check if quantity is selected
    if not qty1_var.get():
        messagebox.showerror("Error", "Please select quantity")
        return

    amo = 'NO'
    remarks = None

    # Retrieve the price from the global variable
    price = price_value.get()

    # List of API objects and corresponding quantities
    apis = [api1, api2, api3, api4]
    if selected_index.get() == "NIFTY":
        qty1 = qty1_var.get()
        qty2 = '25'  # add a multiplier later
        qty3 = '25'
        qty4 = '25'
    elif selected_index.get() == "BANKNIFTY":
        qty1 = qty1_var.get()
        qty2 = '15'  # add a multiplier later
        qty3 = '15'
        qty4 = '15'

    quantities = [qty1, qty2, qty3, qty4]  # Ensure these are correctly initialized
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']

    print(f"{price} and {quantities} and {active_children}")

    # Shared data structure for storing order numbers
    order_numbers = [None] * len(apis)
    lock = threading.Lock()

    def place_order(api, qty, index):
        print(f"{api}, {qty}, {index}")
        global order_place
        try:
            order_place = api.place_order(
                buy_or_sell='B',
                product_type='I',
                exchange='NFO',
                tradingsymbol=tysm,
                quantity=qty,
                discloseqty=0,
                price_type=price_type,
                price=price,
                trigger_price=None,
                retention=retention,
                amo=amo,
                remarks=remarks
            )

            norenordno = order_place.get('norenordno')
            with lock:
                order_numbers[index] = norenordno

            # Writing order details to a file

            #file_name = f"master_orders.txt"  # Generate the file name based on API
            #with open(file_name, 'a') as file:  # Open the file in append mode
            #        file.write(f"{qty},{index}")  # Write order details to the file

            print(f"Order placed successfully: {order_place}")
        except Exception as e:
            print(f"Error placing order: {e}")

    # Create and start threads for placing orders with different quantities if active
    threads = []
    for i, (api, qty, is_active) in enumerate(zip(apis, quantities, active_children)):
        if is_active:
            thread = threading.Thread(target=place_order, args=(api, qty, i))
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Unpack order numbers into individual variables
    ordernumber1, ordernumber2, ordernumber3, ordernumber4 = order_numbers

    # Print the order numbers if they are not empty
    if ordernumber1:
        print(f' order num1 : {ordernumber1}')
    if ordernumber2:
        print(f' order num2 : {ordernumber2}')
    if ordernumber3:
        print(f' order num3 : {ordernumber3}')
    if ordernumber4:
        print(f' order num4 : {ordernumber4}')

    return ordernumber1, ordernumber2, ordernumber3, ordernumber4


def modify_order(api, order_no, quantity, exchange, tradingsymbol, price_type, price):
    api.modify_order(
        exchange=exchange,
        tradingsymbol=tradingsymbol,
        orderno=order_no,
        newquantity=quantity,
        newprice_type=price_type,
        newprice=price
    )


def modify_buy_order():
    global tysm, ordernumber1, ordernumber2, ordernumber3, ordernumber4, exchange, price_type,  modifyBuy_value
    global qty2,qty3,qty4
    qty1 = qty1_var.get()
    print(f"Quantity for Buy Modify : {qty1}")
    orderno = [ordernumber1, ordernumber2, ordernumber3, ordernumber4]
    apis = [api1, api2, api3, api4]
    quantities = [qty1, qty2, qty3, qty4]
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']
    price = modifyBuy_value.get()  # Get price from modifyBuy_value
    print(f"{price} and {quantities} and {active_children}")
    threads = []
    for i in range(len(orderno)):
        if active_children[i]:  # Only modify orders for active children
            t = threading.Thread(target=modify_order, args=(apis[i], orderno[i], quantities[i], exchange, tysm, price_type, price))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()  # Wait for all threads to complete

def modify_sell_order():
    global tysm, sordernumber1, sordernumber2, sordernumber3, sordernumber4, exchange, price_type, qty_var, modifySell_value
    global  qty2, qty3, qty4
    qty1 = qty1_var.get()
    sorderno = [sordernumber1, sordernumber2, sordernumber3, sordernumber4]
    apis = [api1, api2, api3, api4]
    quantities = [qty1, qty2, qty3, qty4]
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']
    price = modifySell_value.get()  # Get price from modifySell_value

    threads = []
    for i in range(len(sorderno)):
        if active_children[i]:  # Only modify orders for active children
            t = threading.Thread(target=modify_order, args=(apis[i], sorderno[i], quantities[i], exchange, tysm, price_type, price))
            threads.append(t)
            t.start()

    for t in threads:
        t.join()  # Wait for all threads to complete







def placeSellOrder():
    global tysm
    global sordernumber1, sordernumber2, sordernumber3, sordernumber4
    global  qty2, qty3, qty4
    sell_button.state(['pressed', 'disabled'])
    qty1 = qty1_var.get()
    amo = 'NO'
    remarks = None

    # Retrieve the price from the global variable
    price = price1_value.get()

    # List of API objects and corresponding quantities
    apis = [api1, api2, api3, api4]
    quantities = [qty1, qty2, qty3, qty4]
    active_children = [True, activeChild2 == 'true', activeChild3 == 'true', activeChild4 == 'true']

    print(f"{price} and {quantities} and {active_children}")

    # Shared data structure for storing order numbers
    sorder_numbers = [None] * len(apis)
    lock = threading.Lock()

    def place_order(api, qty, index):
        global sorder_place
        try:
            sorder_place = api.place_order(
                buy_or_sell='S',
                product_type='I',
                exchange='NFO',
                tradingsymbol=tysm,
                quantity=qty,
                discloseqty=0,
                price_type=price_type,
                price=price,
                trigger_price=None,
                retention=retention,
                amo=amo,
                remarks=remarks
            )
            norenordno = sorder_place.get('norenordno')
            with lock:
                sorder_numbers[index] = norenordno
            print(f"Order placed successfully: {order_place}")
        except Exception as e:
            print(f"Error placing order: {e}")

    # Create and start threads for placing orders with different quantities if active
    threads = []
    for i, (api, qty, is_active) in enumerate(zip(apis, quantities, active_children)):
        if is_active:
            thread = threading.Thread(target=place_order, args=(api, qty, i))
            threads.append(thread)
            thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


    # Unpack order numbers into individual variables
    sordernumber1, sordernumber2, sordernumber3, sordernumber4 = sorder_numbers

    # Print the order numbers if they are not empty
    if sordernumber1:
        print(f' sorder num1 : {sordernumber1}')
    if sordernumber2:
        print(f' sorder num2 : {sordernumber2}')
    if sordernumber3:
        print(f' sorder num3 : {sordernumber3}')
    if sordernumber4:
        print(f' sorder num4 : {sordernumber4
        }')

    return sordernumber1, sordernumber2, sordernumber3, sordernumber4

    # resetting order number and qty

def getMasterPosition():
    ret = api1.get_positions()
    mtm = 0
    pnl = 0
    for i in ret:
        mtm += float(i['urmtom'])
        pnl += float(i['rpnl'])
        day_m2m = mtm + pnl
    print(f'{day_m2m} is your Daily MTM')


def updateMTMValue(api, button):
    ret = api.get_positions()

    if ret is None:
        mtm_value = 0
    else:
        mtm = 0
        pnl = 0
        for i in ret:
            mtm += float(i['urmtom'])
            pnl += float(i['rpnl'])
        day_m2m = mtm + pnl
        mtm_value = day_m2m

    print(f" MTM : {mtm_value}")
    button.config(text=str(mtm_value))

# Function to perform other actions as needed
def other_action():
    # Add your other action logic here
    pass  # Placeholder for the actual action logic


find_exp()

shoonya_login1()   # Login to Shoonya Master Account

######## Fetching List of Strikes ##########
global NFLTP
global BNLTP

quoteNF = api1.get_quotes(exchange='NSE', token='26000')
quoteBN = api1.get_quotes(exchange='NSE', token='26009')
quoteSX = api1.get_quotes(exchange='BSE', token='1')

#quoteSS = api1.get_quotes(exchange='NFO', token='37076')
#SSLTP = quoteSS.get("lp")
#print(SSLTP)
NFLTP = int(round(float(quoteNF.get("lp"))/50)*50)
BNLTP = int(round(float(quoteBN.get("lp"))/100)*100)
SXLTP = int(round(float(quoteSX.get("lp"))/100)*100)

print(f" BN: {BNLTP}, NF: {NFLTP} and SX: {SXLTP}")

global NFStrikeList, NFQtyList
global BNStrikeList, BNQtyList
global SXStrikeList, SXQtyList

NFStrikeList = [NFLTP - 50 * i for i in range(-7,7)]
BNStrikeList = [BNLTP - 100 * i for i in range(-7,7)]
SXStrikeList = [SXLTP - 100 * i for i in range(-7,7)]

NFQtyList = [25 * i for i in range(1,10)]
BNQtyList = [15 * i for i in range(1,10)]
SXQtyList = [10 * i for i in range(1,10)]
print(f'BNList: {BNStrikeList},'
      f'NFList: {NFStrikeList}'
      f'SXList: {SXStrikeList}')


######## Fetching List of Strikes ##########
# Define Bank Nifty and Nifty expiry values


def getNiftyExpiry():
    with open('nf_expiry_dates.txt', 'r') as file:
        nfExpDate = file.read()
        date_obj = datetime.strptime(nfExpDate, '%Y-%m-%d')
        NFExpiry = date_obj.strftime('%d%b%y').upper()
        return NFExpiry

def getBNExpiry():
    with open('bn_expiry_dates.txt', 'r') as file:
        bnExpDate = file.read()
        print(bnExpDate)
        date_obj = datetime.strptime(bnExpDate, '%Y-%m-%d')
        BNExpiry = date_obj.strftime('%d%b%y').upper()
        return BNExpiry

def getSensexExpiry():
    with open('sx_expiry_dates.txt', 'r') as file:
        sxExpDate = file.read()
        date_obj = datetime.strptime(sxExpDate, '%Y-%m-%d')
        SXExpiry = date_obj.strftime('%d%b%y').upper()
        return SXExpiry
def get_bn_current_expiry_date():
    today_date = dt.now().date()
    expiry_days_list = []

    with open('bn_expiry_dates.txt', 'r') as f:
        expiry_days_list = ([dt.strptime(i.replace('\n', ''), '%Y-%m-%d').date() for i in f.readlines()])

    expiry_days_list = sorted(expiry_days_list)
    for i in expiry_days_list:
        if (i - today_date) >= timedelta(0):
            return i
BNExpiry = getBNExpiry()  # Expiry value for Bank Nifty
NFExpiry = getNFExpiry()  # Expiry value for Nifty
SXExpiry = getSensexExpiry() # Expiry value for Sensex

########### Function to get the token #############


# Read the contents of the CSV file into a DataFrame
files = glob.glob("NFO_symbols.txt_*.txt")
files_with_dates = [(file, datetime.strptime(file.split('_')[-1].split('.txt')[0], "%Y-%m-%d")) for file in files]
latest_file = sorted(files_with_dates, key=lambda x: x[1], reverse=True)[0][0]

files_sx = glob.glob("BFO_symbols.txt_*.txt")
files_with_dates_sx = [(file, datetime.strptime(file.split('_')[-1].split('.txt')[0], "%Y-%m-%d")) for file in files_sx]
latest_file_sx = sorted(files_with_dates_sx, key=lambda x: x[1], reverse=True)[0][0]


# Read the latest file
df = pd.read_csv(latest_file)
df_sx = pd.read_csv(latest_file_sx)


# Function to get token from trading symbol
def get_token(trading_symbol):
    # Check if the trading symbol contains 'SENSEX'
    if "SENSEX" in trading_symbol:
        bfo_trading_symbol = convert_sensex_format(trading_symbol)
        print(bfo_trading_symbol)
        row = df_sx[df_sx['TradingSymbol'] == bfo_trading_symbol]
        if not row.empty:
            return row.iloc[0]['Token']
            print(row.iloc[0]['Token'])
        else:
            return None

    else:
        row = df[df['TradingSymbol'] == trading_symbol]

    if not row.empty:
        return row.iloc[0]['Token']
    else:
        return None


def convert_sensex_format(input_str):
    def is_last_friday(date):
        """Check if the given date is the last Friday of the month."""
        year = date.year
        month = date.month
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        last_friday = last_date - timedelta(days=(last_date.weekday() - 4) % 7)
        return date == last_friday

    parts = input_str.split('SENSEX')
    if len(parts) < 2:
        raise ValueError("Invalid input format")

    details = parts[1]
    date_part = details[:7]  # e.g., 27DEC24 or 03JAN25
    strike_price = details[7:-2]  # e.g., 78000
    ce_pe = details[-2:]  # CE or PE

    day = int(date_part[:2])
    month_str = date_part[2:5].upper()
    year = int(date_part[5:])

    month = datetime.strptime(month_str, "%b").month
    date_obj = datetime(2000 + year, month, day)

    if is_last_friday(date_obj):
        output = f"SENSEX{year}{month_str}{strike_price}{ce_pe}"
    else:
        output = f"SENSEX{year}{month}{day:02d}{strike_price}{ce_pe}"

    return output
# Function to get LTP for selected option
def getLTP():
    # Get the selected trading symbol
    global previousToken
    tysm = concatenate_values()
    if 'SENSEX' in tysm:
        exch = 'BFO'
    else:
        exch = 'NFO'

    # Get the token for the selected symbol
    token = get_token(tysm)
    print(token)

    if token is not None:
        try:
            # Check if previousToken is not empty and unsubscribe if so
            if previousToken != "":
                unsubscribeToken = f'{exch}|{previousToken}'
                print(f'UnsubscriptionToken : {unsubscribeToken}')
                api1.unsubscribe(unsubscribeToken)  # Unsubscribe from the old feed

            # Convert token to string
            token_str = str(token)

            # Fetch the LTP based on the token (Replace this with your actual LTP fetching logic)
            LTPObject = api1.get_quotes(exchange= exch, token=token_str)
            ltp = LTPObject.get("c")
            print(ltp)

            websocketToken = f'{exch}|{token}'
            api1.subscribe(websocketToken)
            print(f"subscribed token: {websocketToken}")

            # Update the previousToken with the current token
            previousToken = token_str

        except Exception as e:
            ltp = f"Error fetching LTP: {str(e)}"
    else:
        ltp = f"Token not found for {tysm}"

    # Update the price text box with the fetched LTP
    price_value.set(ltp)
    price1_value.set(ltp)
    modifyBuy_value.set(ltp)
    modifySell_value.set(ltp)


def releaseBuyButton():
    # Manually release the button
    buy_button.state(['!pressed', '!disabled'])
    sell_button.state(['!pressed', '!disabled'])

# Function to concatenate selected values
def concatenate_values(*args):
    global tysm
    selected_index_value = selected_index.get()
    selected_expiry_value = expiry_value.get()
    selected_strike_value = selected_strike.get()
    selected_option_value = selected_option.get()

    # Check if selected_index_value is "SENSEX" and append "E"
    if selected_index_value == "SENSEX":
        tysm = f"{selected_index_value}{selected_expiry_value}{selected_strike_value}{selected_option_value}E"
    else:
        tysm = f"{selected_index_value}{selected_expiry_value}{selected_option_value}{selected_strike_value}"

    print("Concatenated value:", tysm)
    master1_value.set(tysm)
    child2_value.set(tysm)
    child3_value.set(tysm)
    child4_value.set(tysm)

    return tysm


def updatePremiumPriceValue():
    pass

def check_and_enable_buttons():
    if activeChild2 == 'true':
        box7_button.config(state=tk.NORMAL)
    if activeChild3 == 'true':
        box11_button.config(state=tk.NORMAL)
    if activeChild4 == 'true':
        box15_button.config(state=tk.NORMAL)



########## Order Details WINDOW ##########


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        # Create a canvas and a scrollbar
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure the scrollbar and canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
def fetch_order_details(login_object):
    #print(login_object)
    response = login_object.get_order_book()
    #print(response)
    return response


def open_order_details_window(login_object):
    new_window = tk.Toplevel(root)
    new_window.title("Order Details")
    new_window.geometry("1200x400")  # Size of the new window

    scrollable_frame = ScrollableFrame(new_window)
    scrollable_frame.pack(fill="both", expand=True)

    # Fetch order details using the login object
    order_data = fetch_order_details(login_object)

    # Create headers with "Select" just before "Action"
    headers = ["tsym", "norenordno", "prc", "qty", "status", "trantype", "prctyp",
               "fillshares", "avgprc", "uid", "rejreason", "Select", "Action"]
    for col, header in enumerate(headers):
        header_label = tk.Label(scrollable_frame.scrollable_frame, text=header, font=('bold', 12))
        header_label.grid(row=0, column=col, padx=10, pady=5, sticky='w')

    selected_order = tk.IntVar()

    # Create labels and display order details in the scrollable frame
    for row_idx, order in enumerate(order_data, start=1):

        # Add radio button in the second-to-last column ("Select")
        radio_button = tk.Radiobutton(scrollable_frame.scrollable_frame, variable=selected_order, value=row_idx,
                                      anchor='w')
        radio_button.grid(row=row_idx, column=len(headers) - 2, padx=10, pady=5)

        # Add action button in the last column ("Action")
        action_button = tk.Button(scrollable_frame.scrollable_frame, text="Action",
                                  command=lambda idx=row_idx, ord=order: on_action_button_click())
        action_button.grid(row=row_idx, column=len(headers) - 1, padx=10, pady=5)

        # Fill other columns with order details (excluding "Select" and "Action")
        for col_idx, key in enumerate(headers[:-2]):  # Exclude 'Select' and 'Action'
            value = order.get(key, "")
            label = tk.Label(scrollable_frame.scrollable_frame, text=value)
            label.grid(row=row_idx, column=col_idx, padx=10, pady=5, sticky='w')


def on_action_button_click():
    ret = api1.get_order_book()  # Fetch order book from the API
    print("TAKING ACTION")
    # Iterate through each order in the response
    for order in ret:
        trantype = order.get('trantype')  # Get transaction type (B or S)
        status = order.get('status')  # Get order status
        exchange = order.get() #GET EXCHANGE

        # Check conditions for the transaction type and status
        if trantype == 'B':  # Buy transaction
            if status == 'PENDING':
                cancel_Order(order)  # Cancel order if status is PENDING
            elif status == 'OPEN':
                cancel_Order(order)  # Cancel order if status is OPEN
            elif status == 'COMPLETE':
                sell_market(order)  # Sell order if status is COMPLETE

        elif trantype == 'S':  # Sell transaction
            if status == 'PENDING':
                modify_sell_market(order)  # Modify sell order if status is PENDING
            elif status == 'OPEN':
                modify_sell_market(order)  # Modify sell order if status is OPEN


def cancel_Order(order):
    # Logic to cancel the order
    print(f"Cancelling order: {order['norenordno']}")


def sell_market(order):
    # Logic to sell at market price
    print(f"Selling at market price: {order['norenordno']}")


def modify_sell_market(order):
    # Logic to modify sell order
    print(f"Modifying sell order: {order['norenordno']}")


def enable_order_buttons():
    print(f"{activeChild2}, {activeChild3}, {activeChild4}")
    if activeChild2 == 'true':
        box8_button.config(state=tk.NORMAL)
    else:
        box8_button.config(state=tk.DISABLED)

    if activeChild3 == 'true':
        box12_button.config(state=tk.NORMAL)
    else:
        box12_button.config(state=tk.DISABLED)

    if activeChild4 == 'true':
        box16_button.config(state=tk.NORMAL)
    else:
        box16_button.config(state=tk.DISABLED)


#########################   SAMPLE DATA #################

# Create the main window
root = tk.Tk()
root.title("Shoonya Master")
root.geometry("1200x600")  # Set the window size to be larger


# Create a style for the button to increase its height
style = ttk.Style()
style.configure("TButton", padding=(10, 10))  # (horizontal padding, vertical padding)

# Create a frame to hold the buttons
button_frame = tk.Frame(root)
button_frame.pack(side=tk.TOP, fill=tk.X, pady=50)  # Increased padding for better visual spacing

# Create buttons for CHILD2, CHILD3, and CHILD4
login_button2 = tk.Button(button_frame, text="CHILD2", command=shoonya_login2, width=20, height=3)
login_button2.pack(side=tk.LEFT, padx=10)

login_button3 = tk.Button(button_frame, text="CHILD3", command=shoonya_login3, width=20, height=3)
login_button3.pack(side=tk.LEFT, padx=10)

login_button4 = tk.Button(button_frame, text="CHILD4", command=shoonya_login4, width=20, height=3)
login_button4.pack(side=tk.LEFT, padx=10)

release_button = ttk.Button(button_frame, text="RELEASE", command=releaseBuyButton, width=20)
release_button.pack(side=tk.LEFT, padx=10)



# Define the new Premium Price button
premium_price_button = ttk.Button(button_frame, text="Premium Price", command=updatePremiumPriceValue, width=20)
premium_price_button.pack(side=tk.LEFT, padx=10)

# Create a frame for the strike and index selection
selection_frame = tk.Frame(root)
selection_frame.pack(side=tk.TOP, pady=10)

# Label and dropdown box for index selection
index_label = tk.Label(selection_frame, text="Index : ")
index_label.grid(row=0, column=0, padx=10)

index_options = ["BANKNIFTY", "NIFTY", "SENSEX"]  # Options for index
selected_index = tk.StringVar(root)
index_dropdown = ttk.Combobox(selection_frame, textvariable=selected_index, values=index_options)
index_dropdown.grid(row=0, column=1)

# Label for expiry selection
expiry_label = tk.Label(selection_frame, text="Expiry : ")
expiry_label.grid(row=0, column=2, padx=10)

expiry_value = tk.StringVar()
expiry_label_value = tk.Label(selection_frame, textvariable=expiry_value)
expiry_label_value.grid(row=0, column=3)

# Label and dropdown box for strike selection
strike_label = tk.Label(selection_frame, text="Select Strike : ")
strike_label.grid(row=0, column=4, padx=10)

strike_options = []  # Initially empty
selected_strike = tk.StringVar(root)
strike_dropdown = ttk.Combobox(selection_frame, textvariable=selected_strike, values=strike_options)
strike_dropdown.grid(row=0, column=5)

# Label and dropdown box for option type selection
option_label = tk.Label(selection_frame, text="Option : ")
option_label.grid(row=0, column=6, padx=10)

# Create option dropdown with updated option_types
option_types = ["C", "P"]
selected_option = tk.StringVar(root)
option_dropdown = ttk.Combobox(selection_frame, textvariable=selected_option, values=option_types)
option_dropdown.grid(row=0, column=7)

# Bind the concatenate_values function to the option dropdown
selected_option.trace_add('write', concatenate_values)

# Function to update expiry label and strike options based on selected index
def update_selections(*args):
    if selected_index.get() == "NIFTY":
        expiry_value.set(NFExpiry)
        strike_dropdown['values'] = NFStrikeList
        qty1_dropdown['values'] = NFQtyList
    elif selected_index.get() == "BANKNIFTY":
        expiry_value.set(BNExpiry)
        strike_dropdown['values'] = BNStrikeList
        qty1_dropdown['values'] =BNQtyList
    elif selected_index.get() == "SENSEX":
        expiry_value.set(SXExpiry)
        strike_dropdown['values'] = SXStrikeList
        qty1_dropdown['values'] =SXQtyList

selected_index.trace_add('write', update_selections)

# Frame for fetch button and price display
fetch_frame = tk.Frame(root)
fetch_frame.pack(side=tk.TOP, pady=10)

new_button = tk.Button(fetch_frame, text="New Button", command=lambda: print("New button pressed"), width=20, height=3)
new_button.pack(side=tk.LEFT, padx=10)

# Button to fetch price
fetch_button = tk.Button(fetch_frame, text="Fetch Price", command=getLTP, width=20, height=3)
fetch_button.pack(side=tk.LEFT, padx=10)



price_label = tk.Label(fetch_frame, text="Price")
price_label.pack(side=tk.LEFT)

# Text box to display fetched price
price_value = tk.StringVar()
price_box = tk.Entry(fetch_frame, textvariable=price_value, width=10)
price_box.pack(side=tk.LEFT)

# Label and dropdown box for index selection
qty_label = tk.Label(fetch_frame, text="Qty")
qty_label.pack(side=tk.LEFT)

# StringVar to hold the selected quantity
qty1_var = tk.StringVar()


# Initially empty combobox
qty1_dropdown = ttk.Combobox(fetch_frame, textvariable=qty1_var, width=10)
qty1_dropdown.pack(side=tk.LEFT)

# Button to fetch price
buy_button = ttk.Button(fetch_frame, text="BUY", command=placeBuyOrders, width=20)
buy_button.configure(style="TButton")  # Ensure using default ttk style
buy_button.pack(side=tk.LEFT, padx=10)

buy_button.configure(style="GreenButton.TButton")


# Set the button's background color
style = ttk.Style()
style.configure("GreenButton.TButton", background="green")

# Text box to display fetched price
price1_value = tk.StringVar()
price1_box = tk.Entry(fetch_frame, textvariable=price1_value, width=10)
price1_box.pack(side=tk.LEFT)


sell_button = ttk.Button(fetch_frame, text="SELL", command=placeSellOrder, width=20)
sell_button.configure(style="TButton")  # Ensure using default ttk style
sell_button.pack(side=tk.LEFT, padx=10)

# Changing the button's background color to red using tkinter's Button style configuration
sell_button.configure(style="RedButton.TButton")

# Set the button's background color
style = ttk.Style()
style.configure("RedButton.TButton", background="red")

# Create a frame for the buttons and value box
button_frame = tk.Frame(root)
button_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

# Create buttons for MASTER1 and CHILD accounts
master1_button = tk.Button(button_frame, text="MASTER1", command=shoonya_login1, width=15, height=2)
master1_button.grid(row=0, column=0, padx=5, pady=5)

# Initialize StringVar
master1_value = tk.StringVar()
master1_box1 = tk.Entry(button_frame, textvariable=master1_value, state='readonly', width=23,  font=('Helvetica', 12))
master1_box1.grid(row=0, column=1, padx=5, pady=5)

child2_button = tk.Button(button_frame, text="CHILD2", command=shoonya_login2, width=15, height=2)
child2_button.grid(row=1, column=0, padx=5, pady=5)

child2_value = tk.StringVar()
child2_box1 = tk.Entry(button_frame, textvariable=child2_value, state='readonly', width=23,  font=('Helvetica', 12))
child2_box1.grid(row=1, column=1, padx=5, pady=5)

child3_button = tk.Button(button_frame, text="CHILD3", command=shoonya_login3, width=15, height=2)
child3_button.grid(row=2, column=0, padx=5, pady=5)

child3_value = tk.StringVar()
child3_box1 = tk.Entry(button_frame, textvariable=child3_value, state='readonly', width=23,  font=('Helvetica', 12))
child3_box1.grid(row=2, column=1, padx=5, pady=5)

child4_button = tk.Button(button_frame, text="CHILD4", command=shoonya_login4, width=15, height=2)
child4_button.grid(row=3, column=0, padx=5, pady=5)

child4_value = tk.StringVar()
child4_box1 = tk.Entry(button_frame, textvariable=child4_value, state='readonly', width=23,  font=('Helvetica', 12))
child4_box1.grid(row=3, column=1, padx=5, pady=5)

# Create individual "BOX" buttons for each account
box1_button = tk.Button(button_frame, text="Order Status 1", width=15, height=2)
box1_button.grid(row=0, column=2, padx=5, pady=5)

# Add buttons to the main window
box3_button = tk.Button(button_frame, text="MTM1", command=lambda: updateMTMValue(api1, box3_button), width=5, height=2, state=tk.NORMAL)
box3_button.grid(row=0, column=4, padx=5, pady=5)

box7_button = tk.Button(button_frame, text="MTM2", command=lambda: updateMTMValue(api2, box7_button), width=5, height=2, state=tk.DISABLED)
box7_button.grid(row=1, column=4, padx=5, pady=5)

box11_button = tk.Button(button_frame, text="MTM3", command=lambda: updateMTMValue(api3, box11_button), width=5, height=2, state=tk.DISABLED)
box11_button.grid(row=2, column=4, padx=5, pady=5)

box15_button = tk.Button(button_frame, text="MTM4", command=lambda: updateMTMValue(api4, box15_button), width=5, height=2, state=tk.DISABLED)
box15_button.grid(row=3, column=4, padx=5, pady=5)




box4_button = tk.Button(button_frame, text="OrdDet", width=5, height=2, command=lambda: open_order_details_window(api1))
box4_button.grid(row=0, column=5, padx=5, pady=5)


box5_button = tk.Button(button_frame, text="Order Status 2", width=15, height=2)
box5_button.grid(row=1, column=2, padx=5, pady=5)







# Create the button
box8_button = tk.Button(button_frame, text="OrdDet", width=5, height=2, command=lambda: open_order_details_window(api2), state=tk.DISABLED)
box8_button.grid(row=1, column=5, padx=5, pady=5)






box9_button = tk.Button(button_frame, text="Order Status 3", width=15, height=2)
box9_button.grid(row=2, column=2, padx=5, pady=5)





box12_button = tk.Button(button_frame, text="OrdDet", width=5, height=2, command=lambda: open_order_details_window(api3), state=tk.DISABLED)
box12_button.grid(row=2, column=5, padx=5, pady=5)


box13_button = tk.Button(button_frame, text="Order Status 4", width=15, height=2)
box13_button.grid(row=3, column=2, padx=5, pady=5)



box16_button = tk.Button(button_frame, text="OrdDet", width=5, height=2, command=lambda: open_order_details_window(api4), state=tk.DISABLED)
box16_button.grid(row=3, column=5, padx=5, pady=5)



# Create a button for the MODIFY action
modifyBuy_button = tk.Button(button_frame, text="Modify Buy", command=modify_buy_order, width=15, height=2)
modifyBuy_button.grid(row=0, column=8, rowspan=2, padx=2, pady=5)

modifyBuy_value = tk.StringVar()
modifyBuy_box = tk.Entry(button_frame, textvariable=modifyBuy_value, width=10)
modifyBuy_box.grid(row=0, column=7, rowspan=2, padx=2, pady=5)

# Create a button for the SELL action
modifySell_button = tk.Button(button_frame, text="Modify Sell", command=modify_sell_order, width=15, height=2)
modifySell_button.grid(row=2, column=8, rowspan=2, padx=2, pady=5)

modifySell_value = tk.StringVar()
modifySell_box = tk.Entry(button_frame, textvariable=modifySell_value, width=10)
modifySell_box.grid(row=2, column=7, rowspan=2, padx=2, pady=5)

# Create a button above the MODIFY button
cancelBuy_button = tk.Button(button_frame, text="Cancel Buy", command=cancel_buy_order, width=15, height=2)
cancelBuy_button.grid(row=4, column=7, rowspan=2, padx=2, pady=5)

cancelSell_button = tk.Button(button_frame, text="Cancel Sell", command=cancel_sell_order, width=15, height=2)
cancelSell_button.grid(row=4, column=8, rowspan=2, padx=2, pady=5)

# Start the main loop
root.mainloop()