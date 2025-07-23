#!/usr/bin/env python3
import requests
import json
import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Test the MCP HTTP server")
    parser.add_argument("query", help="The query to send")
    parser.add_argument("--schema", default="product_info", help="The schema to use")
    parser.add_argument("--url", default="http://localhost:8080", help="The server URL")
    
    args = parser.parse_args()
    
    # Send a request to the server
    try:
        response = requests.post(
            f"{args.url}/query",
            json={"query": args.query, "schema": args.schema},
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Print the response
        print(json.dumps(response.json(), indent=2))
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()