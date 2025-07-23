import asyncio
from requests import ConnectionError
from functools import wraps

def empty(e, *args, **kwargs):
    pass

async def _call(callee):
    if asyncio.iscoroutine(callee):
        await callee
        
def handle_exception(default_response=empty, conn_error=empty):
    
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                else:
                    return result
            except ConnectionError as e:
                await _call(conn_error(e, func, *args, **kwargs))
            except Exception as e:
                await _call(default_response(e, *args, **kwargs))
        return wrapper
    
    return decorator

async def connection_response(e, func, *args, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await _call(func(*args, **kwargs))
        except Exception as e:
            if attempt < max_retries - 1:
                delay = 2 ** attempt
                await asyncio.sleep(delay)
            else:
                print("Сервер решил послать нахуй куда подальше")
                return
            
async def automatic_response(e, event):
    import traceback
    print(f"Ошибка обработки команды: {e}")
    traceback.print_exc()
