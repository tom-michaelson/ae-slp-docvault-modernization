"""Entry point for running the AWA API server as a standalone service."""

from awa.core.api.api import start_api_server

if __name__ == "__main__":
    start_api_server()
