from kafka import KafkaConsumer
from json import loads
from pymongo import MongoClient
from pyspark.ml import PipelineModel
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import StringType
import re
import datetime
import logging
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AmazonReviewConsumer")

# Initialize Spark session
spark = SparkSession.builder \
    .appName("AmazonReviewStreaming") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# Load trained Spark model
model = PipelineModel.load("Logistic_Regression_best_model")

# MongoDB connection
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['amazon']
collection = db['sentiments']

# Kafka Consumer config
consumer = KafkaConsumer(
    'amazon_reviews',
    group_id='amazon_consumer_group',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda x: loads(x.decode('utf-8'))
)

# Text cleaner
def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    emoji_pattern = re.compile("[" u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF" "]+", flags=re.UNICODE)
    text = emoji_pattern.sub(r'', text)
    return text.strip()

# Label to sentiment string
def pred_to_sentiment(prediction):
    mapping = {0: "Negative", 1: "Neutral", 2: "Positive"}
    return mapping.get(int(prediction), "Unknown")

pred_to_sentiment_udf = udf(pred_to_sentiment, StringType())

# Main logic
def consume_and_predict():
    for message in consumer:
        try:
            data = message.value
            if not isinstance(data, dict) or 'reviewText' not in data:
                logger.warning("❗ Invalid message skipped.")
                continue

            review_text = data.get('reviewText', '')
            if not review_text.strip():
                logger.warning("⚠️ Empty review skipped.")
                continue

            cleaned_text = clean_text(review_text)
            df = spark.createDataFrame([(cleaned_text,)], ['reviewText'])

            prediction_df = model.transform(df)
            prediction_df = prediction_df.withColumn("predicted_sentiment", pred_to_sentiment_udf(col("prediction")))
            row = prediction_df.select("prediction", "predicted_sentiment").first()

            document = {
                'reviewText': review_text,
                'cleanedReview': cleaned_text,
                'predicted_label': int(row['prediction']),
                'predicted_sentiment': row['predicted_sentiment'],
                'summary': data.get('summary'),
                'overall': data.get('overall'),
                'label': data.get('label'),
                'created_at': datetime.datetime.utcnow()
            }

            document = {k: v for k, v in document.items() if v is not None}  # Clean nulls

            collection.insert_one(document)
            logger.info(f"✅ Inserted: {document['predicted_sentiment']} - {review_text[:60]}...")

        except Exception as e:
            logger.error("❌ Error occurred:")
            traceback.print_exc()

if __name__ == "__main__":
    consume_and_predict()