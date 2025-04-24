FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y libgobject-2.0-0 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# Start app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
