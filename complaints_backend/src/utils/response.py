from flask import jsonify

def success_response(data=None, message=None, status_code=200):
    """إنشاء استجابة نجاح موحّدة"""
    response = {
        'success': True,
        'data': data if data is not None else {},
    }
    if message:
        response['message'] = message
    return jsonify(response), status_code

def error_response(error, message=None, status_code=400):
    """إنشاء استجابة خطأ موحّدة"""
    response = {
        'success': False,
        'error': error,
        'data': None
    }
    if message:
        response['message'] = message
    return jsonify(response), status_code
