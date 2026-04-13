import asyncio
from pywizlight import discovery

async def main():
    import socket
    
    # Mencari tahu subnet lokal (misal: 192.168.1.255)
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    subnet_prefix = ".".join(local_ip.split(".")[:-1])
    broadcast_addr = f"{subnet_prefix}.255"

    print(f"IP Laptop Anda: {local_ip}")
    print(f"Mencari lampu WiZ di jaringan: {subnet_prefix}.x ...")
    
    # Mencoba dua metode broadcast (Global dan Subnet)
    print("Sedang menscan (mohon tunggu 5 detik)...")
    bulbs = await discovery.discover_lights(broadcast_space=broadcast_addr)
    
    # Jika tidak ketemu di subnet, coba global
    if not bulbs:
        bulbs = await discovery.discover_lights(broadcast_space="255.255.255.255")
    
    if not bulbs:
        print("\n[!] Tidak ada lampu WiZ yang ditemukan.")
        print("Pastikan lampu sudah menyala dan terhubung ke WiFi yang sama dengan laptop ini.")
    else:
        print(f"\n[v] Berhasil menemukan {len(bulbs)} lampu:")
        for bulb in bulbs:
            # bulb.ip_address adalah IP-nya
            # bulb.mac adalah ID fisiknya (untuk membedakan antar lampu)
            print(f"---")
            print(f"IP Address : {bulb.ip_address}")
            print(f"MAC Address: {bulb.mac}")
        print("\nSilakan salin IP Address di atas ke file main.py bagian BULB_IP.")

if __name__ == "__main__":
    asyncio.run(main())
