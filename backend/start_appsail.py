import os
import sys
import traceback
import http.server
import socketserver

# Insert local vendor directory to sys.path on Catalyst (Linux) or when specified by Catalyst port
if os.name != 'nt' or os.getenv("X_ZOHO_CATALYST_LISTEN_PORT"):
    lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
    if lib_path not in sys.path:
        sys.path.insert(0, lib_path)

def run_error_server(error_msg, port):
    class ErrorHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(error_msg.encode('utf-8'))

    print(f"Starting diagnostic server on port {port}...")
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), ErrorHandler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    try:
        port_str = os.getenv("X_ZOHO_CATALYST_LISTEN_PORT", os.getenv("PORT", "8000"))
        if not port_str or port_str.strip() == "":
            port_str = "8000"
        port = int(port_str)
    except Exception:
        port = 8000

    try:
        # Attempt to import and launch the FastAPI app
        import uvicorn
        from main import app
        
        print(f"Starting uvicorn on port {port}...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = f"BOOT EXCEPTION ENCOUNTERED:\n\n{tb}\n\nPython Path: {sys.path}\nPython Version: {sys.version}\n"
        print(error_msg)
        run_error_server(error_msg, port)
