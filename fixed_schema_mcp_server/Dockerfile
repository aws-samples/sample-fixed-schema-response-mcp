FROM python:3.9-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastmcp boto3

# Make the run script executable
RUN chmod +x run_fastmcp.sh

# Run the FastMCP server
CMD ["./run_fastmcp.sh"]