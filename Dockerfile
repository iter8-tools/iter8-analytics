FROM python:3.7.3-alpine3.9

RUN apk update && apk upgrade && apk add build-base

COPY iter8_analytics /python_code/src/iter8_analytics
ENV PYTHONPATH=/python_code/src
WORKDIR ${PYTHONPATH}
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "iter8_analytics/app.py"]
