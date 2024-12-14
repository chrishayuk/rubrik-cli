# response_utils.py
import asyncio
import logging
from rich.panel import Panel
from rich.text import Text
from rich.live import Live

log = logging.getLogger(__name__)

async def async_token_generator(responder_handler, question: str, conversation):
    stream_gen = responder_handler.get_response_stream(question, conversation)
    if hasattr(stream_gen, '__aiter__'):
        async for token in stream_gen:
            yield token
    else:
        for token in stream_gen:
            yield token
            await asyncio.sleep(0)  # Let event loop run

async def safe_get_response(get_response_func, question: str):
    try:
        return await get_response_func(question)
    except Exception as e:
        log.debug(f"Failed to get response: {e}")
        return ""

async def get_response(responder_handler, output_adapter, question: str, conversation, stream: bool, local_name: str, console):
    # Similar logic as before, but externalized
    if stream and hasattr(responder_handler, "get_response_stream"):
        answer = ""
        style_name = "assistant"
        display_role = local_name

        text_content = Text("", style=style_name)
        panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
        
        token_buffer = []
        tokens_before_update = 5

        with Live(panel, console=console, refresh_per_second=10) as live:
            async for token in async_token_generator(responder_handler, question, conversation):
                token_buffer.append(token)
                if '\n' in token or len(token_buffer) >= tokens_before_update:
                    flushed = ''.join(token_buffer)
                    token_buffer.clear()

                    answer += flushed
                    text_content = Text(answer, style=style_name)
                    updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                    live.update(updated_panel)
                    live.refresh()

                    try:
                        await output_adapter.write_message({
                            "role": "Responder",
                            "message": flushed,
                            "partial": True
                        })
                    except Exception as e:
                        log.debug(f"Failed streaming token batch: {e}")
                        break

            # Flush remaining tokens if any
            if token_buffer:
                flushed = ''.join(token_buffer)
                answer += flushed
                text_content = Text(answer, style=style_name)
                updated_panel = Panel(text_content, title=display_role, border_style=style_name, expand=True)
                live.update(updated_panel)
                live.refresh()

                try:
                    await output_adapter.write_message({
                        "role": "Responder",
                        "message": flushed,
                        "partial": True
                    })
                except Exception as e:
                    log.debug(f"Failed streaming final token batch: {e}")

        try:
            await output_adapter.write_message({"role": "Responder", "partial": False})
        except Exception as e:
            log.debug(f"Failed to send final partial=False message: {e}")

        return answer
    else:
        # Non-streaming mode
        if asyncio.iscoroutinefunction(responder_handler.get_response):
            answer = await responder_handler.get_response(question, conversation)
        else:
            answer = responder_handler.get_response(question, conversation)

        return answer
