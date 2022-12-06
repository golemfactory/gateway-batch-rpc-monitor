FROM python:3.11.0-bullseye
WORKDIR /runtime

COPY batch_rpc_monitor ./batch_rpc_monitor
COPY * ./

