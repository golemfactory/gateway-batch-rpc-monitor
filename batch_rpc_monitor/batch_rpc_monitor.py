import argparse
import asyncio
import time
import json
import logging
import aiohttp
import aiohttp_jinja2
import jinja2
import toml
from aiohttp import web

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Golem multi monitor')
parser.add_argument('--config_file', dest="config_file", type=str, help='Location of config', default="config-dev.toml")


async def main_loop(config):
    while True:
        logger.info("Checking ...")
        await asyncio.sleep(1)



routes = web.RouteTableDef()

@routes.get('/')
async def index(request):
    context = request.app['context']
    return aiohttp_jinja2.render_template('index.jinja2', request, context)

@routes.get('/status')
async def hello(request):
    ctx = request.app['context']

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

    hist_seconds = get_history(ctx['client_info'].time_buckets_seconds["test"], "Seconds")
    hist_minutes = get_history(ctx['client_info'].time_buckets_minutes["test"], "Minutes")
    hist_hours = get_history(ctx['client_info'].time_buckets_hours["test"], "Hours")
    hist_days = get_history(ctx['client_info'].time_buckets_days["test"], "Days")


    ctx["current"] = {
        "block_age": int(time.time()) - ctx["block_timestamp"] if "block_timestamp" in ctx else 0,
        "call_age": int(time.time()) - int(ctx["last_call"].timestamp()),
        "history": [hist_seconds, hist_minutes,hist_hours, hist_days],
    }
    response = aiohttp_jinja2.render_template('status.jinja2',
                                              request,
                                              ctx
                                              )
    return response


async def main():
    args = parser.parse_args()
    config = toml.load(args.config_file)
    app = web.Application()
    app.add_routes(routes)
    app['context'] = {
        'config': config,
    }
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('batch_rpc_monitor/templates'))
    app_task = asyncio.create_task(
        web._run_app(app, port=8080, handle_signals=False)  # noqa
    )
    await main_loop(config)
