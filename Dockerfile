FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XRECHNUNG_VALIDATOR_COMMAND="/opt/invoicebridge/xrechnung/validate-xrechnung.sh {xml}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl openjdk-17-jre-headless unzip \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY alembic.ini ./

RUN scripts/setup_xrechnung_validator.sh /opt/invoicebridge/xrechnung \
    && python -m pip install --upgrade pip \
    && python -m pip install .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
