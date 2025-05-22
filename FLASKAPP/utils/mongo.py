from pymongo import MongoClient

# Connexion à la base MongoDB locale (modifie si tu as une URL distante)
client = MongoClient("mongodb://localhost:27017/")

# Base de données et collection
db = client["avis_amazon"]
collection = db["predictions"]

def get_sentiment_counts():
    pipeline = [
        {"$group": {"_id": "$sentiment", "total": {"$sum": 1}}}
    ]
    results = collection.aggregate(pipeline)

    # Initialisation
    counts = {"positif": 0, "neutre": 0, "negatif": 0}
    for r in results:
        sentiment = r["_id"]
        if sentiment in counts:
            counts[sentiment] = r["total"]
    return counts
