# Pulled via Google's public Docker Hub mirror: the shared docker-build-push.yml
# workflow only authenticates to ghcr.io (push target), and these builds now run on
# shared-IP GitHub-hosted runners instead of dedicated BuildJet ones, so an
# unauthenticated docker.io pull risks Docker Hub rate limiting.
FROM mirror.gcr.io/library/python:3-slim

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

COPY prometheus_fuel_exporter.py /usr/src/app

ENTRYPOINT [ "python", "-u", "prometheus_fuel_exporter.py"]
