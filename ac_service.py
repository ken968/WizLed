import httpx
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ACService:
    def __init__(self, ip_address: str, name: str = "Unknown"):
        self.ip_address = ip_address
        self.name = name
        self.base_url = f"http://{ip_address}"

    async def get_status(self):
        """Ambil status online dari ESP32 IR Controller."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/status", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                return {"error": "Gagal mengambil status AC", "code": response.status_code}
        except Exception as e:
            return {"error": str(e), "status": "failed"}

    async def control_ac(self, power: str, temperature: int):
        """Kirim perintah JSON ke AC."""
        try:
            payload = {
                "power": power.upper(),
                "temperature": temperature
            }
            logger.info(f"[AC] Mengirim perintah ke {self.name} ({self.ip_address}): {payload}")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/control",
                    json=payload,
                    timeout=5.0
                )
                if response.status_code == 200:
                    logger.info(f"[AC] Sukses kontrol {self.name}: {response.json()}")
                    return response.json()
                
                logger.error(f"[AC] Gagal kontrol {self.name}: {response.status_code} - {response.text}")
                return {"error": "Gagal kontrol AC", "code": response.status_code}
        except Exception as e:
            logger.exception(f"[AC] Error kontrol {self.name} ({self.ip_address}):")
            return {"error": repr(e), "status": "failed"}

class ACManager:
    def __init__(self, config_path: str = "devices.json"):
        self.services = []
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for dev in config.get("ac_devices", []):
                    self.services.append(ACService(dev["ip"], dev["name"]))
            logger.info(f"ACManager diinisialisasi dengan {len(self.services)} perangkat AC.")
        except Exception as e:
            logger.error(f"Gagal memuat config AC: {e}")

    def get_service_by_name(self, name: str):
        for service in self.services:
            if service.name == name:
                return service
        return None
