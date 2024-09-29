import logging
import pymongo as mg
import datetime as dt
from config import mango_conf

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
mgh = mg.MongoClient(f"mongodb://{mango_conf.root_user}:{mango_conf.root_pass}@{mango_conf.url}/")
mdb = mgh["order_matching_system"]

# -------------------------------------
# Initialise in Mongo DB
# -------------------------------------
# // Stock Table (Collections/Structures)
# db.createCollection('stock');
# db.stock.ensureIndex({'stock_id': 1}, {unique: true}); // create unique constraint
# db.stock.insertOne({'stock_id': 'apple'  , 'short': 'Apple Inc'  , 'isin': 'US0378331005', 'status': 'Active'})
#
# // Accounts Table
# db.createCollection('account');
# db.account.ensureIndex({'account_id': 1}, {unique: true}); // create unique constraint
# db.account.insertOne({'account_id': 'user1', 'name': 'User One'  , 'broker': 'Zerodha', 'CDSL' : '12341', 'segment': ['Equity', 'Derivatives']})
#
# // Stock Order Table
# db.createCollection('stock.order.apple');
# db.stock.order.apple.ensureIndex({'order_id': 1}, {unique: true}); // create unique constraint
#
# // Stock Audit Table (dropped from original plan)
# //db.createCollection('stock.audit.apple');
# //db.stock.audit.apple.ensureIndex({'order_id': 1, 'status': 1, 'trade_quantity': 1, 'trade_price': 1, 'timestamp': 1}, {unique: true}); // create unique constraint
#
# // Stock Trade Table
# db.createCollection('stock.trade.apple')
# db.stock.trade.apple.ensureIndex({'trade_id': 1}, {unique: true}); // create unique constraint

# Atomic operation in Mongodb
# --------------------------------
# for every new order :
#     db.stock.order.apple.insertOne({
#     'order_id': '20240914115432.222.user1',
#     'account_id': 'user1',
# //  'stock_id' : 'apple', // present in the incoming message, but is not in the order table since there is one order table for every stock_id
#     'direction' : 'buy',
#     'order_quantity' : 10,
#     'order_price' : 222,
#     'trade_quantity': 0,
# //    'trade_price' : 0, // this place is more for an average trade price then trade price. Let the calculation for average trade price come from trade table during reporting and not during trade execution
#     'status' : 'Open',
#     })

# --------------------------------------------------------------------------------------------------------
#
# --------------------------------------------------------------------------------------------------------
def push_order(json_object):
    result = list()
    for row in json_object:
        stock_table = row['stock_id']
        del row['stock_id']
        m_obj = f"stock.order.{stock_table}" # collection
        try:
            mdb.validate_collection(m_obj) # We need to check if order table exist, else mongo db will create by default -- which is bad.
            r = mdb.stock.order[stock_table].bulk_write([mg.InsertOne({
                'order_id': row['order_id'],
                'account_id' : row['account_id'],
                'direction'  : row['direction'],
                'order_quantity' : row['order_quantity'],
                'order_price' : row['order_price'],
                'trade_quantity': 0, # should always be 0 initially. # overwrite(ignore) any kachara/noise coming in row
                'status' : 'Open', #
                'ts'     : dt.datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                })]
                )
            logging.info(f"return value {r}")
        except mg.errors.OperationFailure as e:
            r = f"failed to push order for stock={stock_table}. Exception = {e}"
            logger.error(r)
#             raise Exception(message)
        except Exception as e:
            r = f"failed to push order for stock={stock_table}. Exception = {e}"
            logger.error(r)
#             raise Exception(message)
        result.append(r)
    return result



