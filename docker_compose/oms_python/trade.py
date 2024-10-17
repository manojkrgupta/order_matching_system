# import config
import logging
import pymongo as mg
import datetime as dt

class Trade:
    def __init__(s, mongodb_transaction=False):
#      logger = logging.getLogger("uvicorn.error")
       logger = logging.getLogger("OMS")
       logger.setLevel(logging.DEBUG)
       s.log = logger
#        s.log = config.log
       s.mongodb_transaction = mongodb_transaction
       print(f"mongodb_transaction enabled ? {mongodb_transaction}")
       s.trade = s.fill_quantity_with_transaction if s.mongodb_transaction else s.fill_quantity_without_transaction

    # ------------------------------------------------------------------------------------------------------
    # Supporting function for threads main job
    # ------------------------------------------------------------------------------------------------------
    def fill_quantity_without_transaction(s, mgh, mdb, stock_id, trade_id, buy_order_id, sel_order_id, trade_quantity, trade_price, buy_order_status, sel_order_status):
        r1 = None
        r2 = None
        r3 = None
        print(f"transacting without transaction -- buy_order_id={buy_order_id} with sel_order_id={sel_order_id} for trade_quantity={trade_quantity} at trade_price={trade_price}. buy_order_status={buy_order_status}, sel_order_status={sel_order_status}")
        try:
            r1 = mdb.stock.trade[stock_id].insert_one({
                    'trade_id': trade_id,
                    'buy_order_id': buy_order_id,
                    'sel_order_id': sel_order_id,
                    'trade_quantity': trade_quantity,
                    'trade_price': trade_price,
                    'ts': dt.datetime.now(),
                })

            r2 = mdb.stock.order[stock_id].update_one(
                    {'order_id': buy_order_id,
                     'order_quantity': {'$gte' : trade_quantity},
                     'order_price'   : {'$gte' : trade_price   }, # ask buy price is greater then equal to trade price (paying less is fine)
                    },
                    {
                        '$inc' : { 'trade_quantity': trade_quantity},
                        '$set' : { 'status' : buy_order_status}
                    })

            r3 = mdb.stock.order[stock_id].update_one(
                    {'order_id': sel_order_id,
                     'order_quantity': {'$gte': trade_quantity},
                     'order_price'   : {'$lte': trade_price   }, # ask sel price is less then equal to trade price (getting more price is fine)
                    },
                    {
                        '$inc' : { 'trade_quantity': trade_quantity},
                        '$set' : { 'status' : sel_order_status}
                    })

        except mg.errors.OperationFailure as e:
            r1 = f"failed to transact order for stock={stock_id}. Exception = {e}"
            s.log.error(r1)
    #             raise Exception(message)
        except Exception as e:
            r1 = f"failed to transact order for stock={stock_id}. Exception = {e}"
            s.log.error(r1)
    #             raise Exception(message)
        return([r1, r2, r3])

# ------------------------------------------------------------------------------------------------------
    #
    # ------------------------------------------------------------------------------------------------------
    def fill_quantity_with_transaction(s, mgh, mdb, stock_id, trade_id, buy_order_id, sel_order_id, trade_quantity, trade_price, buy_order_status, sel_order_status):
        def callback_wrapper(session):
            return s.mango_transaction(session, mgh, mdb, stock_id, trade_id, buy_order_id, sel_order_id, trade_quantity, trade_price, buy_order_status, sel_order_status)

        with mgh.start_session() as session:
            session.with_transaction(callback_wrapper)
    # ------------------------------------------------------------------------------------------------------
    # Using Transactions in Mongodb
    # But this needs Replica Instance of MongoDB (standalone is not enough, and it gives error --> OperationFailure: Transaction numbers are only allowed on a replica set member or mongos, full error: {'ok': 0.0, 'errmsg': 'Transaction numbers are only allowed on a replica set member or mongos', 'code': 20, 'codeName': 'IllegalOperation'}
    # ------------------------------------------------------------------------------------------------------
    def mango_transaction(s, session, mgh, mdb, stock_id, trade_id, buy_order_id, sel_order_id, trade_quantity, trade_price, buy_order_status, sel_order_status):
        r1 = None
        r2 = None
        r3 = None
        print(f"transacting with transaction -- buy_order_id={buy_order_id} with sel_order_id={sel_order_id} for trade_quantity={trade_quantity} at trade_price={trade_price}. buy_order_status={buy_order_status}, sel_order_status={sel_order_status}")
        try:
            r1 = mdb.stock.trade[stock_id].insert_one({
                    'trade_id': trade_id,
                    'buy_order_id': buy_order_id,
                    'sel_order_id': sel_order_id,
                    'trade_quantity': trade_quantity,
                    'trade_price': trade_price,
                    'timestamp': 'new Date()',
                }, session=session)

            r2 = mdb.stock.order[stock_id].update_one(
                    {'order_id': buy_order_id,
                     'order_quantity': {'$gte' : trade_quantity},
                     'order_price'   : {'$gte' : trade_price   }, # ask buy price is greater then equal to trade price (paying less is fine)
                    },
                    {
                        '$inc' : { 'trade_quantity': trade_quantity},
                        '$set' : { 'status' : buy_order_status}
                    }, session=session)

            r3 = mdb.stock.order[stock_id].update_one(
                    {'order_id': sel_order_id,
                     'order_quantity': {'$gte': trade_quantity},
                     'order_price'   : {'$lte': trade_price   }, # ask sel price is less then equal to trade price (getting more price is fine)
                    },
                    {
                        '$inc' : { 'trade_quantity': trade_quantity},
                        '$set' : { 'status' : sel_order_status}
                    }, session=session)

        except mg.errors.OperationFailure as e:
            r1 = f"failed to transact order for stock={stock_id}. Exception = {e}"
            s.log.error(r1)
    #             raise Exception(message)
        except Exception as e:
            r1 = f"failed to transact order for stock={stock_id}. Exception = {e}"
            s.log.error(r1)
    #             raise Exception(message)
        return([r1, r2, r3])

