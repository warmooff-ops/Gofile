#!/usr/bin/env python3
"""
GoFile Scanner API for Vercel Deployment
Webhook-enabled GoFile URL scanner
"""

import requests
import json
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import string
import random
import sys
import urllib.parse

# Codes couleur pour le terminal (pour le debug)
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class GoFileScanner:
    def __init__(self, webhook_url=None, max_threads=50, delay=0.1):
        self.webhook_url = webhook_url
        self.max_threads = max_threads
        self.delay = delay
        self.found_urls = []
        self.scanned_count = 0
        self.total_urls = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def generate_gofile_id(self, length=6):
        """Generate random GoFile ID"""
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def check_gofile_url(self, file_id):
        """Check if GoFile URL exists and has content"""
        url = f"https://gofile.io/d/{file_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                # Check if it's a valid GoFile page
                if 'gofile.io' in response.text and 'contentId' in response.text:
                    # Try to extract file information
                    try:
                        # Look for file data in the page
                        if '"files":' in response.text:
                            # Extract JSON data
                            start = response.text.find('"files":')
                            if start != -1:
                                # Find the end of the JSON object
                                bracket_count = 0
                                end = start
                                for i, char in enumerate(response.text[start:], start):
                                    if char == '{':
                                        bracket_count += 1
                                    elif char == '}':
                                        bracket_count -= 1
                                        if bracket_count == 0:
                                            end = i + 1
                                            break
                                
                                if end > start:
                                    json_str = response.text[start:end]
                                    try:
                                        file_data = json.loads('{' + json_str + '}')
                                        
                                        # Extract file information
                                        files_info = []
                                        for file_id, file_info in file_data.get('files', {}).items():
                                            files_info.append({
                                                'name': file_info.get('name', 'Unknown'),
                                                'size': file_info.get('size', 0),
                                                'type': file_info.get('mimeType', 'Unknown'),
                                                'link': file_info.get('link', ''),
                                                'md5': file_info.get('md5', ''),
                                                'created': file_info.get('created', '')
                                            })
                                        
                                        if files_info:
                                            result = {
                                                'url': url,
                                                'status': 'FOUND',
                                                'files': files_info,
                                                'total_files': len(files_info),
                                                'total_size': sum(f['size'] for f in files_info)
                                            }
                                            
                                            self.send_to_webhook(result)
                                            self.found_urls.append(result)
                                            return result
                                            
                                    except json.JSONDecodeError:
                                        pass
                        
                        # If we can't parse JSON but it's a valid GoFile page
                        result = {
                            'url': url,
                            'status': 'VALID_PAGE',
                            'message': 'GoFile page found but content could not be parsed'
                        }
                        
                        self.send_to_webhook(result)
                        self.found_urls.append(result)
                        return result
                        
                    except Exception as e:
                        pass
            
            elif response.status_code == 404:
                return None
                
        except Exception as e:
            pass
        
        return None
    
    def send_to_webhook(self, data):
        """Send found URL to webhook"""
        if not self.webhook_url:
            return
            
        try:
            # Create Discord embed
            embed = {
                "title": "🔍 GoFile Scanner - FOUND!",
                "url": data['url'],
                "color": 5814783,  # Green color
                "fields": []
            }
            
            if data['status'] == 'FOUND':
                embed["fields"].append({
                    "name": "📁 Files Found",
                    "value": str(data['total_files']),
                    "inline": True
                })
                
                embed["fields"].append({
                    "name": "💾 Total Size",
                    "value": f"{data['total_size'] / (1024*1024):.2f} MB",
                    "inline": True
                })
                
                # Add file details
                for i, file_info in enumerate(data['files'][:5]):  # Show first 5 files
                    field_name = f"📄 {file_info['name']}"
                    field_value = f"Size: {file_info['size'] / (1024*1024):.2f} MB\n"
                    if file_info['link']:
                        field_value += f"Link: {file_info['link']}\n"
                    field_value += f"Type: {file_info['type']}"
                    
                    embed["fields"].append({
                        "name": field_name,
                        "value": field_value,
                        "inline": False
                    })
                
                if len(data['files']) > 5:
                    embed["fields"].append({
                        "name": "📋 More Files",
                        "value": f"And {len(data['files']) - 5} more files...",
                        "inline": False
                    })
                    
            else:
                embed["fields"].append({
                    "name": "📄 Status",
                    "value": data['message'],
                    "inline": False
                })
            
            embed["footer"] = {
                "text": "RedTiger GoFile Scanner - Vercel API",
                "icon_url": "https://media.discordapp.net/attachments/1369051349106430004/1369054652213231687/RedTiger-Logo-1-Large.png"
            }
            
            payload = {
                "username": "RedTiger Scanner",
                "avatar_url": "https://media.discordapp.net/attachments/1369051349106430004/1369054652213231687/RedTiger-Logo-1-Large.png",
                "embeds": [embed]
            }
            
            requests.post(self.webhook_url, json=payload, timeout=10)
            
        except Exception as e:
            pass
    
    def scan_specific_ids(self, file_ids):
        """Scan specific GoFile IDs"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = []
            
            for file_id in file_ids:
                future = executor.submit(self.check_gofile_url, file_id)
                futures.append(future)
                self.total_urls += 1
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.scanned_count += 1
                    
                    if result:
                        results.append(result)
                    
                    if self.delay > 0:
                        time.sleep(self.delay)
                        
                except Exception as e:
                    pass
        
        return results
    
    def scan_common_patterns(self):
        """Scan common GoFile ID patterns"""
        common_patterns = [
            # Common patterns from user
            'IIAxbd', 'ABCDEF', '123456', 'TEST01', 'DEMO01',
            # Add more common patterns
            'FILE01', 'DATA01', 'DOC001', 'IMG001', 'VID001',
            'WORK01', 'PROJ01', 'TEMP01', 'BACKUP', 'CONFIG',
        ]
        
        return self.scan_specific_ids(common_patterns)

def handler(request):
    """Main handler for Vercel serverless function"""
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse request body for Vercel
        body = {}
        
        if hasattr(request, 'json') and callable(request.json):
            # Vercel's request object has json() method
            try:
                body = request.json()
            except:
                body = {}
        elif hasattr(request, 'body') and request.body:
            # Fallback to raw body parsing
            try:
                if isinstance(request.body, str):
                    body = json.loads(request.body)
                else:
                    body = json.loads(request.body.decode('utf-8'))
            except:
                body = {}
        
        # Also check query parameters for GET requests
        if hasattr(request, 'args') and request.args:
            body.update(request.args)
        elif hasattr(request, 'query_string') and request.query_string:
            query_string = request.query_string.decode('utf-8')
            query_params = dict(urllib.parse.parse_qsl(query_string))
            body.update(query_params)
        
        # Get parameters
        webhook_url = body.get('webhook')
        count = int(body.get('count', 100))
        threads = int(body.get('threads', 50))
        delay = float(body.get('delay', 0.1))
        patterns = body.get('patterns', 'false').lower() == 'true'
        
        # Validate parameters
        if count > 1000:
            count = 1000
        if threads > 100:
            threads = 100
        if delay < 0.01:
            delay = 0.01
        if delay > 5:
            delay = 5
        
        # Create scanner
        scanner = GoFileScanner(webhook_url, threads, delay)
        
        # Perform scan
        if patterns:
            results = scanner.scan_common_patterns()
        else:
            # Generate random IDs
            file_ids = [scanner.generate_gofile_id() for _ in range(count)]
            results = scanner.scan_specific_ids(file_ids)
        
        # Prepare response
        response_data = {
            'success': True,
            'scanned_count': scanner.scanned_count,
            'found_count': len(results),
            'success_rate': (len(results) / scanner.scanned_count * 100) if scanner.scanned_count > 0 else 0,
            'found_urls': results,
            'parameters': {
                'count': count,
                'threads': threads,
                'delay': delay,
                'patterns': patterns,
                'webhook': webhook_url is not None
            }
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

# Vercel serverless function entry point
def lambda_handler(event, context):
    """AWS Lambda style handler for Vercel compatibility"""
    class MockRequest:
        def __init__(self, event):
            self.method = event.get('httpMethod', 'GET')
            self.body = event.get('body', '{}')
            self.query_string = event.get('queryStringParameters', {})
            
            # Convert query parameters to string format
            if self.query_string:
                query_parts = []
                for key, value in self.query_string.items():
                    query_parts.append(f"{key}={value}")
                self.query_string = '&'.join(query_parts)
            else:
                self.query_string = ''
        
        def json(self):
            if self.body:
                return json.loads(self.body)
            return {}
    
    request = MockRequest(event)
    return handler(request)

# Vercel serverless function entry point
def main(request):
    return handler(request)

# Default Vercel entry point
handler_func = handler

# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self, method='GET', body='{}', query_string=''):
            self.method = method
            self.body = body
            self.query_string = query_string
    
    # Test the API
    test_request = MockRequest(
        method='POST',
        body=json.dumps({
            'webhook': 'https://discord.com/api/webhooks/YOUR_WEBHOOK',
            'count': 10,
            'threads': 20,
            'delay': 0.5,
            'patterns': 'true'
        })
    )
    
    result = main(test_request)
    print(json.dumps(json.loads(result['body']), indent=2))
