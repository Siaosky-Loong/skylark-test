import json

def handler(request, response):
    """
    Simple function handler for Vercel
    """
    try:
        # Set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Content-Type'] = 'application/json'
        
        # Handle different methods
        method = getattr(request, 'method', 'GET')
        
        if method == 'GET':
            data = {
                'status': 'success',
                'message': 'Simple function handler is working',
                'method': method
            }
        elif method == 'POST':
            try:
                body = getattr(request, 'body', '{}')
                if isinstance(body, bytes):
                    body = body.decode('utf-8')
                request_data = json.loads(body) if body else {}
            except:
                request_data = {}
                
            data = {
                'status': 'success',
                'message': 'POST request received',
                'method': method,
                'data': request_data
            }
        else:
            data = {
                'status': 'error',
                'message': f'Method {method} not supported'
            }
            
        response.status = 200
        response.write(json.dumps(data))
        
    except Exception as e:
        response.status = 500
        response.headers['Content-Type'] = 'application/json'
        error_data = {
            'status': 'error',
            'message': f'Internal error: {str(e)}'
        }
        response.write(json.dumps(error_data))