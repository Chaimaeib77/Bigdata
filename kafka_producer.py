from kafka import KafkaProducer
import pandas as pd
import json
import time

# Load your cleaned CSV with extra columns if available
df = pd.read_csv("cleaned_amazon_reviews.csv")

# Select relevant columns; add any additional columns you want to send
# Make sure these columns exist in your CSV or remove those you don't have
columns_to_send = ['reviewText', 'label','overall']
# Some columns might not exist; filter them out
columns_to_send = [col for col in columns_to_send if col in df.columns]

# Limit the number of rows to send
df = df[columns_to_send].dropna(subset=['reviewText']).sample(50, random_state=42)  # send 50 random reviews

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic = 'amazon_reviews'

# Send each review one at a time
for index, row in df.iterrows():
    # Build message dict from available columns
    message = {col: row[col] for col in columns_to_send}
    
    print(f"📤 Sending message: {message}")
    producer.send(topic, message)
    time.sleep(1)  # wait 1 second between messages

producer.flush()
print("✅ All messages sent.")
