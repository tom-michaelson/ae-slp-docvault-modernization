from temporalio import activity

from awa.sdk import constants


@activity.defn(name=constants.ACTIVITY_SAY_HELLO)
async def say_hello_activity(name: str) -> str:
    """Return a greeting.

    Args:
        name: The name to include in the greeting.

    Returns:
        A greeting string in the format "Hello, {name}!".

    """
    activity.logger.info(f"Hello, {name} (from activity logger)!")
    return f"Hello, {name}!"
