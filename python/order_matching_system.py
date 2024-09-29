from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from datetime import datetime, timedelta
import logging
import time
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import expr
from pyspark.sql.functions import avg
from pyspark.sql.functions import window
from pyspark.sql import SparkSession
from datetime import datetime, timedelta
from pyspark.sql.functions import *
from pyspark.sql.types import *
import time
import os
from pyspark.sql import SQLContext
import mango

os.environ['PYSPARK_SUBMIT_ARGS']='--packages org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.2,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.2 pyspark-shell'

spark = SparkSession.builder \
    .appName("Order Management System for apple") \
    .getOrCreate()

log4j_logger = spark._jvm.org.apache.log4j
log = log4j_logger.LogManager.getLogger("OMS") # order_matching_system
# log = logging.getLogger('pyspark')

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
def process_line(d):
    d = line.asDict()
    log.info(f"yahooo {d}")
#     if d.get('value') is not None: # when input is not blank
#         order = d['value'].asDict()
#         if order.get('order_id') is not None:
#             log.info(f"processing order {order}")


from pyspark.sql.functions import udf


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
        mango.push_order(obj)

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
    "startingOffsets": "earliest", # Start from the beginning when we consume from kafka
    "subscribe": "apple"           # Our topic name
}

df = spark.readStream.format("kafka").options(**kafka_options).load()

# Transform to Output DataFrame
value_df = df.select(from_json(col("value").cast("string"),json_schema).alias("value"))
log.info("yahoooooooo")
value_df.printSchema()
query = value_df.writeStream.outputMode("append").format("console").foreachBatch(process_line_by_line).start()

# time.sleep(10)
query.awaitTermination()



# value_df.printSchema()
#
# exploded_df = value_df.selectExpr('value.row_id', 'value.res_id', 'value.name', 'value.cuisines',
#                                   'value.location.zipcode as zipcode',
#                                   'explode(value.user_ratings) as usr_ratings')
#

# exploded_df.printSchema()

# flattened_df = exploded_df \
#     .withColumn('rowid', concat(col('row_id'), col('res_id'), col('usr_ratings.user_id'))) \
#     .withColumn('rating_text',expr('usr_ratings.rating_text')) \
#     .withColumn('user_id',expr('usr_ratings.user_id')) \
#     .withColumn('rating',expr('usr_ratings.rating')) \
#     .drop('usr_ratings') \
#     .drop('row_id')

# flattened_df.printSchema()

# Write to Sink
# output_query = flattened_df.writeStream \
#     .format("csv") \
#     .option("path","hdfs://localhost:9000/user/hive/restaurants") \
#     .option("checkpointLocation", "chck-pnt-dir-kh") \
#     .outputMode("append") \
#     .queryName("Flattened Invoice Writter") \
#     .start()
#
# output_query.awaitTermination()


# Deserialize the value from Kafka as a String for now
# deserialized_df = df.selectExpr("CAST(value AS STRING)")

# Subscribe to Kafka topic "hello"

# Create a DStream that will connect to hostname:port, like localhost:9999
# lines = ssc.socketTextStream("localhost", 9999)

# Deserialize the value from Kafka as a String for now
# deserialized_df = df.selectExpr("CAST(value AS STRING)")

# Query Kafka and wait 10sec before stopping pyspark
# query = deserialized_df.writeStream.outputMode("append").format("console").start()
# time.sleep(10)
# query.awaitTermination()


# Split each line into words
# words = lines.flatMap(lambda line: line.split(" "))

# Count each word in each batch
# pairs = words.map(lambda word: (word, 1))
# wordCounts = pairs.reduceByKey(lambda x, y: x + y)

# Print the first ten elements of each RDD generated in this DStream to the console
# wordCounts.pprint()

# spark.start()           # Start the computation
# spark.awaitTermination()  # Wait for the computation to terminate