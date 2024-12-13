# chat_handler/adapters.py
import logging
import inspect

log = logging.getLogger(__name__)

async def start_adapters(input_adapter, output_adapter):
    start_method = getattr(input_adapter, "start", None)
    if callable(start_method) and inspect.iscoroutinefunction(start_method):
        await start_method()

    start_method = getattr(output_adapter, "start", None)
    if callable(start_method) and inspect.iscoroutinefunction(start_method):
        await start_method()

async def stop_adapters(input_adapter, output_adapter):
    stop_method = getattr(input_adapter, "stop", None)
    if callable(stop_method) and inspect.iscoroutinefunction(stop_method):
        try:
            await stop_method()
        except Exception as e:
            log.debug(f"Error stopping input_adapter: {e}")

    stop_method = getattr(output_adapter, "stop", None)
    if callable(stop_method) and inspect.iscoroutinefunction(stop_method):
        try:
            await stop_method()
        except Exception as e:
            log.debug(f"Error stopping output_adapter: {e}")

