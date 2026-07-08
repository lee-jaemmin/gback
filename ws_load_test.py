import asyncio
import sys

import websockets


active_count = 0
active_lock = asyncio.Lock()


async def connect_client(index: int, url: str):
    global active_count

    while True:
        try:
            async with websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
                close_timeout=5,
            ) as websocket:
                async with active_lock:
                    active_count += 1
                    print(f"connected {index} active={active_count}")

                try:
                    async for _ in websocket:
                        pass
                finally:
                    async with active_lock:
                        active_count -= 1
                        print(f"disconnected {index} active={active_count}")
        except Exception as e:
            print(f"connect failed {index}: {type(e).__name__}: {e}")

        await asyncio.sleep(2)


async def main():
    if len(sys.argv) != 3:
        print("Usage: python3 ws_load_test.py <websocket-url> <connection-count>")
        raise SystemExit(1)

    url = sys.argv[1]
    count = int(sys.argv[2])

    tasks = []
    for index in range(count):
        tasks.append(asyncio.create_task(connect_client(index, url)))
        await asyncio.sleep(0.05)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
