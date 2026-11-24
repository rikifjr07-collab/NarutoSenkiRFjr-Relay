import asyncio
import os
import random
import websockets

# Menyimpan daftar room: { "4821": {"host": ws, "clients": set()} }
rooms = {}

def generate_code():
    while True:
        code = str(random.randint(1000, 9999))
        if code not in rooms:
            return code

async def handler(websocket):
    room_code = None
    role = None
    try:
        async for message in websocket:
            # 1. Host membuat room
            if message == "CREATE":
                room_code = generate_code()
                rooms[room_code] = {"host": websocket, "clients": set()}
                role = "HOST"
                await websocket.send(f"ROOM_CODE:{room_code}")

            # 2. Client bergabung ke room ("JOIN:4821")
            elif message.startswith("JOIN:"):
                code = message.split(":", 1)[1].strip()
                if code in rooms and len(rooms[code]["clients"]) < 5:
                    room_code = code
                    rooms[code]["clients"].add(websocket)
                    role = "CLIENT"
                    await websocket.send("JOIN_OK")
                    await rooms[code]["host"].send("NEW_CLIENT")
                else:
                    await websocket.send("ERR_ROOM")

            # 3. Teruskan semua paket game ("R:<kode>:H:<isi>" atau "R:<kode>:C:<isi>")
            elif message.startswith("R:"):
                parts = message.split(":", 3)
                if len(parts) == 4:
                    _, code, sender_role, payload = parts
                    if code in rooms:
                        if sender_role == "H":
                            # Broadcast dari Host ke semua Client
                            for client_ws in list(rooms[code]["clients"]):
                                try:
                                    await client_ws.send(payload)
                                except:
                                    pass
                        elif sender_role == "C":
                            # Kirim dari Client ke Host
                            try:
                                await rooms[code]["host"].send(payload)
                            except:
                                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Bersihkan room jika Host atau Client terputus
        if room_code in rooms:
            if role == "HOST":
                for client_ws in list(rooms[room_code]["clients"]):
                    try:
                        await client_ws.close()
                    except:
                        pass
                del rooms[room_code]
            elif role == "CLIENT":
                rooms[room_code]["clients"].discard(websocket)

async def main():
    port = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handler, "0.0.0.0", port, ping_interval=20, ping_timeout=20):
        print(f"Server WebSocket Naruto Senki berjalan di port {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
