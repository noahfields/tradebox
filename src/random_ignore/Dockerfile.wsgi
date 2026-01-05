FROM python:3.14.2-trixie

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./

RUN pip install --no-cache-dir -e .

COPY src ./src

ENV PYTHONUNBUFFERED=1

# Run Flask app with gunicorn WSGI server
# Timeout 600s handles long-running Robinhood API calls
CMD ["gunicorn", "--timeout", "600", "--workers", "3", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "src.wsgi:app"]
