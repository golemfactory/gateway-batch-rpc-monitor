FROM python:3.11.0-bullseye
RUN pip install --upgrade pip


WORKDIR /runtime

COPY batch_rpc_monitor ./batch_rpc_monitor
COPY setup.py ./setup.py
COPY setup.cfg ./setup.cfg

