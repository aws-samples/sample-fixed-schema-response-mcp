#!/usr/bin/env python3
import json
import requests
import argparse

def send_request(query, schema=None):
    """Send a request to the MCP server."""
    url = "http://localhost:8080/query"
    
    payload = {
        "query": query
    }
    
    if schema:
        payload["schema"] = schema
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Test client for Fixed Schema MCP Server")
    parser.add_argument("query", help="The query to send to the server")
    parser.add_argument("--schema", help="The schema to use for the response")
    
    args = parser.parse_args()
    
    print(f"Sending query: {args.query}")
    if args.schema:
        print(f"Using schema: {args.schema}")
    
    response = send_request(args.query, args.schema)
    
    if response:
        print("\nResponse:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    main()