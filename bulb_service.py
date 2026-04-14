import asyncio
import json
import logging
from pywizlight import wizlight, PilotBuilder
from models import ColorModel

logger = logging.getLogger(__name__)

class WizService:
    def __init__(self, ip_address: str, name: str = "Unknown", max_retries: int = 10):
        self.ip_address = ip_address
        self.name = name
        self.max_retries = max_retries

    async def _get_light(self):
        """Helper untuk inisialisasi koneksi lampu."""
        return wizlight(self.ip_address)

    async def execute_with_retry(self, func, *args, **kwargs):
        """Wrapper untuk menjalankan fungsi dengan percobaan ulang (retry)."""
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                # Tambahkan timeout internal 5 detik per percobaan
                return await asyncio.wait_for(func(*args, **kwargs), timeout=5.0)
            except Exception as e:
                last_exception = e
                logger.warning(f"Percobaan {attempt}/{self.max_retries} gagal untuk {self.name} ({self.ip_address}): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5) # Jeda sebentar sebelum coba lagi
        
        logger.error(f"Semua {self.max_retries} percobaan gagal untuk {self.name}.")
        raise last_exception

    async def turn_on(self, color: ColorModel = None, brightness: int = None):
        """Menyalakan lampu dengan warna dan kecerahan opsional (dengan Retry)."""
        async def _action():
            light = await self._get_light()
            try:
                if color and brightness is not None:
                    pilot = PilotBuilder(rgb=(color.Red, color.Green, color.Blue), brightness=brightness)
                    await light.turn_on(pilot)
                else:
                    await light.turn_on()
                return True
            finally:
                await light.async_close()

        return await self.execute_with_retry(_action)

    async def turn_off(self):
        """Mematikan lampu (dengan Retry)."""
        async def _action():
            light = await self._get_light()
            try:
                await light.turn_off()
                return True
            finally:
                await light.async_close()

        return await self.execute_with_retry(_action)

    async def get_status(self):
        """Mendapatkan status saat ini (dengan Retry)."""
        async def _action():
            light = await self._get_light()
            try:
                state = await light.updateState()
                return {
                    "name": self.name,
                    "ip": self.ip_address,
                    "on": state.get_state(),
                    "brightness": state.get_brightness(),
                    "rgb": state.get_rgb()
                }
            finally:
                await light.async_close()

        try:
            return await self.execute_with_retry(_action)
        except Exception as e:
            return {"name": self.name, "ip": self.ip_address, "error": str(e)}

class WizManager:
    def __init__(self, config_path: str = "devices.json"):
        self.services = []
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                for dev in config.get("wiz_devices", []):
                    self.services.append(WizService(dev["ip"], dev["name"]))
            logger.info(f"WizManager diinisialisasi dengan {len(self.services)} perangkat.")
        except Exception as e:
            logger.error(f"Gagal memuat config devices: {e}")

    async def broadcast_turn_on(self, color: ColorModel = None, brightness: int = None):
        """Mengirim perintah NYALA ke semua lampu secara PARALEL agar tidak saling menunggu."""
        tasks = [service.turn_on(color, brightness) for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def broadcast_turn_off(self):
        """Mengirim perintah MATI ke semua lampu secara PARALEL."""
        tasks = [service.turn_off() for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def get_all_statuses(self):
        """Mengambil status semua lampu secara PARALEL."""
        tasks = [service.get_status() for service in self.services]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
