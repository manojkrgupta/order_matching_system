import os
import time
import logging
from pyspark.sql import SparkSession
from pyspark.streaming import StreamingContext
from pyspark.sql.types import *
from pyspark.sql.functions import *
# import config
from mango import Mango

os.environ['PYSPARK_SUBMIT_ARGS']='--packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.2,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2 pyspark-shell'

# below two lines does not connect to cluster
#spark = SparkSession.builder.appName("Order Management System for apple").getOrCreate() # does not connect to cluster
#spark = SparkSession.builder.master("local").appName("Order Management System for apple").getOrCreate() # does not connect to cluster

spark = SparkSession.builder.master("spark://smaster:7077").appName("Order Management System for apple").getOrCreate() # connects to cluster

log4j_logger = spark._jvm.org.apache.log4j
log = log4j_logger.LogManager.getLogger("OMS") # order_management_system
# log = logging.getLogger('pyspark')
log.info("My test info statement")
# config.log = log # share the logger to all class objects
m = Mango()

# --------------------------------------------------------------------------------------------------------------
# An experiment with Spark DataFrame
# --------------------------------------------------------------------------------------------------------------
# df = spark.createDataFrame([
#     {"order_id": "223322334222.122322", "account_id": "user1", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy"},
#     {"order_id": "323322334222.122322", "account_id": "user2", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy"},
#     {"order_id": "423322334222.122322", "account_id": "user3", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy"},
#     {"order_id": "523322334222.122322", "account_id": "user4", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy"}
# ])
# df.show()
# df.toJSON().foreach(lambda l:print(f"{type(l)} == {l}"))
# df.foreach(lambda l : print(l.asDict()))
# --------------------------------------------------------------------------------------------------------------
def push_order(obj):
    log.info(f"order input {obj}")

# --------------------------------------------------------------------------------------------------------------
# Important information
# --------------------------------------------------------------------------------------------------------------
# Situation 1 : When input is blank -- it comes as None
# --------------------------------------------------------------------------------------------------------------
# Situation 2 : When input is malformed - when input json is broken or malformed -- it turns like None for all the columns
# Example :
#   Input :
#         example 1 = {"order_id": "123322334222.122322", "account_id": "user1", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy",
#         example 2 = {}
#   Output :
#         {'account_id': None, 'stock_id': None, 'order_quantity': None, 'order_price': None, 'direction': None}
# --------------------------------------------------------------------------------------------------------------
# Situation 3 : When input has extra - the extra attribute is ignored
# Example :
#   Input: {"order_id": "123322334222.122322", "account_id": "user1", "stock_id": "apple", "order_quantity": 10, "order_price": 222.10, "direction": "buy", 'extra': 1222}
#   Ouput: {'account_id': 'user1', 'stock_id': 'apple', 'order_quantity': 10, 'order_price': 222.10000610351562, 'direction': 'buy'}
# --------------------------------------------------------------------------------------------------------------
def process_line_by_line(*args):
    log.info(f"message from kafka q == {args}")
    df = args[0]
#     print(f"arguments --> {args} --> {len(args)} --> {args[0]} --> {type(args[0])}")
#     df.show()
#     obj = list()
#     df.foreach(lambda l : print(f"yahoooo --- {type(l)} -- {l.asDict().get('value')}")) # yahoooo --- <class 'pyspark.sql.types.Row'> -- {'value': Row(account_id='user1', stock_id='apple', order_quantity=10, order_price=222.10000610351562, direction='buy')}

# Below does not work
#     df.foreach(lambda l : obj.append(l.asDict().get('value'))) # Does not work

# Below also does not work
#     process_line_udf = udf(lambda a: process_line(a))
#     df.foreach(process_line_udf) # Does not work

# Below also does not work
#     process_line([o.asDict() for o in obj])
#     df.foreach(lambda l : push_order(l['value'].asDict()))

    obj = df.rdd.map(lambda x: x['value']).filter(lambda x: x is not None).map(lambda x: x.asDict()).collect()
    print(f"{obj}")
    if len(obj):
        m.push_order(obj)

json_schema = StructType([
    StructField("order_id", StringType()),
    StructField("account_id", StringType()),
    StructField("stock_id", StringType()),
    StructField("order_quantity", IntegerType()),
#     StructField("order_price", FloatType()), --> Input was "order_price": 222.10 --> Resulted into 'order_price': 222.10000610351562 --> Hence not using float
    StructField("order_price", StringType()),
    StructField("direction", StringType())
])

kafka_options = {
    "kafka.bootstrap.servers": "kafka1:9092",
    # "kafka.sasl.mechanism": "SCRAM-SHA-256",
    # "kafka.security.protocol": "SASL_SSL",
    # "kafka.sasl.jaas.config": """org.apache.kafka.common.security.scram.ScramLoginModule required username="XXX" password="YYY";""",
#     "startingOffsets": "earliest", # Start from the beginning when we consume from kafka
    "startingOffsets": "latest", # Start from the latest
    "subscribe": "stockorder"           # Our topic name
}

df = spark.readStream.format("kafka").options(**kafka_options).load()

# Transform to Output DataFrame
value_df = df.select(from_json(col("value").cast("string"),json_schema).alias("value"))
log.info("yahoooooooo")
value_df.printSchema()
query = value_df.writeStream.outputMode("append").format("console").foreachBatch(process_line_by_line).start()

# time.sleep(10)
query.awaitTermination()

