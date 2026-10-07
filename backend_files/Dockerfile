# Lightweight Python base image
FROM python:3.11-slim

# Working directory inside the container
WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the API code and the serialized model
COPY . .

# Port on which the Flask API is served
EXPOSE 7860

# Run the Flask app (object `superkart_api` in app.py) on 0.0.0.0:7860 with gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:7860", "app:superkart_api"]
