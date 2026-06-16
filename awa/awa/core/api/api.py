import asyncio
import threading

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from awa.core.api.routes.versions.v1.router import router as v1_router
from awa.core.api.socketio_server import get_socketio_app
from awa.core.api.versioning import API_PREFIX
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.version_utils import get_project_version

# Initialize logging before creating the API instance
init_logging()


class Api:
    app: FastAPI

    def __init__(self) -> None:
        env_config = EnvConfig.get_env_config()

        # Configure OpenAPI security scheme for Swagger UI
        openapi_security = {}
        if env_config.public_auth_mode.lower() == "cognito":
            openapi_security = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter your JWT access token obtained from Cognito authentication",
                },
            }

        self.app = FastAPI(
            title="AWA API",
            description="Agentic Workflow Accelerator API",
            version=get_project_version(),
            openapi_components={
                "securitySchemes": openapi_security,
            }
            if openapi_security
            else None,
        )
        self._setup_routes()
        self._add_middleware()
        self._mount_socketio()
        self._server = None
        self._shutdown_event = threading.Event()
        self.logger = get_logger(LoggerComponent.API)

    def _setup_routes(self) -> None:
        self.app.include_router(
            v1_router,
            prefix=API_PREFIX,
        )

    def _add_middleware(self) -> None:
        # Allow api requests from ui, to be further configured
        # See AWA-318 - https://slalom.atlassian.net/browse/AWA-318
        env_config = EnvConfig.get_env_config()
        allowed_origins = [
            f"http://{env_config.awa_ui_host}:{env_config.awa_ui_port}",
            "http://localhost:8000",  # Allow localhost for development
            "http://ui:8000",  # Allow UI container in Docker
        ]

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Accept"],
            allow_credentials=True,
            max_age=3600,  # Cache preflight requests for 1 hour
        )

    def _mount_socketio(self) -> None:
        """Mount Socket.IO server for real-time log streaming."""
        socketio_app = get_socketio_app()
        self.app.mount("/socket.io", socketio_app)

    def run(self) -> None:
        self.logger.info("Starting FastAPI Server...")
        # Disable uvicorn's default logging config so our InterceptHandler handles everything
        config = uvicorn.Config(
            self.app,
            host=EnvConfig.get_env_config().awa_api_host,
            port=EnvConfig.get_env_config().awa_api_port,
            log_level="info",
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "loggers": {
                    "uvicorn": {"handlers": [], "propagate": True},
                    "uvicorn.error": {"handlers": [], "propagate": True},
                    "uvicorn.access": {"handlers": [], "propagate": True},
                },
            },
            access_log=True,
        )
        self._server = uvicorn.Server(config)
        # Run until shutdown event is set
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server_task = loop.create_task(self._server.serve())
        try:
            while not self._shutdown_event.is_set():
                loop.run_until_complete(asyncio.sleep(0.1))
        finally:
            self._server.should_exit = True
            loop.run_until_complete(server_task)
            loop.close()

    def run_docker(self) -> None:
        """Run the FastAPI server using uvicorn.run (recommended for Docker)."""
        self.logger.info("Starting FastAPI Server (Docker mode)...")
        uvicorn.run(
            self.app,
            host=EnvConfig.get_env_config().awa_api_host,
            port=EnvConfig.get_env_config().awa_api_port,
            log_level="info",
            log_config={
                "version": 1,
                "disable_existing_loggers": False,
                "loggers": {
                    "uvicorn": {"handlers": [], "propagate": True},
                    "uvicorn.error": {"handlers": [], "propagate": True},
                    "uvicorn.access": {"handlers": [], "propagate": True},
                },
            },
            access_log=True,
        )

    def shutdown(self) -> None:
        self._shutdown_event.set()


async def _run_api_server() -> None:
    """Run the FastAPI server."""
    api = Api()
    thread = threading.Thread(target=api.run)
    thread.daemon = True
    thread.start()

    event = asyncio.Event()
    try:
        await event.wait()
    except asyncio.CancelledError:
        api.shutdown()
        thread.join()


def start_api_server() -> None:
    """Start the FastAPI server for Docker deployment.

    This function is designed to be called directly from the command line
    or Docker entry point to start only the API service without other dependencies.
    """
    logger = get_logger(LoggerComponent.API)
    logger.info("Starting AWA API Server for Docker deployment...")
    api = Api()
    try:
        api.run_docker()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping API server...")
        api.shutdown()
    except Exception:
        logger.exception("API server error")
        raise
