from flask import Blueprint, render_template, jsonify, request, Response
from pymongo import MongoClient
import csv
import io

bp = Blueprint('routes', __name__)
bootstrap_servers = ['localhost:9092']

# Kafka topic to produce messages to
topic_name = 'amazon_reviews'  # match your Kafka topic

# MongoDB connection (your project DB + collection)
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['amazon']
collection = db['sentiments']


# --- Pages Front-End ---
@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@bp.route("/predict")
def predict():
    return render_template("predict.html")

@bp.route("/live")
def live():
    return render_template("live.html")

@bp.route("/history")
def history():
    return render_template("history.html")


# --- API JSON ---

# Compteur global
@bp.route("/api/stats")
def api_stats():
    pipeline = [{"$group": {"_id": "$predicted_sentiment", "total": {"$sum": 1}}}]
    result = list(collection.aggregate(pipeline))
    print("Aggregation result:", result)  # Debug print
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for r in result:
        counts[r["_id"]] = r["total"]
    return jsonify(counts)



# Courbe par date
@bp.route("/api/stats-by-date")
def stats_by_date():
    pipeline = [
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "total": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    return jsonify(list(collection.aggregate(pipeline)))


# Score moyen par ASIN
@bp.route("/api/overall-distribution")
def overall_distribution():
    pipeline = [
        {
            "$group": {
                "_id": "$overall",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}  # Sort by score from 1 to 5
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)

# Répartition sentiments
@bp.route("/api/sentiment-pie")
def sentiment_pie():
    pipeline = [
        {
            "$group": {
                "_id": "$predicted_sentiment",  # Use your actual sentiment field name
                "count": {"$sum": 1}
            }
        }
    ]
    results = list(collection.aggregate(pipeline))
    return jsonify(results)

# Derniers avis
@bp.route("/api/recent")
def api_recent():
    docs = collection.find().sort("created_at", -1).limit(5)
    result = []
    for d in docs:
        result.append({
            "date": d.get("created_at", ""),
            "text": d.get("reviewText", ""),
            "sentiment": d.get("predicted_sentiment", ""),
        })
    return jsonify(result)

# Prédiction IA simulée
@bp.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json()
    texte = data.get("text", "").lower()
    if "bon" in texte or "excellent" in texte:
        sentiment = "positif"
    elif "mauvais" in texte or "nul" in texte:
        sentiment = "négatif"
    else:
        sentiment = "neutre"
    return jsonify({"sentiment": sentiment})

# Historique complet
@bp.route("/api/history")
def api_history():
    docs = collection.find().sort("date", -1)
    result = []
    for d in docs:
        result.append({
            "date": d.get("date", ""),
            "asin": d.get("asin", ""),
            "text": d.get("text", ""),
            "sentiment": d.get("sentiment", ""),
            "score": d.get("score", 0)
        })
    return jsonify(result)

# Export CSV
@bp.route("/api/export")
def export_csv():
    docs = collection.find()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "asin", "text", "sentiment", "score"])
    for d in docs:
        writer.writerow([
            d.get("date", ""), d.get("asin", ""),
            d.get("text", ""), d.get("sentiment", ""), d.get("score", 0)
        ])
    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=historique_predictions.csv"})

@bp.route("/api/reviews")
def api_reviews():
    docs = collection.find().sort("created_at", -1).limit(10)
    result = []
    for d in docs:
        result.append({
            "created_at": d.get("created_at", ""),
            "reviewText": d.get("reviewText", ""),
            "predicted_sentiment": d.get("predicted_sentiment", ""),
            "overall": d.get("overall", ""),
        })
    return jsonify(result)


