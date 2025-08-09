import os
from typing import List, Dict, Any

from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
import folium
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(APP_ROOT, "data", "regions.csv")
STATIC_DIR = os.path.join(APP_ROOT, "static")
MAP_FILE = os.path.join(STATIC_DIR, "map.html")

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# Global state
regions_df: pd.DataFrame = pd.DataFrame()
model_avg_score_lr: LinearRegression | None = None
model_dropout_rf: RandomForestRegressor | None = None
kmeans_model: KMeans | None = None
sentiment = SentimentIntensityAnalyzer()


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    # Ensure expected columns exist
    expected_cols = {
        "region",
        "latitude",
        "longitude",
        "schools",
        "internet_coverage",
        "teachers",
        "students",
        "avg_score",
        "dropout_rate",
    }
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in data: {missing}")

    # Derived metrics
    df["student_teacher_ratio"] = (df["students"] / df["teachers"]).replace([np.inf, -np.inf], np.nan)
    df["students_per_school"] = (df["students"] / df["schools"]).replace([np.inf, -np.inf], np.nan)
    df["teachers_per_school"] = (df["teachers"] / df["schools"]).replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0)
    return df


def train_models(df: pd.DataFrame) -> None:
    global model_avg_score_lr, model_dropout_rf, kmeans_model
    feature_cols = ["schools", "internet_coverage", "teachers", "students",
                    "student_teacher_ratio", "students_per_school", "teachers_per_school"]

    X = df[feature_cols].values

    # Linear Regression for avg_score
    y_score = df["avg_score"].values
    model_avg_score_lr = LinearRegression()
    model_avg_score_lr.fit(X, y_score)

    # Random Forest for dropout_rate
    y_dropout = df["dropout_rate"].values
    model_dropout_rf = RandomForestRegressor(n_estimators=200, random_state=42)
    model_dropout_rf.fit(X, y_dropout)

    # Clustering
    kmeans_model = KMeans(n_clusters=4, n_init=10, random_state=42)
    df["cluster"] = kmeans_model.fit_predict(X)


def ensure_map(df: pd.DataFrame) -> None:
    # Create Folium map with circle markers sized by students and color by avg_score
    if not os.path.exists(STATIC_DIR):
        os.makedirs(STATIC_DIR, exist_ok=True)

    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6)

    # Color scaling for avg_score
    min_score = df["avg_score"].min()
    max_score = df["avg_score"].max()

    def score_color(score: float) -> str:
        # Green for high, red for low
        if max_score == min_score:
            ratio = 0.5
        else:
            ratio = (score - min_score) / (max_score - min_score)
        # Interpolate between red (255,0,0) and green (0,150,0)
        r = int(255 * (1 - ratio))
        g = int(150 * ratio)
        b = 0
        return f"#{r:02x}{g:02x}{b:02x}"

    for _, row in df.iterrows():
        popup_html = folium.Popup(
            html=(
                f"<b>{row['region']}</b><br>"
                f"Avg score: {row['avg_score']}<br>"
                f"Dropout rate: {row['dropout_rate']}%<br>"
                f"Schools: {row['schools']}<br>"
                f"Students: {row['students']}<br>"
                f"Teachers: {row['teachers']}<br>"
                f"Internet coverage: {row['internet_coverage']}%"
            ),
            max_width=300,
        )
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=max(4, min(18, row["students"] / 100000)),
            color=score_color(row["avg_score"]),
            fill=True,
            fill_opacity=0.7,
            popup=popup_html,
        ).add_to(m)

    m.save(MAP_FILE)


@app.route("/")
def index() -> Any:
    return send_from_directory(app.static_folder, "index.html")


@app.route("/map")
def serve_map() -> Any:
    # Regenerate map if missing
    if not os.path.exists(MAP_FILE):
        ensure_map(regions_df)
    return send_from_directory(app.static_folder, "map.html")


@app.route("/api/regions")
def api_regions() -> Any:
    regions = regions_df["region"].sort_values().tolist()
    return jsonify({"regions": regions})


@app.route("/api/stats")
def api_stats() -> Any:
    region = request.args.get("region")
    if not region:
        return jsonify({"error": "Missing region parameter"}), 400
    row = regions_df[regions_df["region"] == region]
    if row.empty:
        return jsonify({"error": f"Region '{region}' not found"}), 404
    result = row.iloc[0].to_dict()
    # Ensure native Python types for JSON
    result = {k: (v.item() if hasattr(v, "item") else v) for k, v in result.items()}
    return jsonify(result)


@app.route("/api/summary")
def api_summary() -> Any:
    summary = {
        "num_regions": int(regions_df.shape[0]),
        "best_avg_score_region": regions_df.loc[regions_df["avg_score"].idxmax(), "region"],
        "worst_avg_score_region": regions_df.loc[regions_df["avg_score"].idxmin(), "region"],
        "max_avg_score": float(regions_df["avg_score"].max()),
        "min_avg_score": float(regions_df["avg_score"].min()),
        "median_student_teacher_ratio": float(regions_df["student_teacher_ratio"].median()),
    }
    return jsonify(summary)


@app.route("/api/compare")
def api_compare() -> Any:
    metric = request.args.get("metric", "avg_score")
    if metric not in regions_df.columns:
        return jsonify({"error": f"Unknown metric '{metric}'"}), 400
    records = regions_df[["region", metric]].sort_values(metric, ascending=False).to_dict(orient="records")
    return jsonify({"metric": metric, "data": records})


@app.route("/api/clusters")
def api_clusters() -> Any:
    if "cluster" not in regions_df.columns:
        return jsonify({"error": "Clustering not available"}), 500
    records = regions_df[["region", "cluster"]].to_dict(orient="records")
    return jsonify({"clusters": records})


@app.route("/api/predict", methods=["POST"])
def api_predict() -> Any:
    payload = request.get_json(silent=True) or {}
    feature_cols = ["schools", "internet_coverage", "teachers", "students",
                    "student_teacher_ratio", "students_per_school", "teachers_per_school"]
    try:
        X_input = np.array([[float(payload.get(col)) for col in feature_cols]])
    except Exception as e:
        return jsonify({"error": f"Invalid payload: {e}"}), 400

    score_pred = float(model_avg_score_lr.predict(X_input)[0]) if model_avg_score_lr else None
    dropout_pred = float(model_dropout_rf.predict(X_input)[0]) if model_dropout_rf else None
    return jsonify({
        "predicted_avg_score": score_pred,
        "predicted_dropout_rate": dropout_pred,
    })


@app.route("/api/sentiment", methods=["POST"])
def api_sentiment() -> Any:
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    scores = sentiment.polarity_scores(text)
    label = "positive" if scores["compound"] >= 0.05 else ("negative" if scores["compound"] <= -0.05 else "neutral")
    return jsonify({"scores": scores, "label": label})


@app.route("/api/recommendations")
def api_recommendations() -> Any:
    region = request.args.get("region")
    if not region:
        return jsonify({"error": "Missing region parameter"}), 400
    row = regions_df[regions_df["region"] == region]
    if row.empty:
        return jsonify({"error": f"Region '{region}' not found"}), 404
    row = row.iloc[0]

    recs: List[str] = []
    # Heuristic recommendations comparing to medians
    medians = regions_df.median(numeric_only=True)

    if row["internet_coverage"] < medians["internet_coverage"]:
        recs.append("Increase broadband and school Wi‑Fi coverage; prioritize school connectivity programs.")
    if row["student_teacher_ratio"] > medians["student_teacher_ratio"]:
        recs.append("Hire additional teachers or deploy remote teaching support to reduce class sizes.")
    if row["students_per_school"] > medians["students_per_school"]:
        recs.append("Consider building new schools/classrooms or optimizing school zoning to reduce overcrowding.")
    if row["avg_score"] < medians["avg_score"]:
        recs.append("Targeted tutoring, teacher professional development, and learning materials in low-performing schools.")
    if row["dropout_rate"] > medians["dropout_rate"]:
        recs.append("Implement at-risk student monitoring, stipends, and community engagement to reduce dropout.")

    # Cluster-based peer suggestions
    if "cluster" in regions_df.columns:
        same_cluster = regions_df[(regions_df["cluster"] == row["cluster"]) & (regions_df["region"] != region)]
        top_peers = same_cluster.sort_values("avg_score", ascending=False).head(2)["region"].tolist()
    else:
        top_peers = []

    return jsonify({
        "region": region,
        "recommendations": recs,
        "peer_regions": top_peers,
    })


@app.after_request
def add_cache_headers(resp):
    # Prevent caching during development
    resp.headers["Cache-Control"] = "no-store"
    return resp


def bootstrap() -> None:
    global regions_df
    regions_df = load_data()
    train_models(regions_df)
    ensure_map(regions_df)


if __name__ == "__main__":
    bootstrap()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)