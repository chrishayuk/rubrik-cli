import asyncio
import websockets

async def handler(ws):
    print("websocat connected!")
    async for msg in ws:
        print("Received:", msg)
        await ws.send("Echo: " + msg)

async def main():
    # `websockets.serve` returns a Serve object now
    async with websockets.serve(handler, "127.0.0.1", 8045):
        print("Server running on ws://127.0.0.1:8045")
        # Keep the server running forever
        await asyncio.Future()  # This will never complete

asyncio.run(main())
