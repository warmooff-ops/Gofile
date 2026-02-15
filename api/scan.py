#!/usr/bin/env python3
"""
GoFile Scanner API for Vercel Deployment - Simple Version
"""

import json

def handler(event, context=None):
    """Simple handler for testing"""
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request
    if isinstance(event, dict) and event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Simple response for testing
        response_data = {
            'success': True,
            'message': 'GoFile Scanner API is working!',
            'status': 'ready'
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data, indent=2)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Internal server error'
            })
        }

# For local testing
if __name__ == "__main__":
    result = handler({})
    print(json.dumps(json.loads(result['body']), indent=2))
