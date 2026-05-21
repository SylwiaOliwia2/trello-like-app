FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

WORKDIR /app

COPY e2e/requirements.txt /tmp/e2e-requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/e2e-requirements.txt

COPY . /app

CMD ["pytest", "-q", "e2e/tests"]
