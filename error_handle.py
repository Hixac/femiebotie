import asyncio
from requests import ConnectionError
from functools import wraps

def empty(e, *args, **kwargs):
    pass

def handle_exception(default_response=empty, conn_error=empty):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ConnectionError as e:
                result = conn_error(e, func, *args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                result = default_response(e, *args, **kwargs)
                if asyncio.iscoroutine(result):
                    await result
        return wrapper
    return decorator

async def connection_response(e, func, *args, **kwargs):
    max_retries = 3
    print("Getting here")
    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                await asyncio.sleep(delay)
            else:
                print("Сервер решил послать нахуй куда подальше")
                return
            
async def automatic_response(e, event, bot):
    print(f"Ошибка обработки команды: {e}")
    await bot.send_message("⚠️ Произошла ошибка при обработке команды", event.peer_id)
