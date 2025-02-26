import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8001"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print("Datos recibidos:", message)

asyncio.run(test_websocket())
