# slim variant omits build tools and docs, reducing image size
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first so this layer is only rebuilt when dependencies change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# 0.0.0.0 makes the server reachable from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
