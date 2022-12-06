# batch-rpc-monitor

Tool for monitoring web3 RPC endpoints

## How to run 

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
