FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY *.py .

RUN chmod +x *.py

ENTRYPOINT ["python3",  "getEnergyData.py" ]