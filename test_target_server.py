from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/data', methods=['POST'])
def receive_data():
    if request.is_json:
        data = request.get_json()
        print(f"Test-Zielserver: JSON-Daten empfangen: {data}")
        return jsonify({"status": "success", "received_data": data}), 200
    else:
        print(f"Test-Zielserver: Nicht-JSON-Daten empfangen oder falscher Content-Type: {request.headers.get('Content-Type')}")
        return jsonify({"status": "error", "message": "Expected JSON data"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)