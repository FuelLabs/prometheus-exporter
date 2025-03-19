FROM python:3-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY utils/prometheus-fuel-exporter/requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY utils/prometheus-fuel-exporter/prometheus_fuel_exporter.py /usr/src/app

ENTRYPOINT [ "python", "-u", "prometheus_fuel_exporter.py"]
