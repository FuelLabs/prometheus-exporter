FROM python:3-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY prometheus_fuel_exporter.py /usr/src/app

ENTRYPOINT [ "python", "-u", "prometheus_fuel_exporter.py"]
