FROM python:3.9-slim

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir jsonschema pydantic aiohttp

EXPOSE 8080

CMD ["python", "http_server.py", "--host", "0.0.0.0", "--port", "8080"]