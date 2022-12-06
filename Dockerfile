FROM python:3.11.0-bullseye
RUN apt-get update
RUN apt-get install -y vim
RUN pip install --upgrade pip

WORKDIR /runtime

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY setup.py ./setup.py
COPY setup.cfg ./setup.cfg
COPY batch_rpc_monitor ./batch_rpc_monitor
