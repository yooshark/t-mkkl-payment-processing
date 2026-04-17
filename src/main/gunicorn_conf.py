from uvicorn_worker import UvicornWorker as BaseUvicornWorker


class CustomUvicornWorker(BaseUvicornWorker):
    CONFIG_KWARGS = {
        "forwarded_allow_ips": "*",
        "proxy_headers": True,
    }
