import asyncio
import json
import os
import sys

# Menambahkan path folder utama agar bisa import dari bulb_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bulb_service import WizService

async def test_bulb_with_retry(name, ip):
    print(f"--- Mengetes {name} ({ip}) ---")
    # Menggunakan WizService yang sudah punya fitur Auto-Retry 5x
    service = WizService(ip, name, max_retries=5)
    
    status = await service.get_status()
    
    if "error" not in status:
        print(f"[v] BERHASIL: {name} merespon setelah percobaan ulang.")
        print(f"    Status: {'NYALA' if status['on'] else 'MATI'}, Kecerahan: {status['brightness']}")
    else:
        print(f"[!] GAGAL TOTAL: {name} tetap tidak terjangkau setelah 5x percobaan.")
        print(f"    Detail: {status['error']}")
    print()

async def main():
    # Mencari devices.json
    json_path = "devices.json"
    if not os.path.exists(json_path):
        json_path = os.path.join("..", "devices.json")

    try:
        with open(json_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: File devices.json tidak ditemukan!")
        return

    devices = config.get("devices", [])
    if not devices:
        print("Error: Tidak ada perangkat di devices.json")
        return

    print(f"Memulai tes koneksi (Auto-Retry 5x) untuk {len(devices)} perangkat...\n")
    
    for dev in devices:
        await test_bulb_with_retry(dev["name"], dev["ip"])

if __name__ == "__main__":
    asyncio.run(main())
