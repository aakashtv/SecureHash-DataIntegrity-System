import os

from flask import Flask, jsonify, redirect, render_template, request, url_for

from modules.feature_engineering import extract_features
from modules.key_manager import create_key, get_all_keys, init_db
from modules.lifecycle import execute_action, get_key_status
from modules.policy_engine import decide_action
from modules.risk_engine import predict_risk
from modules.telemetry import ensure_telemetry_columns, simulate_attack, simulate_normal_usage

app = Flask(__name__)
app.config.from_object('config.Config')
init_db()
ensure_telemetry_columns()


@app.route('/')
def home():
    keys = get_all_keys()
    return render_template('index.html', keys=keys)


@app.route('/create-key', methods=['POST'])
def create_key_route():
    key_name = request.form.get('key_name', '').strip()
    algorithm = request.form.get('algorithm', '').strip()

    if key_name and algorithm:
        create_key(key_name, algorithm)

    return redirect(url_for('home'))


@app.route('/simulate-normal/<int:key_id>')
def simulate_normal_route(key_id):
    simulate_normal_usage(key_id)
    return redirect(url_for('home'))


@app.route('/simulate-attack/<int:key_id>')
def simulate_attack_route(key_id):
    simulate_attack(key_id)
    return redirect(url_for('home'))


@app.route('/features/<int:key_id>')
def feature_route(key_id):
    try:
        features = extract_features(key_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 404

    return jsonify(features)


@app.route('/risk/<int:key_id>')
def risk_route(key_id):
    try:
        features = extract_features(key_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 404

    risk_result = predict_risk(features)
    policy_result = decide_action(risk_result["risk_score"])
    execute_action(key_id, policy_result["action"])
    updated_status = get_key_status(key_id)

    return jsonify(
        {
            **risk_result,
            **policy_result,
            "status": updated_status,
        }
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
