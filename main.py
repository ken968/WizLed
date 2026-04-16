import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ControlRequest, parse_warna, RelayControlRequest, BulkControlRequest, ACControlRequest
from bulb_service import WizManager
from relay_service import RelayManager
from ac_service import ACManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="WiZ Multi-Controller Backend")

# Aktifkan CORS agar UI dari device lain bisa mengakses API ini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration: Inisialisasi Manager
wiz_manager = WizManager("devices.json")
relay_manager = RelayManager("devices.json")
ac_manager = ACManager("devices.json")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "WiZ and Relay Unified Backend is running",
        "endpoints": {
            "docs": "/docs",
            "devices": "/devices",
            "relay_status": "/relay/status",
            "bulb_status": "/status",
            "ac_status": "/ac/status"
        }
    }

@app.post("/control")
async def control_lights(request: ControlRequest):
    logger.info(f"Menerima request control: {request}")
    try:
        color = parse_warna(request.Warna)
        results = await wiz_manager.broadcast_turn_on(color=color, brightness=request.Kecerahan)
        
        # Susun laporan detail per perangkat
        report = []
        for i, res in enumerate(results):
            dev = wiz_manager.services[i]
            if isinstance(res, Exception):
                report.append({"name": dev.name, "ip": dev.ip_address, "status": "failed", "error": str(res)})
            else:
                report.append({"name": dev.name, "ip": dev.ip_address, "status": "success"})

        # Cek apakah ada yang sukses sama sekali
        success_count = sum(1 for r in report if r["status"] == "success")
        
        return {
            "status": "partial_success" if success_count < len(report) else "success",
            "summary": {
                "total": len(report),
                "success": success_count,
                "failed": len(report) - success_count
            },
            "devices": report,
            "data_sent": {
                "rgb": (color.Red, color.Green, color.Blue),
                "brightness": request.Kecerahan
            }
        }
    except Exception as e:
        logger.error(f"Critical error in control_lights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/turn_on")
async def turn_on_all():
    try:
        await wiz_manager.broadcast_turn_on()
        return {"status": "success", "message": "Semua lampu dinyalakan"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/turn_off")
async def turn_off_all():
    try:
        await wiz_manager.broadcast_turn_off()
        return {"status": "success", "message": "Semua lampu dimatikan"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_all_status():
    try:
        statuses = await wiz_manager.get_all_statuses()
        return {"status": "success", "devices": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def list_devices():
    """Mengembalikan daftar perangkat yang terdaftar di konfigurasi."""
    return {
        "wiz_count": len(wiz_manager.services),
        "relay_count": len(relay_manager.services),
        "ac_count": len(ac_manager.services),
        "wiz_devices": [{"name": s.name, "ip": s.ip_address} for s in wiz_manager.services],
        "relay_devices": [{"name": s.name, "ip": s.ip_address} for s in relay_manager.services],
        "ac_devices": [{"name": s.name, "ip": s.ip_address} for s in ac_manager.services]
    }

# --- Relay Routes ---
@app.get("/relay/status")
async def get_relay_status():
    try:
        results = []
        for service in relay_manager.services:
            status = await service.get_status()
            results.append(status)
        return {"relays": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/relay/control")
async def control_relay(request: RelayControlRequest):
    service = relay_manager.get_service_by_name(request.device_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Device {request.device_name} tidak ditemukan")
    
    if request.channel < 1 or request.channel > 4:
         raise HTTPException(status_code=400, detail="Channel harus antara 1-4")

    result = await service.control_channel(request.channel, request.state)
    return result

@app.post("/relay/control-all")
async def control_all_relays(request: BulkControlRequest):
    service = relay_manager.get_service_by_name(request.device_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Device {request.device_name} tidak ditemukan")
    
    result = await service.control_all(request.state)
    return result

# --- AC Routes ---
@app.get("/ac/status")
async def get_ac_status():
    try:
        results = []
        for service in ac_manager.services:
            status = await service.get_status()
            results.append(status)
        return {"ac": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ac/control")
async def control_ac(request: ACControlRequest):
    service = ac_manager.get_service_by_name(request.device_name)
    if not service:
        raise HTTPException(status_code=404, detail=f"Device {request.device_name} tidak ditemukan")

    result = await service.control_ac(
        power=request.power,
        temperature=request.temperature
    )
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
