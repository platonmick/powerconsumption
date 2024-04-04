#!/usr/bin/python3

import requests
from datetime import datetime
from typing import List, Dict
import logging
from os import environ
from time import sleep
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

def create_point(field_key, field_value, timestamp):
    measurement = "powerconsumption"
    device="delock-0580"
    return influxdb_client.Point(measurement_name=measurement).tag("device", device).field(field_key, float(field_value)).time(int(timestamp), write_precision="s")


def create_point_list(energydata: Dict, timestamp: int) -> List[influxdb_client.Point]:
    result = []
    power=energydata["Power"]
    total=energydata["Total"]
    yesterday=energydata["Yesterday"]
    today=energydata["Today"]
    apparentPower=energydata["ApparentPower"]
    reactivePower=energydata["ReactivePower"]
    factor=energydata["Factor"]
    voltage=energydata["Voltage"]
    current=energydata["Current"]

    result.append(create_point("power", power, timestamp))
    result.append(create_point("total", total, timestamp))
    result.append(create_point("yesterday", yesterday, timestamp))
    result.append(create_point("today", today, timestamp))
    result.append(create_point("apparentPower", apparentPower, timestamp))
    result.append(create_point("reactivePower", reactivePower, timestamp))
    result.append(create_point("factor", factor, timestamp))
    result.append(create_point("voltage", voltage, timestamp))
    result.append(create_point("current", current, timestamp))

    return result


def influx_write(points):
    bucket = environ["INFLUX_BUCKET_NAME"]
    org = environ["INFLUX_ORG"]
    token = environ["INFLUX_TOKEN"]
    url=environ["INFLUX_URL"]

    logging.info(f"url={url} org={org}")
    client = influxdb_client.InfluxDBClient(
        url=url,
        token=token,
        org=org
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=points)


def get_energy_data():
    uri = "http://192.168.178.39/cm?cmnd=Status%2008"
    response = requests.get(uri)
    content = response.json()

    return content["StatusSNS"]["ENERGY"]


def main():
    try:
        energydata = get_energy_data()
        timestamp = int(datetime.now().timestamp())
        list = create_point_list(energydata=energydata, timestamp=timestamp)
        influx_write(list)
    except:
        logging.exception('Got exception on main handler')


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    while True:
        main()
        sleep(60)