from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, IntegerType

# 1. Load saved model
print("Loading model...")
model = PipelineModel.load(r"C:\Users\HP\Documents\bigdata\Projet\consumer\logistic_model_only")
print("Model loaded successfully")
# 2. Create Spark session with MongoDB connector
spark = SparkSession.builder \
    .appName("KafkaSparkStreaming") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
    .config("spark.mongodb.output.uri", "mongodb://localhost:27017/amazon.sentiments") \
    .getOrCreate()

# 3. Define schema of incoming Kafka JSON
schema = StructType() \
    .add("reviewText", StringType()) \
    .add("label", IntegerType())  # Optional if you're sending ground truth

# 4. Read from Kafka topic
df_kafka_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "amazon_reviews") \
    .option("startingOffsets", "latest") \
    .load()

# 5. Extract value and parse JSON
df_kafka = df_kafka_raw.selectExpr("CAST(value AS STRING) as json_str") \
    .select(from_json(col("json_str"), schema).alias("data")) \
    .select("data.*")

# 6. Apply prediction model
df_predictions = model.transform(df_kafka)

# 7. Select useful output
df_output = df_predictions.select("reviewText", "prediction")

# 8. Write to MongoDB
df_output.writeStream \
    .format("mongodb") \
    .outputMode("append") \
    .option("checkpointLocation", "./checkpoint") \
    .start() \
    .awaitTermination()
