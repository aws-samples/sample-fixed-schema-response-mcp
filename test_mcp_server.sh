#!/bin/bash

echo "Testing MCP server..."
echo "Running with bash..."
/bin/bash fixed_schema_mcp_server/run_mcp.sh &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"
echo "Waiting 5 seconds..."
sleep 5
echo "Testing connection..."
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test query", "schema": "product_info"}'
echo ""
echo "Killing server..."
kill $SERVER_PID
echo "Done."