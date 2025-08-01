"""
使用函数格式的Vercel API处理器
"""
import json

def handler(request):
    """
    Vercel函数处理器
    """
    try:
        # 获取请求方法和路径
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        # 设置响应头
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        if method == 'GET':
            response_data = {
                'status': 'success',
                'message': 'Function-based Vercel API is working',
                'method': method,
                'path': path
            }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data)
            }
            
        elif method == 'POST':
            # 获取请求体
            body = request.get('body', '{}')
            if isinstance(body, str):
                try:
                    data = json.loads(body)
                except:
                    data = {}
            else:
                data = body
            
            response_data = {
                'status': 'success',
                'message': 'POST request received',
                'method': method,
                'path': path,
                'data': data
            }
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(response_data)
            }
            
        else:
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({
                    'status': 'error',
                    'message': f'Method {method} not allowed'
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            })
        }