import argparse
import uvicorn

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from metrics_cache import MetricsCache
from metrics_collector import MetricsCollector
from logger import *

app = FastAPI()


@app.get('/metrics', response_class=PlainTextResponse)
async def metrics():
    return cache_updater.retrieve_cache()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default='localhost', help='IP address to bind the app to')
    parser.add_argument('--port', type=int, default=9820, help='Port to listen on')
    parser.add_argument('--wg', type=str, default='/usr/bin/wg', help='Path to wg')
    parser.add_argument('--tls-cert', type=str, help='Path to TLS certificate file')
    parser.add_argument('--tls-key', type=str, help='Path to TLS private key file')
    args = parser.parse_args()

    wg_metrics = MetricsCollector(args.wg)
    cache_updater = MetricsCache(wg_metrics)
    cache_updater.start()

    try:
        if args.tls_cert and args.tls_key:
            uvicorn.run(app, host=args.ip, port=args.port, ssl_keyfile=args.tls_key, ssl_certfile=args.tls_cert,
                        log_config=log_config_path)
        else:
            uvicorn.run(app, host=args.ip, port=args.port, log_config=log_config_path)
    except Exception as e:
        logger.exception(f"Failed to bind the app to {args.ip}:{args.port} - {str(e)}")

    cache_updater.stop()
    cache_updater.join()
