FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /app

COPY e2e/requirements.txt /tmp/e2e-requirements.txt
RUN pip install --no-cache-dir -r /tmp/e2e-requirements.txt
