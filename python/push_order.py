import os
import json
import random
import logging
import pymongo as mg
from kafka import KafkaProducer

def random_orders(n=1000):
    stocks = ['apple', 'amazon', 'zoomato']
    account  = ['a1', 'a2', 'a3', 'a4']

    pid = os.getpid() # pid
    rid = random.randrange(10000) # random run id -- from 0 to 9999 -- max 4 digit
    order_id_partial = f"{pid:06}.{rid:04}"
    for i in range(n): # max 2digit
        o_id = f"{order_id_partial}.{i:04}"
        a_id = random.choice(account)
        s_id = random.choice(stocks)
        q    = random.randrange(10, 100)
        p    = random.randrange(22200, 23000) / 100 # from 222.00 to 229.99
        d    = 'sell' if random.randrange(2) == 1 else 'buy'
        order = dict(order_id=o_id, account_id=a_id, stock_id=s_id, order_quantity=q, order_price=p, direction=d)
        future = producer.send('apple', str.encode(json.dumps(order)))
        result = future.get(timeout=3)
        print(result)
        print(order)
    producer.flush()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)
mgh = mg.MongoClient(f"mongodb://admin:admin@localhost:27017/")
mdb = mgh["order_matching_system"]

producer = KafkaProducer(bootstrap_servers='localhost:29092') # kafka1:29092, kafka2:29093, kafka3:29094

random_orders(10000)