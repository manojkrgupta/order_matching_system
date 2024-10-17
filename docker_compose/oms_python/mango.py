import os
import time
import random
import logging
import threading
import pymongo as mg
import datetime as dt
# import config
from trade import Trade

class Mango: # Mango for MongoDB
    def __init__(s):
#         logger = logging.getLogger("uvicorn.error")
        logger = logging.getLogger("OMS")
        logger.setLevel(logging.DEBUG)
        s.log = logger
#         s.log = config.log
        s.mongodb_user = "admin"
        s.mongodb_pass = "admin"
        s.mongodb_url  = "mongo1:27017"
        s.stock_to_oms_thread_mapping = dict()
        s.trade = Trade(mongodb_transaction=True).trade

# ------------------------------------------------------------------------------------------------------
# Without using Transactions in Mongodb
# But this needs Replica Instance of MongoDB (standalone is not enough, and it gives error --> OperationFailure: Transaction numbers are only allowed on a replica set member or mongos, full error: {'ok': 0.0, 'errmsg': 'Transaction numbers are only allowed on a replica set member or mongos', 'code': 20, 'codeName': 'IllegalOperation'}
# ------------------------------------------------------------------------------------------------------
# Connect to database
# ------------------------------------------------------------------------------------------------------
    def connect_to_mongodb(s):
#         s.mgh = mg.MongoClient(f"mongodb://{s.mongodb_user}:{s.mongodb_pass}@{s.mongodb_url}/")
        s.mgh = mg.MongoClient(f"mongodb://{s.mongodb_url}/")
        s.mdb = s.mgh["order_matching_system"]

# -------------------------------------
#
# -------------------------------------
    def save_order_book(s, stock_id, sorted_buy_orders, sorted_sel_orders):
        b_col = f"stock.obook.{stock_id}" # order book for a stock. written for visualisation on UI. Not referred. Only written for display
        r1 = s.mdb.stock.obook[stock_id].delete_many({}) # to truncate collection. delete all rows, and keeping the schema
        r2 = s.mdb.stock.obook[stock_id].insert_one(
                    {'ts': dt.datetime.now(),
                     'sorted_buy_orders': sorted_buy_orders,
                     'sorted_sel_orders': sorted_sel_orders
                    })

# -------------------------------------
# Threads main function for processing one stock
# -------------------------------------
    def order_matching_engine(s, stock_id):
        s.connect_to_mongodb()  # in thread, make a new connection
        pid = os.getpid() # pid
        rid = random.randrange(100) # random run id -- from 0 to 9999 -- max 4 digit
        tim = time.time()
        trade_id_partial = f"{pid:06}.{rid:02}.{tim}"
        trade_counter = 1
        previous_trade_counter = 0
        print(f"starting -- order matching engine/thread for stock={stock_id} -- short id={trade_id_partial}")
        s.log.info(f"starting -- order matching engine/thread for stock={stock_id} -- short id={trade_id_partial}")
        o_col = f"stock.order.{stock_id}"
        t_col = f"stock.trade.{stock_id}"
        # a_col = f"stock.audit.{stockid}"
        try: # We need to check if order table exist, else mongo db will create by default -- which is bad(beyond code control)
            s.mdb.validate_collection(o_col)
            s.mdb.validate_collection(t_col)
            # s.mdb.validate_collection(a_col)
        except mg.errors.OperationFailure as e:
            r = f"failed to validate collections {o_col}, {t_col}. Exception = {e}"
            s.log.error(r)
            raise Exception(r)
        except Exception as e:
            r = f"failed to validate collections {o_col}, {t_col}. Exception = {e}"
            s.log.error(r)
            raise Exception(r)

        while trade_counter > previous_trade_counter:
            print(f"redingmd -- order matching engine/thread for stock={stock_id} -- short id={trade_id_partial}")
            s.log.info(f"redingmd -- order matching engine/thread for stock={stock_id} -- short id={trade_id_partial}")
            previous_trade_counter = trade_counter
            buy_orders = dict()
            sel_orders = dict()
            for o in s.mdb[o_col].find({'status': {'$in': ['Open', 'Partial Filled']}}):
                o['pending_quantity'] = o['order_quantity'] - o['trade_quantity']
                if o['direction'] == 'buy':
                    try:
                        buy_orders[o['order_price']].append(o)
                    except KeyError:
                        buy_orders[o['order_price']] = [o]
                elif o['direction'] == 'sell':
                    try:
                        sel_orders[o['order_price']].append(o)
                    except KeyError:
                        sel_orders[o['order_price']] = [o]
                else:
                    move_to_error(o, 'direction should be either buy, or sell')

            for k in buy_orders:
                if len(buy_orders[k]) > 1:
                    buy_orders[k] = sorted(buy_orders[k], key=lambda e: e['ts'])

            for k in sel_orders:
                if len(sel_orders[k]) > 1:
                    sel_orders[k] = sorted(sel_orders[k], key=lambda e: e['ts'])

            sorted_buy_orders = sorted(buy_orders, reverse=True)  # dsc
            sorted_sel_orders = sorted(sel_orders, reverse=False) # asc
            print(f"len(sorted_buy_orders)={len(sorted_buy_orders)}, len(sorted_sel_orders)={len(sorted_sel_orders)}")
            s.log.info(f"len(sorted_buy_orders)={len(sorted_buy_orders)}, len(sorted_sel_orders)={len(sorted_sel_orders)}")
            if (len(sorted_buy_orders) == 0) or (len(sorted_sel_orders) == 0): # save this data onto mongodb as order_book for visualisation
                break

            top_buy_price = sorted_buy_orders.pop(0) # shift. Removes first element. Element at index 0 is removed/poped out
            top_sel_price = sorted_sel_orders.pop(0) # shift. Removes first element. Element at index 0 is removed/poped out

            top_buy_order = buy_orders[top_buy_price].pop(0)
            top_sel_order = sel_orders[top_sel_price].pop(0)
            print(f"stock_id={stock_id}, top_buy_price = {top_buy_price}, top_sel_price = {top_sel_price}")
            s.log.info(f"stock_id={stock_id}, top_buy_price = {top_buy_price}, top_sel_price = {top_sel_price}")
            while top_buy_price >= top_sel_price:
                print(f"transacting orders for -- stock_id={stock_id}, top_buy_price = {top_buy_price}, top_sel_price = {top_sel_price}")
                s.log.info(f"transacting orders for -- stock_id={stock_id}, top_buy_price = {top_buy_price}, top_sel_price = {top_sel_price}")
                if top_buy_order['pending_quantity'] >= top_sel_order['pending_quantity']:
                    sel_order_status = 'Filled'
                    buy_order_status = 'Filled' if top_buy_order['pending_quantity'] == top_sel_order['pending_quantity'] else 'Partial Filled'

                    trade_id = f"{trade_id_partial}.{trade_counter:08}"
                    trade_counter = trade_counter + 1
                    s.trade(mgh = s.mgh,
                                  mdb = s.mdb,
                                  stock_id = stock_id,
                                  trade_id = trade_id,
                                  buy_order_id=top_buy_order['order_id'],
                                  sel_order_id=top_sel_order['order_id'],
                                  trade_quantity=top_sel_order['pending_quantity'],
                                  trade_price=top_sel_price, # sell price is considered as trade price
                                  buy_order_status=buy_order_status,
                                  sel_order_status=sel_order_status
                                 )

                    if top_buy_order['pending_quantity'] == top_sel_order['pending_quantity']:
                        top_buy_order = buy_orders[top_buy_price].pop(0) if len(buy_orders[top_buy_price]) else None

                    top_sel_order = sel_orders[top_sel_price].pop(0) if len(sel_orders[top_sel_price]) else None

                else:
                    sel_order_status = 'Partial Filled'
                    buy_order_status = 'Filled'
                    trade_id = f"{trade_id_partial}.{trade_counter:08}"
                    trade_counter = trade_counter + 1
                    s.trade(mgh = s.mgh, mdb = s.mdb,
                                  stock_id = stock_id,
                                  trade_id = trade_id,
                                  buy_order_id=top_buy_order['order_id'],
                                  sel_order_id=top_sel_order['order_id'],
                                  trade_quantity=top_buy_order['pending_quantity'],
                                  trade_price=top_sel_price, # sell price is considered as trade price
                                  buy_order_status=buy_order_status,
                                  sel_order_status=sel_order_status
                                 )
                    top_buy_order = buy_orders[top_buy_price].pop(0) if len(buy_orders[top_buy_price]) else None

                if top_buy_order is None:
                    if len(sorted_buy_orders):
                        top_buy_price = sorted_buy_orders.pop(0)
                        top_buy_order = buy_orders[top_buy_price].pop(0)
                    else: # No more buy orders
                        break

                if top_sel_order is None:
                    if len(sorted_sel_orders):
                        top_sel_price = sorted_sel_orders.pop(0)
                        top_sel_order = sel_orders[top_sel_price].pop(0)
                    else: # No more sell orders
                        break
            s.save_order_book(stock_id, sorted_buy_orders, sorted_sel_orders)  # save this data onto mongodb as order_book for visualisation
        print(f"stopping -- order matching engine/thread for stock={stock_id} -- processed = {trade_counter} trades")
        s.log.info(f"stopping -- order matching engine/thread for stock={stock_id} -- processed = {trade_counter} trades")

# -------------------------------------
# Thread
# -------------------------------------
    def ensure_order_matching_engine_is_running(s, stock_id):
        print(f"list of running threads = {[x for x in threading.enumerate() if 'oms_for_' in x.name]}")
        s.log.info(f"list of running threads = {[x for x in threading.enumerate() if 'oms_for_' in x.name]}")
        if stock_id in s.stock_to_oms_thread_mapping and s.stock_to_oms_thread_mapping[stock_id].is_alive(): return # all good. oms thread for stock is already running.
        x = threading.Thread(target=s.order_matching_engine, args=(stock_id,))
        x.name = f"oms_for_{stock_id}"
        s.stock_to_oms_thread_mapping[stock_id] = x
        x.start()
        # x.join()
        print(f"started oms thread for {stock_id}")
        s.log.info(f"started oms thread for {stock_id}")

    # --------------------------------------------------------------------------------------------------------
    # Save every new order into mongodb collection name = order
    # --------------------------------------------------------------------------------------------------------
    def push_order(s, json_object):
        result = list()
        for row in json_object:
            stock_id = row['stock_id']
            del row['stock_id']
            print("aaaaaaaaaa")
            print(row)
            print("ooooooooooooooooo")
            m_obj = f"stock.order.{stock_id}" # collection
            try:
                s.mdb.validate_collection(m_obj) # We need to check if order table exist, else mongo db will create by default -- which is bad.
                r = s.mdb.stock.order[stock_id].bulk_write([mg.InsertOne({
                    'order_id': row['order_id'],
                    'account_id' : row['account_id'],
                    'direction'  : row['direction'],
                    'order_quantity' : row['order_quantity'],
                    'order_price' : float(row['order_price']), # input json_object has order_price as string and not float .. since, when it was float, input "order_price": 222.10 --> Resulted into 'order_price': 222.10000610351562 --> Hence not using float in input JSON schema.
                    'trade_quantity': 0, # should always be 0 initially. # overwrite(ignore) any kachara/noise coming in row
                    'status' : 'Open', #
                    'ts'     : time.time() # dt.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                    })]
                    )
                print(f"return value {r}")
            except mg.errors.OperationFailure as e:
                r = f"failed to push order for stock={stock_id}. Exception = {e}"
                print(r)
    #             raise Exception(message)
            except Exception as e:
                r = f"failed to push order for stock={stock_id}. Exception = {e}"
                print(r)
    #             raise Exception(message)
            result.append(r)
            s.ensure_order_matching_engine_is_running(stock_id)
        return result