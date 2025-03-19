#!/usr/bin/python

import json
import os
import sys
import time
import logging
import requests
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY

logging.basicConfig(stream=sys.stdout, level=os.environ.get('LOGLEVEL', 'info').upper())
logger = logging.getLogger(__name__)


def get_block_height_header(url):
    headers = {'Content-Type': 'application/json'}
    data = {"query": "query ChainInfo { chain { latestBlock { header { height daHeight}}}}"}

    logger.debug(get_block_height_header.__name__ + ":url: " + url)
    logger.debug(get_block_height_header.__name__ + ":headers: " + str(headers))
    logger.debug(get_block_height_header.__name__ + ":data: " + str(data))

    response = requests.post(url, headers=headers, data=json.dumps(data))
    logger.debug(get_block_height_header.__name__ + ":response: " + response.text + "\n")

    return json.loads(response.text)["data"]["chain"]["latestBlock"]["header"]


def get_balance_amount(url, owner, asset_id):
    headers = {'Content-Type': 'application/json'}
    data = {
        "query": "query Balance($owner: Address!, $assetId: AssetId!) { balance(owner: $owner, assetId: $assetId) { amount }}",
        "variables": {
            "owner": owner,
            "assetId": asset_id
        }
    }

    logger.debug(get_balance_amount.__name__ + ":url: " + url)
    logger.debug(get_balance_amount.__name__ + ":headers: " + str(headers))
    logger.debug(get_balance_amount.__name__ + ":data: " + str(data))

    response = requests.post(url, headers=headers, data=json.dumps(data))
    logger.debug(get_balance_amount.__name__ + ":response: " + response.text + "\n")

    return json.loads(response.text)["data"]["balance"]["amount"]


def get_dispense_amount(url):
    logger.debug(get_dispense_amount.__name__ + ":url: " + url)

    response = requests.get(url)
    logger.debug(get_dispense_amount.__name__ + ":response: " + response.text + "\n")

    return json.loads(response.text)["amount"]


class FuelCollector(object):
    def __init__(self, network, graphql_url, balance_owner, balance_asset_id, faucet_url):
        self._network = network
        self._graphql_url = graphql_url
        self._balance_owner = balance_owner
        self._balance_assed_id = balance_asset_id
        self._faucet_url = faucet_url

    def collect(self):
        labels = ["metric"]

        logger.info(FuelCollector.collect.__name__ + ":Collecting Chain data")
        block_height_header = get_block_height_header(self._graphql_url)
        block_height = block_height_header["height"]
        block_da_height = block_height_header["daHeight"]
        logger.info(FuelCollector.collect.__name__ + ":Block height = " + str(block_height))
        logger.info(FuelCollector.collect.__name__ + ":Block daHeight = " + str(block_da_height))

        counter_metrics = [
            {"key": "block_height", "value": block_height},
            {"key": "block_da_height", "value": block_da_height}
        ]

        logger.info(FuelCollector.collect.__name__ + ":Adding Chain metrics")
        for metric in counter_metrics:
            counter = CounterMetricFamily("chain", "Metrics for Chain info", labels=labels)
            counter.add_metric([metric["key"]], metric["value"])
            yield counter
        logger.info(FuelCollector.collect.__name__ + ":Chain metrics added successfully!\n")

        if self._network != "mainnet":
            logger.info(FuelCollector.collect.__name__ + ":Collecting Faucet data")
            balance_amount = get_balance_amount(self._graphql_url, self._balance_owner, self._balance_assed_id)
            logger.info(FuelCollector.collect.__name__ + ":Balance amount = " + str(balance_amount))

            dispense_amount = get_dispense_amount(self._faucet_url)
            logger.info(FuelCollector.collect.__name__ + ":Dispense amount = " + str(dispense_amount))

            gauge_metrics = [
                {"key": "balance_amount", "value": balance_amount},
                {"key": "dispense_amount", "value": dispense_amount}
            ]

            logger.info(FuelCollector.collect.__name__ + ":Adding Faucet metrics")
            for metric in gauge_metrics:
                gauge = GaugeMetricFamily("faucet", "Metrics for Faucet health", labels=labels)
                gauge.add_metric([metric["key"]], metric["value"])
                yield gauge
            logger.info(FuelCollector.collect.__name__ + ":Faucet metrics added successfully!\n")


if __name__ == "__main__":
    logger.info("Starting...")

    required_envs = ["NETWORK", "APP_PORT", "GRAPHQL_URL"]
    for env in required_envs:
        if env not in os.environ:
            logging.error("Please set required environment variables!\n" + str(required_envs) + "\n")
            sys.exit(1)

    network = os.environ["NETWORK"]
    app_port = os.environ["APP_PORT"]
    graphql_url = os.environ["GRAPHQL_URL"]

    if network != "mainnet":
        additional_envs = ["BALANCE_OWNER", "BALANCE_ASSET_ID", "FAUCET_URL"]
        for env in additional_envs:
            if env not in os.environ:
                logging.error("Please set required environment variables!\n" + str(additional_envs) + "\n")
                sys.exit(1)

    balance_owner = os.environ.get("BALANCE_OWNER", "N/A")
    balance_asset_id = os.environ.get("BALANCE_ASSET_ID", "N/A")
    faucet_url = os.environ.get("FAUCET_URL", "N/A")

    logger.debug("CONFIG:network: " + network)
    logger.debug("CONFIG:app_port: " + app_port)
    logger.debug("CONFIG:graphql_url: " + graphql_url)
    logger.debug("CONFIG:balance_owner: " + str(balance_owner))
    logger.debug("CONFIG:balance_asset_id: " + str(balance_asset_id))
    logger.debug("CONFIG:faucet_url: " + str(faucet_url) + "\n")

    logger.debug("Starting HTTP server on port " + app_port)
    start_http_server(int(app_port))

    logger.debug("Registering Fuel Collector\n")
    REGISTRY.register(FuelCollector(network, graphql_url, balance_owner, balance_asset_id, faucet_url))

    while True:
        time.sleep(1)
