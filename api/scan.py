#!/usr/bin/env python3
"""
GoFile Scanner API for Vercel Deployment
"""

import json
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import string
import random
import urllib.parse

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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def generate_gofile_id(self, length=6):
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def check_gofile_url(self, file_id):
        url = f"https://gofile.io/d/{file_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                if 'gofile.io' in response.text and 'contentId' in response.text:
                    if '"files":' in response.text:
                        start = response.text.find('"files":')
                        if start != -1:
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
                    
                    result = {
                        'url': url,
                        'status': 'VALID_PAGE',
                        'message': 'GoFile page found but content could not be parsed'
                    }
                    
                    self.send_to_webhook(result)
                    self.found_urls.append(result)
                    return result
            
            elif response.status_code == 404:
                return None
                
        except Exception:
            pass
        
        return None
    
    def send_to_webhook(self, data):
        if not self.webhook_url:
            return
            
        try:
            embed = {
                "title": "🔍 GoFile Scanner - FOUND!",
                "url": data['url'],
                "color": 5814783,
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
                
                for i, file_info in enumerate(data['files'][:5]):
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
            
        except Exception:
            pass
    
    def scan_specific_ids(self, file_ids):
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
                        
                except Exception:
                    pass
        
        return results
    
    def scan_common_patterns(self):
        common_patterns = [
            'IIAxbd', 'ABCDEF', '123456', 'TEST01', 'DEMO01',
            'FILE01', 'DATA01', 'DOC001', 'IMG001', 'VID001',
            'WORK01', 'PROJ01', 'TEMP01', 'BACKUP', 'CONFIG',
        ]
        
        return self.scan_specific_ids(common_patterns)

def handler(event, context=None):
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
        # Parse request
        body = {}
        query_params = {}
        
        if isinstance(event, dict):
            # AWS Lambda format
            method = event.get('httpMethod', 'GET')
            body_data = event.get('body', '{}')
            query_params = event.get('queryStringParameters', {}) or {}
            
            if method == 'POST' and body_data:
                try:
                    if isinstance(body_data, str):
                        body = json.loads(body_data)
                    else:
                        body = body_data
                except:
                    body = {}
        else:
            # Direct request
            method = getattr(event, 'method', 'GET')
            if hasattr(event, 'json') and callable(event.json):
                try:
                    body = event.json()
                except:
                    body = {}
            elif hasattr(event, 'body') and event.body:
                try:
                    if isinstance(event.body, str):
                        body = json.loads(event.body)
                    else:
                        body = json.loads(event.body.decode('utf-8'))
                except:
                    body = {}
        
        # Merge parameters
        all_params = {**query_params, **body}
        
        # Get parameters
        webhook_url = all_params.get('webhook')
        count = int(all_params.get('count', 100))
        threads = int(all_params.get('threads', 50))
        delay = float(all_params.get('delay', 0.1))
        patterns = all_params.get('patterns', 'false').lower() == 'true'
        
        # Validate parameters
        if count > 1000:
            count = 1000
        if threads > 100:
            threads = 100
        if delay < 0.01:
            delay = 0.01
        if delay > 5:
            delay = 5
        
        # Create scanner and run
        scanner = GoFileScanner(webhook_url, threads, delay)
        
        if patterns:
            results = scanner.scan_common_patterns()
        else:
            file_ids = [scanner.generate_gofile_id() for _ in range(count)]
            results = scanner.scan_specific_ids(file_ids)
        
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

# For local testing
if __name__ == "__main__":
    class MockRequest:
        def __init__(self, method='GET', body='{}'):
            self.method = method
            self.body = body
    
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
    
    result = handler(test_request)
    print(json.dumps(json.loads(result['body']), indent=2))
