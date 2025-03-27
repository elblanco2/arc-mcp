"""
Entry point for running the Arc MCP server.
"""
import argparse
import logging
from arc.server import ArcServer

def main():
    parser = argparse.ArgumentParser(description="Arc MCP Server - Web application deployment simplified")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="localhost", help="Host to bind the server to")
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    server = ArcServer(debug=args.debug)
    server.start(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
