"""
===============================================================================
server.py: FastAPI Web Engine for SlabOS
===============================================================================
"""

import os
import signal
import threading
import time
import json
import shutil
import io
import httpx
import uvicorn
import psutil
import qrcode
import qrcode.image.svg
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from project import get_system_vitals
from slabos.auth.service import AuthService
from slabos.config.manager import ConfigManager

# =============================================================================
# CORE UTILITIES & PATH RESOLUTION
# =============================================================================
app = FastAPI(title="SlabOS Web Engine")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)


class ChatPayload(BaseModel):
    prompt: str = Field(..., min_length=1, description="The user's message")
    model: str = Field(..., description="The name of the active Ollama model")
    images: Optional[List[str]] = Field(default=[], description="Base64 encoded images for vision models")


config_manager = ConfigManager()
auth_service = AuthService(config_manager)


def check_access(provided_pin: str) -> tuple[bool, bool]:
    """Return the authorization result for an API PIN."""
    return auth_service.authenticate(provided_pin, app.state.session_pin)

def get_usb_drives() -> dict:
    """Scans the host OS for attached external/USB drives."""
    usbs = {}
    try:
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt' and part.device != 'C:\\':
                usbs[f"USB_Drive_{part.device[0]}"] = part.mountpoint
            elif os.name != 'nt' and ('/media/' in part.mountpoint or '/mnt/' in part.mountpoint or '/Volumes/' in part.mountpoint):
                usbs[f"USB_{os.path.basename(part.mountpoint)}"] = part.mountpoint
    except Exception:
        pass
    return usbs


def resolve_vault_path(subpath: str) -> tuple[str, str]:
    """Dynamically routes paths to local Vault or physical USB drives."""
    usbs = get_usb_drives()
    
    for usb_name, usb_path in usbs.items():
        if subpath == usb_name or subpath.startswith(usb_name + "/"):
            relative = subpath[len(usb_name):].lstrip("/")
            target = os.path.abspath(os.path.join(usb_path, relative))
            return target, usb_path
            
    media_dir = os.path.abspath(app.state.media_dir)
    target = os.path.abspath(os.path.join(media_dir, subpath))
    return target, media_dir


# =============================================================================
# SECTION 1: DASHBOARD & TELEMETRY
# =============================================================================
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request, pin: str = ""):
    _, is_admin = check_access(pin)
    
    return templates.TemplateResponse(request, "index.html", {
        "request": request, 
        "active_model": getattr(app.state, "active_model", "Disabled"),
        "enable_ai": getattr(app.state, "enable_ai", True),
        "enable_media": getattr(app.state, "enable_media", True),
        "is_admin": is_admin
    })


@app.get("/api/vitals")
async def api_get_vitals(pin: str):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    vitals = get_system_vitals()
    return {
        "status": "online",
        "cpu_pct": vitals.get("cpu_pct", 0.0),
        "ram_pct": vitals.get("ram_pct", 0.0),
        "cpu_temp": vitals.get("cpu_temp", -1.0),
        "disk_free_gb": vitals.get("disk_free_gb", 0.0)
    }


# =============================================================================
# SECTION 2: VISION MODEL PROBING & AI CHAT STREAMING
# =============================================================================
@app.get("/api/ai/check-vision")
async def check_vision_support(pin: str):
    """Probes whether the active Ollama model supports multimodal vision inputs."""
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    active_model = getattr(app.state, "active_model", "Disabled")
    if active_model == "Disabled":
        return {"is_vision": False, "model": active_model}
        
    vision_keywords = ["llava", "vision", "qwen2-vl", "moondream", "bakllava", "llama3.2-vision", "minicpm", "cogvlm"]
    model_lower = active_model.lower()
    is_vision = any(kw in model_lower for kw in vision_keywords)
    
    return {"is_vision": is_vision, "model": active_model}


async def stream_ollama_generator(prompt: str, model_name: str, images: List[str] = []) -> AsyncGenerator[str, None]:
    ollama_url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True
    }
    
    if images and len(images) > 0:
        payload["images"] = images

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            async with client.stream("POST", ollama_url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        token = data.get("response", "")
                        yield f"data: {json.dumps({'text': token})}\n\n"
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"


@app.post("/api/chat")
async def api_chat_stream(payload: ChatPayload, pin: str):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    return StreamingResponse(
        stream_ollama_generator(payload.prompt, payload.model, payload.images or []),
        media_type="text/event-stream"
    )


# =============================================================================
# SECTION 3: ADMIN COMMAND CENTER
# =============================================================================
def execute_delayed_shutdown():
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGINT)


@app.post("/api/system/shutdown")
async def shutdown_server(pin: str):
    if not verify_api_pin(pin, app.state.session_pin):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    threading.Thread(target=execute_delayed_shutdown).start()
    return {"status": "success", "message": "Node shutdown sequence initiated."}


@app.post("/api/system/guest")
async def create_guest_pin(request: Request, pin: str):
    is_auth, is_admin = check_access(pin)
    if not is_admin:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        new_guest = auth_service.create_guest_pin()

        base_url = str(request.base_url).rstrip("/")
        guest_url = f"{base_url}/?pin={new_guest}"

        # Generate SVG QR Code (Zero external library dependencies)
        factory = qrcode.image.svg.SvgPathImage
        img = qrcode.make(guest_url, image_factory=factory)
        stream = io.BytesIO()
        img.save(stream)
        svg_qr = stream.getvalue().decode("utf-8")

        return {
            "status": "success",
            "guest_pin": new_guest,
            "guest_url": guest_url,
            "qr_svg": svg_qr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SECTION 4: MEDIA VAULT ENDPOINTS
# =============================================================================
@app.get("/api/media/list")
async def list_media_files(pin: str, subpath: str = ""):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    target_dir, base_dir = resolve_vault_path(subpath)
    
    if not target_dir.startswith(base_dir) or not os.path.isdir(target_dir):
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    try:
        items = os.listdir(target_dir)
        folders, files = [], []
        usbs = get_usb_drives()
        
        for item in items:
            item_path = os.path.join(target_dir, item)
            if os.path.isdir(item_path):
                if subpath == "" and item in usbs.keys():
                    continue
                folders.append(item)
            elif os.path.isfile(item_path):
                files.append(item)
        
        folders.sort()
        files.sort()
        
        if subpath == "":
            for usb_name in usbs.keys():
                folders.insert(0, usb_name)
        
        return {"status": "success", "current_path": subpath, "folders": folders, "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/api/media/download/{filepath:path}")
async def download_media(filepath: str, pin: str):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    target_path, base_dir = resolve_vault_path(filepath)
    if not target_path.startswith(base_dir) or not os.path.isfile(target_path):
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    return FileResponse(target_path)


@app.post("/api/media/upload")
async def upload_media(pin: str = Form(...), subpath: str = Form(""), file: UploadFile = File(...)):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    target_dir, base_dir = resolve_vault_path(subpath)
    if not target_dir.startswith(base_dir) or not os.path.isdir(target_dir):
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    file_path = os.path.join(target_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        return {"status": "success", "filename": file.filename}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.post("/api/media/mkdir")
async def create_folder(pin: str = Form(...), subpath: str = Form(""), folder_name: str = Form(...)):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    target_dir, base_dir = resolve_vault_path(subpath)
    new_dir = os.path.abspath(os.path.join(target_dir, folder_name))
    
    if not new_dir.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    os.makedirs(new_dir, exist_ok=True)
    return {"status": "success"}


@app.post("/api/media/delete")
async def delete_item(pin: str = Form(...), target_path: str = Form(...)):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    full_path, base_dir = resolve_vault_path(target_path)
    if not full_path.startswith(base_dir) or full_path == base_dir:
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    elif os.path.isfile(full_path):
        os.remove(full_path)
        
    return {"status": "success"}


@app.post("/api/media/rename")
async def rename_item(pin: str = Form(...), old_path: str = Form(...), new_name: str = Form(...)):
    is_auth, _ = check_access(pin)
    if not is_auth:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    source_path, base_dir = resolve_vault_path(old_path)
    parent_dir = os.path.dirname(source_path)
    dest_path = os.path.abspath(os.path.join(parent_dir, new_name))
    
    if not dest_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Forbidden Path")
        
    os.rename(source_path, dest_path)
    return {"status": "success"}


# =============================================================================
# SECTION 5: IGNITION ENGINE
# =============================================================================
def run_web_server(host: str, port: int, pin: str, media_dir: str, active_model: str):
    app.state.session_pin = pin
    app.state.media_dir = media_dir
    app.state.active_model = active_model
    app.state.enable_ai = (active_model != "Disabled")
    app.state.enable_media = (media_dir != "Disabled" and media_dir != "")
    
    print(f"\n[System] Igniting ASGI Web Engine on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")