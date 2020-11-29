FROM python:3.9-slim AS builder
RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

RUN mkdir /iter8-analytics
WORKDIR /iter8-analytics

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY setup.py .
COPY iter8_analytics/ ./iter8_analytics/
RUN pip install -e .

FROM python:3.9-slim AS build-image
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /iter8-analytics /iter8-analytics

WORKDIR /iter8-analytics/iter8_analytics

# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"
CMD ["python", "fastapi_app.py"]
