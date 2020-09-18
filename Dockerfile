FROM iter8/iter8-analytics-base:latest

ENV PYTHONPATH=/

WORKDIR ${PYTHONPATH}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY iter8_analytics /iter8_analytics

CMD [ "python", "iter8_analytics/fastapi_app.py"]
