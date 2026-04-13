import asyncio
from pywizlight import wizlight, PilotBuilder

async def main():
    # Replace with your bulb's IP address
    ip_address = "10.1.42.69" 
    light = wizlight(ip_address) 

    try:
        # Set to a specific RGB color and brightness
        await light.turn_on(PilotBuilder(rgb=(255, 0, 255), brightness=255))
        
        # Sync and verify state
        state = await light.updateState()
        print(f"Bulb brightness: {state.get_brightness()}")
    
    finally:
        # Explicitly close the connection to prevent "Event loop is closed" error
        await light.async_close()

if __name__ == "__main__":
    asyncio.run(main())