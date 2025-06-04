from flask import Flask, jsonify
import redis
import time

app = Flask(__name__)

redis_host = "localhost"
r = redis.Redis(host=redis_host, port=6379, decode_responses=True)

@app.route('/data/<key>')
def get_data(key):
    cached = r.get(key)
    if cached:
        return jsonify({'data': cached, 'source': 'cache'})

    time.sleep(2)
    value = f"Valeur générée pour {key}"
    r.setex(key, 60, value)
    return jsonify({'data': value, 'source': 'slow source'})

if __name__ == '__main__':
    app.run(debug=True)
