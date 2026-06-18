from temporalio import activity


@activity.defn
async def say_hello(name: str) -> str:
    greeting = f"Hello, {name}!"
    activity.logger.info(f"Generated greeting: {greeting}")
    return greeting
