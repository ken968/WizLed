import json
import logging
from typing import Union
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ColorModel(BaseModel):
    Red: int = Field(..., ge=0, le=255)
    Green: int = Field(..., ge=0, le=255)
    Blue: int = Field(..., ge=0, le=255)

class ControlRequest(BaseModel):
    # Warna bisa berupa string (JSON stringified) atau objek ColorModel
    Warna: Union[str, ColorModel]
    Kecerahan: int = Field(..., ge=0, le=255)

    model_config = {
        "json_schema_extra": {
            "example": {
                "Warna": {
                    "Red": 255,
                    "Green": 0,
                    "Blue": 0
                },
                "Kecerahan": 255
            }
        }
    }

def parse_warna(warna: Union[str, ColorModel]) -> ColorModel:
    """Mengolah field Warna jika dikirim sebagai string JSON."""
    if isinstance(warna, str):
        try:
            data = json.loads(warna)
            return ColorModel(**data)
        except Exception as e:
            logger.error(f"Gagal memparse field Warna: {e}")
            raise ValueError(f"Format JSON 'Warna' tidak valid: {e}")
    return warna

# --- Relay Models ---
class RelayControlRequest(BaseModel):
    device_name: str
    channel: int
    state: str  # "ON" atau "OFF"

class BulkControlRequest(BaseModel):
    device_name: str
    state: str  # "ON" atau "OFF"

# --- AC Models ---
class ACControlRequest(BaseModel):
    device_name: str
    power: str = "ON"       # "ON" atau "OFF"
    temperature: int = 24   # 16 - 30
