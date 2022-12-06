# batch-rpc-monitor

Tool for monitoring web3 RPC endpoints

## How to run locally

1. python -m batch_rpc_monitor --config-file config-dev.toml

if you are missing any dependencies, you can install them from requirements.txt

## How to run in docker

1. Prepare .env file with following variables:

```
EXTERNAL_PORT=15774
```

2. Build docker image

```
docker-compose build
```

3. Prepare config.toml file in the conf directory based on config-dev.toml

4. Run docker container

```
docker-compose up -d
```
