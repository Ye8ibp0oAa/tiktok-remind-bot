FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use Render's dynamic port environment variable
CMD uvicorn bot:app --host 0.0.0.0 --port ${PORT:-10000}
