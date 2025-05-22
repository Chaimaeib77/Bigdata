# from flask import Blueprint, jsonify
# from pymongo import MongoClient
# from flask import request

# bp = Blueprint('routes', __name__)
# client = MongoClient("mongodb://localhost:27017/")
# collection = client["avis_amazon"]["predictions"]

# # 1. 📈 Graphes des prédictions par date
# @bp.route('/api/stats-by-date')
# def stats_by_date():
#     pipeline = [
#         {"$group": {"_id": "$date", "total": {"$sum": 1}}},
#         {"$sort": {"_id": 1}}
#     ]
#     result = list(collection.aggregate(pipeline))
#     return jsonify(result)

# # 2. 🧮 Score moyen par ASIN
# @bp.route('/api/score-by-asin')
# def score_by_asin():
#     pipeline = [
#         {"$group": {"_id": "$asin", "avg_score": {"$avg": "$score"}}},
#         {"$sort": {"avg_score": -1}}
#     ]
#     result = list(collection.aggregate(pipeline))
#     return jsonify(result)

# # 3. 🟠 Histogramme circulaire des sentiments
# @bp.route('/api/sentiment-pie')
# def sentiment_pie():
#     pipeline = [
#         {"$group": {"_id": "$sentiment", "count": {"$sum": 1}}}
#     ]
#     result = list(collection.aggregate(pipeline))
#     return jsonify(result)
  

#     return jsonify({"sentiment": resultat})

# @bp.route("/api/history")
# def api_history():
#     docs = list(collection.find().sort("date", -1))
#     result = []
#     for d in docs:
#         result.append({
#             "date": d.get("date", "inconnu"),
#             "asin": d.get("asin", "N/A"),
#             "text": d.get("text", "..."),
#             "sentiment": d.get("sentiment", "neutre"),
#             "score": d.get("score", 0)
#         })
#     return jsonify(result)
