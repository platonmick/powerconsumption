#!/usr/bin/python3

import requests
from datetime import datetime
import logging
from os import environ
import sys
import signal
from threading import Event
from influxdb_client import Point, InfluxDBClient, WriteApi
from influxdb_client.client.write_api import SYNCHRONOUS

if sys.version_info < (3, 9):
    sys.exit("This script requires Python 3.9!")

def create_point(field_key: str, field_value: float, timestamp: datetime) -> Point:
    measurement: str = "powerconsumption"
    device: str ="delock-0580"
    return Point(measurement_name=measurement).tag("device", device).field(field_key, field_value).time(timestamp, write_precision="s")


def create_point_list(energydata: dict[str, float], timestamp: datetime) -> list[Point]:
    result: list[Point] = []
    power: float = energydata["Power"]
    total: float = energydata["Total"]
    yesterday: float = energydata["Yesterday"]
    today: float = energydata["Today"]
    apparentPower: float = energydata["ApparentPower"]
    reactivePower: float = energydata["ReactivePower"]
    factor: float = energydata["Factor"]
    voltage: float = energydata["Voltage"]
    current: float = energydata["Current"]

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


def influx_write(points: list[Point]) -> None:
    bucket: str = environ["INFLUX_BUCKET_NAME"]
    org: str = environ["INFLUX_ORG"]
    token: str = environ["INFLUX_TOKEN"]
    url: str = environ["INFLUX_URL"]

    logging.debug(f"url={url} org={org}")
    client: InfluxDBClient = InfluxDBClient(
        url=url,
        token=token,
        org=org
    )

    write_api: WriteApi = client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket=bucket, org=org, record=points)
    logging.debug(f"{len(points)} points written")
    client.close()


def get_energy_data() -> dict[str, float]:
    uri: str = "http://192.168.178.39/cm?cmnd=Status%2008"
    logging.debug("send request")
    response: requests.Response = requests.get(uri, timeout = (2, 5))
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


def main() -> None:
    exit: Event = Event()
    sighandler = GracefulDeath(exit)
    while not exit.is_set():
        logging.debug("next try")
        try:
            sleeptime: int = 10
            energydata: dict[str, float] = get_energy_data()
            timestamp: datetime = datetime.now()
            points: list[Point] = create_point_list(energydata=energydata, timestamp=timestamp)
            influx_write(points)
            sleeptime = 60
        except requests.exceptions.ConnectTimeout:
            logging.warning('ConnectTimeout')
        except requests.exceptions.ReadTimeout:
            logging.warning('ReadTimeout')
        except requests.exceptions.ConnectionError as e:
            logging.warning(f'ConnectionError: {e}')
        except BaseException as e:
            logging.exception(f'Got exception on main handler: {e}')
        logging.debug(f"start sleeping for {sleeptime} seconds")
        exit.wait(sleeptime)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
    main()
