import findspark
findspark.init()

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType
from pyspark.ml import PipelineModel


# Windows environment setup (edit if needed)
os.environ["JAVA_HOME"] = "C:/Program Files/Java/jdk-17"
os.environ["HADOOP_HOME"] = "C:/hadoop"

# 1. Load saved Spark ML pipeline model
from pathlib import Path
model_path = Path.cwd() / "Logistic_Regression_best_model"
model = PipelineModel.load("file:///" + str(model_path).replace("\\", "/"))


# 2. Start Spark session with MongoDB connector
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingSentiment") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/amazon.sentiments") \
    .config("spark.hadoop.hadoop.native.lib", "false") \
    .config("spark.driver.extraJavaOptions", "-Dhadoop.native.lib=false") \
    .getOrCreate()



# 3. Define expected schema for Kafka JSON input
schema = StructType().add("reviewText", StringType())

# 4. Read stream from Kafka topic
df_kafka_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "amazon_reviews") \
    .option("startingOffsets", "latest") \
    .load()

# 5. Extract and parse JSON from Kafka message
df_kafka = df_kafka_raw.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.reviewText") \
    .filter(col("reviewText").isNotNull()) \
    .filter(col("reviewText") != "")

# 6. Apply the trained model
df_predictions = model.transform(df_kafka)

# 7. Select output: review + prediction
df_output = df_predictions.select("reviewText", "prediction")

# 8. Write output to MongoDB
df_output.writeStream \
    .format("mongodb") \
    .outputMode("append") \
    .option("checkpointLocation", "./checkpoint") \
    .start() \
    .awaitTermination()
