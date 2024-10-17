import os
import json
import random
import logging
import pymongo as mg
from kafka import KafkaProducer

kafka_topic = 'stockorder'
stocks = ['apple', 'amazon', 'zoomato', 'ibm'] # do not change the index, it will lead to change in kafka partition
account  = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6']

producer = KafkaProducer(bootstrap_servers='localhost:29092') # kafka1:29092, kafka2:29093, kafka3:29094
topic_list = producer.partitions_for(kafka_topic) # Returns set of all known partitions for the topic.
stock_to_partition_map = {s: stocks.index(s) % len(topic_list) for s in stocks} # order for one stock should go to one particular partition

mgh = mg.MongoClient(f"mongodb://admin:admin@localhost:27017/")
mdb = mgh["order_matching_system"]

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)

def random_orders(n=10000):

    pid = os.getpid() # pid
    rid = random.randrange(10000) # random run id -- from 0 to 9999 -- max 4 digit
    order_id_partial = f"{pid:06}.{rid:04}"
    for i in range(n): # max 2digit
        o_id = f"{order_id_partial}.{i:04}"
        a_id = random.choice(account)
        s_id = random.choice(stocks)
        q    = random.randrange(10, 100)
#         p    = random.randrange(22000, 22200) / 100    # from 220.00, 220.01, 220.02 .... till ... 221.99
        p    = random.randrange(22000, 22200, 5) / 100 # from 220.00, 220.05, 220.10 .... till ... 221.95
        d    = 'sell' if random.randrange(2) == 1 else 'buy'
        order = dict(order_id=o_id, account_id=a_id, stock_id=s_id, order_quantity=q, order_price=p, direction=d)
        future = producer.send(kafka_topic, str.encode(json.dumps(order)), partition=stock_to_partition_map[s_id])
        result = future.get(timeout=3)
        print(result)
        print(order)
    producer.flush()

random_orders(1000)