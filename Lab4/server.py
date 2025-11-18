import os

from flask import Flask, request, jsonify
from replication import replicate_to_followers

from Lab4.store import Store

app = Flask(__name__)

store = Store()
ROLE = os.getenv("ROLE", "FOLLOWER")
FOLLOWER_URLS = os.getenv("FOLLOWERS", "")
if FOLLOWER_URLS:
    FOLLOWER_URLS = FOLLOWER_URLS.split(",")
else:
    FOLLOWER_URLS = []


@app.route("/get", methods=["GET"])
def get_data():
    key = request.args.get("key")
    if key is None:
        return jsonify({"error": "Missing ?key="}), 400

    with store.lock_data:
        value = store.data.get(key)

    return jsonify({"key": key, "value": value})


if ROLE == "LEADER":
    @app.route("/set", methods=["POST"])
    def leader_set():
        data = request.get_json()
        key = data.get("key")
        value = data.get("value")

        if key is None or value is None:
            return jsonify({"error": "Missing key or value"}), 400

        store.write_data(key, value)
        success = replicate_to_followers(key, value, FOLLOWER_URLS)

        if success:
            return jsonify({"status": "ok", "message": "Quorum reached"})
        else:
            return jsonify({"status": "fail", "message": "Quorum not reached"})


@app.route("/replicate", methods=["POST"])
def follower_replicate():
    data = request.get_json()
    key = data.get("key")
    value = data.get("value")

    if key is None or value is None:
        return jsonify({"error": "Missing key or value"}), 400

    store.write_data(key, value)

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)