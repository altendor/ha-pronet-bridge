FROM python:3.12-alpine

RUN pip install websocket-client paho-mqtt

COPY run.py /run.py

CMD ["python", "/run.py"]
