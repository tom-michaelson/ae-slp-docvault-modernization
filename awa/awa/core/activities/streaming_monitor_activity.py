"""Activity for monitoring streaming events via API in real-time."""

import asyncio
import json
from typing import Any

import aiohttp
from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.env_config import EnvConfig

logger = get_logger(LoggerComponent.ACTIVITY)


@activity.defn(name="monitor_streaming_events")
async def monitor_streaming_events_activity(  # noqa: PLR0915
    session_id: str,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Monitor streaming events for a session via the API.

    This activity connects to the streaming API and logs events in real-time
    as they are emitted during agent execution.

    Args:
        session_id: The session identifier to monitor
        timeout_seconds: How long to monitor for events

    Returns:
        Dictionary with monitoring results and captured events

    """
    logger.info(f"🎯 MONITOR: Starting streaming event monitor for session: {session_id}")

    # Get API server configuration
    env_config = EnvConfig.get_env_config()
    api_host = env_config.awa_api_host
    api_port = env_config.awa_api_port

    # Build streaming API endpoint URL
    stream_url = f"http://{api_host}:{api_port}/api/v1/agents/stream/{session_id}/live"

    events_captured = []
    event_count = 0

    try:
        logger.info(f"🎯 MONITOR: Connecting to streaming endpoint: {stream_url}")

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(stream_url) as response:
            http_ok = 200
            if response.status != http_ok:
                logger.error(f"🎯 MONITOR: Failed to connect to streaming endpoint, status: {response.status}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status}",
                    "events_captured": 0,
                    "events": [],
                }

            logger.info("🎯 MONITOR: Connected to streaming endpoint, waiting for events...")

            # Read streaming events
            async for line in response.content:
                if not line:
                    continue

                line_text = line.decode("utf-8").strip()

                # Skip SSE protocol lines that aren't data
                if not line_text.startswith("data: "):
                    continue

                # Extract JSON data
                try:
                    event_data_str = line_text[6:]  # Remove 'data: ' prefix
                    event_data = json.loads(event_data_str)

                    event_count += 1
                    events_captured.append(event_data)

                    # Log the streaming event in real-time with full details
                    event_type = event_data.get("type", "unknown")
                    if event_type == "connection":
                        logger.info(f"🎯 MONITOR: [{event_count}] Connection established for session {session_id}")
                    elif event_type in ["stream_complete", "execution_complete", "execution_error"]:
                        logger.info(
                            f"🎯 MONITOR: [{event_count}] Stream completed for session {session_id} "
                            f"(event: {event_type})",
                        )
                        break
                    elif event_type == "error":
                        logger.error(
                            f"🎯 MONITOR: [{event_count}] Stream error: {event_data.get('message', 'Unknown error')}",
                        )
                        break
                    else:
                        # Real PydanticAI streaming event - log with full details
                        event_json = json.dumps(event_data, separators=(",", ":"))
                        max_log_length = 300
                        if len(event_json) > max_log_length:
                            logger.info(f"🎯 MONITOR: [{event_count}] 📡 {event_type}")
                            logger.info(f"   📡 DATA: {event_json[:max_log_length]}...")
                        else:
                            logger.info(f"🎯 MONITOR: [{event_count}] 📡 {event_type}")
                            logger.info(f"   📡 DATA: {event_json}")

                except json.JSONDecodeError as e:
                    logger.warning(f"🎯 MONITOR: Failed to parse event data: {line_text[:100]}... - {e}")
                    continue

        logger.info(f"🎯 MONITOR: Streaming monitor completed. Captured {event_count} events total.")

        return {
            "success": True,
            "events_captured": event_count,
            "events": events_captured,
            "session_id": session_id,
            "stream_url": stream_url,
        }

    except asyncio.CancelledError:
        logger.info(f"🎯 MONITOR: Streaming monitor cancelled for session {session_id}")
        return {
            "success": True,
            "error": "cancelled",
            "events_captured": event_count,
            "events": events_captured,
            "session_id": session_id,
        }
    except TimeoutError:
        logger.warning(f"🎯 MONITOR: Streaming monitor timed out after {timeout_seconds} seconds")
        return {
            "success": False,
            "error": "timeout",
            "events_captured": event_count,
            "events": events_captured,
            "session_id": session_id,
        }
    except Exception as e:
        logger.exception(f"🎯 MONITOR: Error during streaming monitor for session {session_id}")
        return {
            "success": False,
            "error": str(e),
            "events_captured": event_count,
            "events": events_captured,
            "session_id": session_id,
        }
