import asyncio
import random
import socket
import sys
from urllib.parse import urlsplit

import websockets


active_count = 0
active_lock = asyncio.Lock()


async def connect_client(index: int, url: str, connect_host: str, connect_port: int):
    global active_count

    while True:
        try:
            async with websockets.connect(
                url,
                host=connect_host,
                port=connect_port,
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

        await asyncio.sleep(random.uniform(3, 10))


async def main():
    if len(sys.argv) != 3:
        print("Usage: python3 ws_load_test.py <websocket-url> <connection-count>")
        raise SystemExit(1)

    url = sys.argv[1]
    count = int(sys.argv[2])
    parsed_url = urlsplit(url)
    if parsed_url.scheme not in {"ws", "wss"} or not parsed_url.hostname:
        print("Invalid websocket URL")
        raise SystemExit(1)

    connect_port = parsed_url.port or (443 if parsed_url.scheme == "wss" else 80)
    addresses = socket.getaddrinfo(
        parsed_url.hostname,
        connect_port,
        type=socket.SOCK_STREAM,
    )
    connect_host = next(
        (address[4][0] for address in addresses if address[0] == socket.AF_INET),
        addresses[0][4][0],
    )
    print(f"resolved {parsed_url.hostname} -> {connect_host}")

    tasks = []
    for index in range(count):
        tasks.append(
            asyncio.create_task(
                connect_client(index, url, connect_host, connect_port)
            )
        )
        await asyncio.sleep(0.2)

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
