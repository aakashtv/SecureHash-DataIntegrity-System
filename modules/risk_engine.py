import pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
RISK_MODEL_PATH = MODEL_DIR / "risk_model.pkl"
ANOMALY_MODEL_PATH = MODEL_DIR / "anomaly_model.pkl"
FEATURE_ORDER = [
    "usage_rate",
    "geo_variance",
    "key_age",
    "anomaly_flag",
    "algo_strength",
]


def _generate_synthetic_data(num_samples=1000):
    random_state = np.random.default_rng(42)

    usage_rate = random_state.integers(0, 101, size=num_samples)
    geo_variance = random_state.integers(0, 3, size=num_samples)
    key_age = random_state.integers(0, 366, size=num_samples)
    anomaly_flag = random_state.integers(0, 2, size=num_samples)
    algo_strength = random_state.integers(0, 2, size=num_samples)

    features = np.column_stack(
        (usage_rate, geo_variance, key_age, anomaly_flag, algo_strength)
    )
    labels = np.where(
        (anomaly_flag == 1) | (usage_rate > 70) | (algo_strength == 0),
        1,
        0,
    )

    return features, labels


def train_models():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    features, labels = _generate_synthetic_data()

    risk_model = RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        max_depth=8,
    )
    risk_model.fit(features, labels)

    anomaly_model = IsolationForest(
        contamination=0.2,
        random_state=42,
    )
    anomaly_model.fit(features)

    with open(RISK_MODEL_PATH, "wb") as model_file:
        pickle.dump(risk_model, model_file)

    with open(ANOMALY_MODEL_PATH, "wb") as model_file:
        pickle.dump(anomaly_model, model_file)


def _load_pickle_model(model_path):
    with open(model_path, "rb") as model_file:
        return pickle.load(model_file)


def load_models():
    if not RISK_MODEL_PATH.exists() or not ANOMALY_MODEL_PATH.exists():
        train_models()

    risk_model = _load_pickle_model(RISK_MODEL_PATH)
    anomaly_model = _load_pickle_model(ANOMALY_MODEL_PATH)
    return risk_model, anomaly_model


def _prepare_feature_array(features_dict):
    return np.array(
        [[float(features_dict.get(feature_name, 0)) for feature_name in FEATURE_ORDER]]
    )


def _normalize_anomaly_score(anomaly_model, feature_array):
    raw_score = anomaly_model.decision_function(feature_array)[0]
    normalized_score = np.interp(raw_score, [-0.5, 0.5], [100, 0])
    return float(np.clip(normalized_score, 0, 100))


def _risk_level_from_score(risk_score):
    if risk_score <= 25:
        return "Low"
    if risk_score <= 50:
        return "Medium"
    if risk_score <= 75:
        return "High"
    return "Critical"


def predict_risk(features_dict):
    risk_model, anomaly_model = load_models()
    feature_array = _prepare_feature_array(features_dict)

    ml_probability = risk_model.predict_proba(feature_array)[0][1]
    ml_score = float(ml_probability * 100)
    anomaly_score = _normalize_anomaly_score(anomaly_model, feature_array)
    risk_score = round((ml_score * 0.7) + (anomaly_score * 0.3), 2)

    return {
        "risk_score": risk_score,
        "risk_level": _risk_level_from_score(risk_score),
    }
