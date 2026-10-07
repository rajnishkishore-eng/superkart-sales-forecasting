# Lightweight Python base image
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the Streamlit app
COPY . .

# Default backend address on the shared Docker network (can be overridden with -e BACKEND_URL=...)
ENV BACKEND_URL=http://superkart-backend:7860

# Streamlit port
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
