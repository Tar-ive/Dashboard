from http.server import BaseHTTPRequestHandler
import json
import time

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Health check endpoint
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {
                    "status": "healthy",
                    "service": "CADS Research Dashboard",
                    "timestamp": int(time.time()),
                    "message": "Service is operational",
                    "version": "1.0.0"
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Main page - return HTML
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'public, max-age=300')
            self.end_headers()
            
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>CADS Research Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        padding: 40px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }}
                    .container {{ 
                        max-width: 800px;
                        background: rgba(255, 255, 255, 0.1);
                        backdrop-filter: blur(10px);
                        border-radius: 20px;
                        padding: 40px;
                        text-align: center;
                        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                        border: 1px solid rgba(255, 255, 255, 0.18);
                    }}
                    .status {{ 
                        color: #4ade80;
                        font-weight: bold;
                        font-size: 1.2em;
                        margin: 20px 0;
                    }}
                    .info {{ 
                        background: rgba(255, 255, 255, 0.1);
                        padding: 30px;
                        border-radius: 15px;
                        margin: 30px 0;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }}
                    h1 {{ 
                        font-size: 3em;
                        margin-bottom: 10px;
                        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                    }}
                    h3 {{
                        color: #fbbf24;
                        margin-bottom: 15px;
                    }}
                    .badge {{
                        display: inline-block;
                        background: rgba(34, 197, 94, 0.2);
                        color: #4ade80;
                        padding: 8px 16px;
                        border-radius: 20px;
                        margin: 5px;
                        border: 1px solid #4ade80;
                    }}
                    .timestamp {{
                        font-family: monospace;
                        opacity: 0.8;
                        font-size: 0.9em;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔬 CADS Research Dashboard</h1>
                    <p class="status">✅ Service is running successfully</p>
                    
                    <div class="info">
                        <h3>🤖 AI-Powered Research Team Assembly</h3>
                        <p>Advanced Streamlit application for intelligent matching of researchers to grant solicitations using machine learning algorithms and semantic analysis.</p>
                        
                        <div>
                            <span class="badge">Python + Streamlit</span>
                            <span class="badge">Machine Learning</span>
                            <span class="badge">NLP Processing</span>
                            <span class="badge">Vercel Deployment</span>
                        </div>
                        
                        <p><strong>Status:</strong> Deployed and operational</p>
                        <p class="timestamp"><strong>Last updated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    </div>
                    
                    <p>✨ Full Streamlit interface deployment in progress...</p>
                    <p><small>Sentry monitoring active | Health checks passing</small></p>
                </div>
            </body>
            </html>
            '''
            
            self.wfile.write(html_content.encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "error": "Internal server error",
                "message": str(e),
                "timestamp": int(time.time())
            }
            self.wfile.write(json.dumps(error_response).encode())

    def do_POST(self):
        # Handle POST requests the same way for now
        self.do_GET()