import argparse
import asyncio
import time
import json
import logging
from datetime import datetime, timedelta, timezone

import aiohttp
import aiohttp_jinja2
import jinja2
import prometheus_client
import toml
from aiohttp import web
from batch_rpc_provider import BatchRpcProvider, BatchRpcException
from .client_info import ClientInfo, RequestType

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Golem multi monitor')
parser.add_argument('--config-file', dest="config_file", type=str, help='Location of config', default="config-dev.toml")

METRICS = {}  # Lazy initialized later


async def burst_call(context, target_url, token_holder, token_address, number_calls):
    number_of_success_req = 0
    number_of_failed_req = 0
    p = BatchRpcProvider(target_url, 20)

    try:
        latest_block = await p.get_block_by_number("latest", False)
        block_number = int(latest_block["number"], 0)
        block_checked = block_number - 10
        block_ts = int(latest_block["timestamp"], 0)
        current_ts = int(time.time())
        old_s = current_ts - block_ts

        context["block_age"] = old_s
        context["block_timestamp"] = block_ts

        logger.info(f"Latest block is {old_s}s old")

        # logger.info(f"Latest block: {latest_block}")
    except Exception as ex:
        logger.error(f"Other error when getting request: {ex}")
        raise ex

    token_address = token_address

    single_holder_array = [token_holder]

    max_steps = number_calls
    while max_steps > 0:
        max_steps -= 1
        success = False
        try:
            resp = await p.get_erc20_balance(single_holder_array[0], token_address, f"0x{block_checked:x}")
            balance = resp
            b = int(balance, 16) / 10 ** 18
            logger.info(f"Block checked: {block_checked} Amount: {b}")
            success = True
        except BatchRpcException as ex:
            logger.error(f"BatchRpcException when getting request: {ex}")
            raise ex
        except Exception as ex:
            logger.error(f"Other error when getting request: {ex}")
            raise ex

        if success:
            number_of_success_req += 1
        else:
            number_of_failed_req += 1

    logger.info(f"Number of success requests: {number_of_success_req}")
    logger.info(f"Number of failed requests: {number_of_failed_req}")

    return number_of_success_req, number_of_failed_req


async def worker_loop(context, entry):
    stats = dict()

    context["status"][entry]['stats'] = stats
    stats['client_info'] = ClientInfo(1, "apikey")

    while True:
        try:

            endpoint = context["config"]['endpoint'][entry]

            p = BatchRpcProvider(endpoint["url"], 20)

            target_url = endpoint["url"]
            logger.info(f"Checking target url: {target_url}")
            try:
                # burst_call returns success_request_count and failure_request_count
                (s_r, f_r) = await burst_call(stats, target_url, endpoint["token_holder"], endpoint["token_address"],
                                              endpoint["request_burst"])
                if f_r == 0 and s_r > 0:
                    stats["last_success"] = datetime.now()
                    stats["last_result"] = "success"
                    stats['client_info'].add_request("test", RequestType.Succeeded)
                else:
                    stats["last_result"] = "failure"
                    stats['client_info'].add_request("test", RequestType.Failed)
            except Exception as ex:
                stats["last_result"] = "error"
                stats["last_err"] = ex
                stats["last_err_time"] = datetime.now()
                stats['client_info'].add_request("test", RequestType.Failed)
            stats["last_call"] = datetime.now()
            logger.info(f"Worker loop {endpoint} ...")
        except Exception as ex:
            logger.error(f"Exception in worker loop: {ex}")

        await asyncio.sleep(20)


async def main_loop(context):
    config = context['config']
    for entry in config['endpoint']:
        asyncio.create_task(worker_loop(context, entry))

    while True:
        # logger.info("Main loop ...")
        await asyncio.sleep(1)


routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    context = request.app['context']
    return aiohttp_jinja2.render_template('index.jinja2', request, context)


@routes.get('/status')
async def status_endpoint(request):
    context = request.app['context']

    def get_history(buckets, title):
        hist = []
        for key in reversed(buckets):
            time1 = key
            el = buckets[key]
            if el.request_count > 0 and el.request_failed_count:
                class_name = "warning"
            elif el.request_failed_count > 0:
                class_name = "error"
            elif el.request_count > 0:
                class_name = "success"
            else:
                class_name = "warning"


            hist.append({
                "time": time1,
                "requests": el.request_count,
                "failures": el.request_failed_count,
                'class': class_name
            })
        return {
            "hist": hist,
            "title": title
        }

    for endpoint in context['status']:
        status = context['status'][endpoint]
        hist_seconds = get_history(status['stats']['client_info'].time_buckets_seconds["test"], "Seconds")
        hist_minutes = get_history(status['stats']['client_info'].time_buckets_minutes["test"], "Minutes")
        hist_hours = get_history(status['stats']['client_info'].time_buckets_hours["test"], "Hours")
        hist_days = get_history(status['stats']['client_info'].time_buckets_days["test"], "Days")

        dt = datetime.now(timezone.utc)
        minute_ago_str = (dt - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S")
        hour_ago_str = (dt - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        days_ago_str = (dt - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        last_minute_errors = 0
        last_minute_requests = 0
        for i in range(0, len(hist_seconds['hist'])):
            if hist_seconds['hist'][i]['time'] < minute_ago_str:
                break
            last_minute_errors += hist_seconds['hist'][i]['failures']
            last_minute_requests += hist_seconds['hist'][i]['requests']

        last_hour_errors = 0
        last_hour_requests = 0
        for i in range(0, len(hist_minutes['hist'])):
            if hist_minutes['hist'][i]['time'] < hour_ago_str:
                break
            last_hour_errors += hist_minutes['hist'][i]['failures']
            last_hour_requests += hist_minutes['hist'][i]['requests']

        last_day_errors = 0
        last_day_requests = 0
        for i in range(0, len(hist_hours['hist'])):
            if hist_hours['hist'][i]['time'] < days_ago_str:
                break
            last_day_errors += hist_hours['hist'][i]['failures']
            last_day_requests += hist_hours['hist'][i]['requests']

        last_status = status['stats']['last_result']
        status["current"] = {
            "last_status": last_status,
            "block_age": int(time.time()) - status['stats']["block_timestamp"] if "block_timestamp" in status['stats'] else 0,
            "call_age": int(time.time()) - int(status['stats']["last_call"].timestamp()),
            "last_day_requests": last_day_requests,
            "last_day_errors": last_day_errors,
            "last_day_error_class": "failure" if last_day_errors != 0 else "success",
            "last_hour_requests": last_hour_requests,
            "last_hour_errors": last_hour_errors,
            "last_hour_error_class": "failure" if last_hour_errors != 0 else "success",
            "last_minute_requests": last_minute_requests,
            "last_minute_errors": last_minute_errors,
            "last_minute_error_class": "failure" if last_minute_errors != 0 else "success",
            "history": [hist_seconds, hist_minutes, hist_hours, hist_days],
        }
    if 'json' in request.query:
        response = aiohttp.web.json_response([[i, context['status'][i]['current']] for i in context['status']])
    elif 'muninconfig' in request.query:
        response_lines = []
        response_lines.append("graph_title Batch RPC endpoint")
        response_lines.append("graph_vlabel seconds")
        for endpoint_label in context['status']:
            response_lines.append(f"{endpoint_label}_call_age.label {endpoint_label} last check")
            response_lines.append(f"{endpoint_label}_call_age.warning 60")
            response_lines.append(f"{endpoint_label}_call_age.critical 1800")
            response_lines.append(f"{endpoint_label}_block_age.label {endpoint_label} last block")
            response_lines.append(f"{endpoint_label}_block_age.warning 120")
            response_lines.append(f"{endpoint_label}_block_age.critical 600")
        response = aiohttp.web.Response(text="\n".join(response_lines))
    elif 'munin' in request.query:
        response_lines = []
        for endpoint_label in context['status']:
            current_endpoint = context['status'][endpoint_label]['current']
            response_lines.append(f"{endpoint_label}_call_age.value {current_endpoint['call_age']}")
            response_lines.append(f"{endpoint_label}_block_age.value {current_endpoint['block_age']}")
        response = aiohttp.web.Response(text="\n".join(response_lines))
    elif 'prometheus' in request.query:
        for endpoint_label in context['status']:
            current_endpoint = context['status'][endpoint_label]['current']
            call_label = f"{endpoint_label.replace('-', '_')}_call_age"
            block_label = f"{endpoint_label.replace('-', '_')}_block_age"
            if call_label not in METRICS:
                METRICS[call_label] = prometheus_client.Gauge(call_label, "Seconds since last check")
            if block_label not in METRICS:
                METRICS[block_label] = prometheus_client.Gauge(block_label, "Latest block age")
            METRICS[call_label].set(current_endpoint['call_age'])
            METRICS[block_label].set(current_endpoint['block_age'])
        response = aiohttp.web.Response(body=prometheus_client.generate_latest())
    else:
        response = aiohttp_jinja2.render_template('status.jinja2',
                                              request,
                                              context
                                              )
    return response


async def main():
    args = parser.parse_args()
    config = toml.load(args.config_file)
    app = web.Application()
    app.add_routes(routes)

    status = dict()
    for c in config["endpoint"]:
        status[c] = dict()
        status[c]["info"] = "unknown"

    app['context'] = {
        'config': config,
        'status': status,
    }
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('batch_rpc_monitor/templates'))
    app_task = asyncio.create_task(
        web._run_app(app, port=8080, handle_signals=False)  # noqa
    )
    await main_loop(app['context'])
