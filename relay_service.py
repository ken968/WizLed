import httpx
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class RelayService:
    def __init__(self, ip_address: str, name: str = "Unknown", channels: int = 4):
        self.ip_address = ip_address
        self.name = name
        self.channels = channels
        self.base_url = f"http://{ip_address}"

    async def get_status(self):
        """Ambil status relay dari ESP32."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/status", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": "Gagal mengambil status", "code": response.status_code}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    async def control_channel(self, channel: int, state: str):
        """Kontrol satu channel relay."""
        try:
            payload = {
                "channel": channel,
                "state": state.upper()
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/control",
                    json=payload,
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                return {"error": "Gagal kontrol channel", "code": response.status_code}
        except Exception as e:
            logger.error(f"Error kontrol channel {channel}: {e}")
            return {"error": str(e), "status": "failed"}

    async def control_all(self, state: str):
        """Kirim perintah ke SEMUA channel SEKALIGUS secara paralel."""
        tasks = [self.control_channel(i, state) for i in range(1, self.channels + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {"status": "success", "detail": results}

class RelayManager:
    def __init__(self, config_path: str = "devices.json"):
        self.services = []
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for dev in config.get("relay_devices", []):
                    channels = dev.get("channels", 4)
                    self.services.append(RelayService(dev["ip"], dev["name"], channels=channels))
            logger.info(f"RelayManager diinisialisasi dengan {len(self.services)} perangkat.")
        except Exception as e:
            logger.error(f"Gagal memuat config relay: {e}")

    def get_service_by_name(self, name: str):
        for service in self.services:
            if service.name == name:
                return service
        return None
