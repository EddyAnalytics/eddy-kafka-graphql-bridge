import json
import logging
import asyncio
import sentry_sdk
from tartiflette_starlette import mount
from sentry_asgi import SentryMiddleware
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.authentication import requires
from starlette_jwt import JWTAuthenticationBackend
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException
from starlette_prometheus import metrics, PrometheusMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from graphql import graphql_app
from config import *


# instantiate the main webapp
app = Starlette(debug=DEBUG)


# enable permissive CORS
# https://www.starlette.io/middleware/#corsmiddleware
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])


# enable gzip for responses over 500 bytes
# https://www.starlette.io/middleware/#gzipmiddleware
app.add_middleware(GZipMiddleware)


# enable sentry middleware if a DSN is configured
if SENTRY_DSN:
    # https://github.com/encode/sentry-asgi
    sentry_sdk.init(dsn=SENTRY_DSN)
    app.add_middleware(SentryMiddleware)


# if deployed behind a proxy set the client data from the X-Forwarded headers
if BEHIND_PROXY:
    # https://github.com/encode/uvicorn/blob/master/uvicorn/middleware/proxy_headers.py
    app.add_middleware(ProxyHeadersMiddleware)


# if metrics are enabled load the prometheus middleware
# https://github.com/perdy/starlette-prometheus
if METRICS:
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics/", metrics)


# enable JWT
# https://github.com/amitripshtos/starlette-jwt
def on_auth_error(request, exc):
    return JSONResponse({"error": str(exc), "success": False}, status_code=401)
app.add_middleware(AuthenticationMiddleware, on_error=on_auth_error, backend=JWTAuthenticationBackend(secret_key=JWT_KEY, algorithm=JWT_ALGORITHM, prefix='JWT'))


# Add a generic exception handler
@app.exception_handler(HTTPException)
async def http_exception(request, exc):
    return JSONResponse({"error": exc.detail, "success": False}, status_code=exc.status_code)


# example authenticated route
# @app.route('/example')
# @requires('authenticated')
# async def index(request):
#    return JSONResponse({'success': True})


mount.starlette(app, "/", graphql_app)

