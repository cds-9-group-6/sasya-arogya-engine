#!/usr/bin/env python3
"""
Simple HTTP server to serve the HTML diagram visualizations
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def serve_diagrams(port=7080):
    """Serve the HTML diagrams on the specified port"""
    
    # Change to the diagrams directory
    diagrams_dir = Path(__file__).parent
    os.chdir(diagrams_dir)
    
    # Create a simple HTTP server
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print(f"🌐 Serving diagrams at http://localhost:{port}")
            print(f"📁 Serving from: {diagrams_dir}")
            print(f"🔗 Main page: http://localhost:{port}/index.html")
            print(f"🏛️ Architecture: http://localhost:{port}/architecture_visualization.html")
            print(f"🔄 Workflow: http://localhost:{port}/workflow_visualization.html")
            print("\nPress Ctrl+C to stop the server")
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{port}/index.html')
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use. Try a different port:")
            print(f"   python3 serve_diagrams.py {port + 1}")
        else:
            print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    port = 7080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid port number. Using default port 8080")
    
    serve_diagrams(port)
