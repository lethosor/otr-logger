FROM python:3.12-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install gunicorn

COPY bottle.py .
COPY main.py .

RUN useradd --uid 1000 user
USER user

EXPOSE 8000
STOPSIGNAL INT

ENTRYPOINT ["python3", "main.py", "--data-dir", "/data", "--host", "0.0.0.0", "--port", "8000"]
