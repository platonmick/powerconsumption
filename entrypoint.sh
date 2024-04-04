#!/bin/bash

# Protects script from continuing with an error
set -eu -o pipefail

# Ensures environment variables are set
export DOCKER_INFLUXDB_INIT_MODE=$DOCKER_INFLUXDB_INIT_MODE
export DOCKER_INFLUXDB_INIT_USERNAME=$DOCKER_INFLUXDB_INIT_USERNAME
export DOCKER_INFLUXDB_INIT_PASSWORD=$DOCKER_INFLUXDB_INIT_PASSWORD
export DOCKER_INFLUXDB_INIT_ORG=$DOCKER_INFLUXDB_INIT_ORG
export DOCKER_INFLUXDB_INIT_BUCKET=$DOCKER_INFLUXDB_INIT_BUCKET
export DOCKER_INFLUXDB_INIT_RETENTION=$DOCKER_INFLUXDB_INIT_RETENTION
export DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN
export DOCKER_INFLUXDB_INIT_PORT=$DOCKER_INFLUXDB_INIT_PORT
export DOCKER_INFLUXDB_INIT_HOST=$DOCKER_INFLUXDB_INIT_HOST

export INFLUX_TOKEN=${INFLUX_TOKEN}
export INFLUX_ORG=${INFLUX_ORG}
export INFLUX_BUCKET_NAME=${INFLUX_BUCKET_NAME}
export INFLUX_URL=${INFLUX_URL}


# Conducts initial InfluxDB using the CLI
influx setup --skip-verify --bucket ${DOCKER_INFLUXDB_INIT_BUCKET} --retention ${DOCKER_INFLUXDB_INIT_RETENTION} --org ${DOCKER_INFLUXDB_INIT_ORG} --username ${DOCKER_INFLUXDB_INIT_USERNAME} --password ${DOCKER_INFLUXDB_INIT_PASSWORD} --host http://${DOCKER_INFLUXDB_INIT_HOST}:${INFLUX_CONTAINER_PORT} --force