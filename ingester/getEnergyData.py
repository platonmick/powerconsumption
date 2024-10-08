#!/usr/bin/python3

import requests
from datetime import datetime
from typing import List, Dict
import logging
from os import environ
import signal
from threading import Event
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

    logging.debug(f"Power = {power}")
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

    logging.debug(f"url={url} org={org}")
    client = influxdb_client.InfluxDBClient(
        url=url,
        token=token,
        org=org
    )

    write_api = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=points)
    logging.debug(f"{len(points)} points written")
    client.close()


def get_energy_data():
    uri = "http://192.168.178.39/cm?cmnd=Status%2008"
    logging.debug("send request")
    response = requests.get(uri, timeout = (1, 1))
    logging.debug("got response")
    response.raise_for_status()
    
    content = response.json()

    return content["StatusSNS"]["ENERGY"]


class GracefulDeath:
  def __init__(self, exit: Event):
    self.exit = exit
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    logging.info("got signal, terminating...")
    self.exit.set()


def main():
    exit = Event()
    sighandler = GracefulDeath(exit)
    while not exit.is_set():
        logging.debug("next try")
        try:
            energydata = get_energy_data()
            timestamp = int(datetime.now().timestamp())
            list = create_point_list(energydata=energydata, timestamp=timestamp)
            influx_write(list)
        except requests.exceptions.Timeout:
            logging.warning('Timeout')
        except requests.exceptions.ReadTimeout:
            logging.warning('ReadTimeout')
        except BaseException as e:
            logging.exception(f'Got exception on main handler: {e}')
        logging.debug("start sleeping for 60 seconds")
        exit.wait(60)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    main()
