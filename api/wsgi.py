from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello():
    return jsonify({
        'status': 'success',
        'message': 'WSGI Flask API is working',
        'method': 'GET'
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
    })

@app.route('/test', methods=['POST'])
def test_post():
    try:
        data = request.get_json() or {}
        return jsonify({
            'status': 'success',
            'message': 'POST request received',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Vercel expects an 'app' variable for WSGI applications
if __name__ == '__main__':
    app.run(debug=True)