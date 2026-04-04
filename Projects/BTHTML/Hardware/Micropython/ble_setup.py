import asyncio
import aioble
import bluetooth
import network
import time

# These MUST match the HTML file exactly
_SERVICE_UUID = bluetooth.UUID('12345678-1234-5678-1234-56789abcdef0')
_CHAR_UUID = bluetooth.UUID('12345678-1234-5678-1234-56789abcdef1')

# 1. Setup BLE Service and Characteristic
_service = aioble.Service(_SERVICE_UUID)
_characteristic = aioble.Characteristic(
    _service, _CHAR_UUID, write=True, capture=True
)
aioble.register_services(_service)

async def connect_wifi(ssid, password):
    print(f"\n[Wi-Fi] Attempting to connect to: {ssid}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    # Wait up to 10 seconds for connection
    for _ in range(10):
        if wlan.isconnected():
            print("\n[Wi-Fi] Success! We are online.")
            print("[Wi-Fi] IP Address:", wlan.ifconfig()[0])
            return True
        await asyncio.sleep(1)
        
    print("\n[Wi-Fi] Failed. Incorrect password or out of range.")
    wlan.active(False)
    return False

async def ble_task():
    print("[BLE] Starting BLE Advertising...")
    print("[BLE] Waiting for phone/browser to connect to 'ESP32-Setup'...")
    
    while True:
        # 2. Broadcast our presence
        async with await aioble.advertise(
            250_000, 
            name="ESP32-Setup", 
            services=[_SERVICE_UUID]
        ) as connection:
            print(f"\n[BLE] Connected to: {connection.device}")
            
            # 3. Wait for the browser to write the credentials
            conn, data = await _characteristic.written()
            credentials = data.decode('utf-8')
            print(f"[BLE] Received encrypted payload!")
            
            try:
                # 4. Split and connect
                ssid, password = credentials.split(',')
                await connect_wifi(ssid, password)
            except ValueError:
                print("[Error] Data was not in 'SSID,PASSWORD' format.")
            
            print("[BLE] Disconnecting...")
            await connection.disconnect()

async def main():
    await ble_task()

# Start the asynchronous event loop
asyncio.run(main())