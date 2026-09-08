"""
===============================================================================
SlabOS: Automated Headless Server Provisioner & Portable Local AI Node
===============================================================================
Author: Vansh Saini
License: MIT
===============================================================================
"""

import json
import hashlib
import os
import platform
import random
import secrets
import shutil
import string
import sys
import time
import ctypes
import io
import socket
import subprocess
from pathlib import Path

# Third-Party Dependencies
import psutil
import pyfiglet
import qrcode
import questionary
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from zeroconf import ServiceInfo, Zeroconf

console = Console()

# =============================================================================
# SECTION 1: CORE PURE FUNCTIONS
# =============================================================================

def recommend_ai_model(ram_gb: float, has_gpu: bool, disk_free_gb: float = 50.0) -> str:
    """Determines optimal AI model, enforcing a 5GB OS storage safety buffer."""
    SAFETY_BUFFER_GB = 5.0
    if disk_free_gb < (2.0 + SAFETY_BUFFER_GB):
        return "" 
    if ram_gb < 6.0:
        return "qwen2.5:1.5b" if has_gpu else "llama3.2:1b"
    elif ram_gb < 12.0:
        if disk_free_gb >= (5.0 + SAFETY_BUFFER_GB):
            return "qwen2.5:7b" if has_gpu else "gemma2:2b"
        return "qwen2.5:1.5b" if has_gpu else "llama3.2:1b"
    elif ram_gb < 16.0:
        if disk_free_gb >= (5.0 + SAFETY_BUFFER_GB):
            return "deepseek-r1:7b" if has_gpu else "llama3.2:3b"
        return "gemma2:2b"
    else:
        if disk_free_gb >= (5.0 + SAFETY_BUFFER_GB):
            return "deepseek-r1:7b" if has_gpu else "llama3:8b"
        return "llama3.2:3b"

def calculate_zram_size(total_ram_gb: float, max_ratio: float = 0.5) -> float:
    """Calculates compressed ZRAM swap size allocation in Gigabytes."""
    if not isinstance(total_ram_gb, (int, float)) or total_ram_gb <= 0:
        return 0.0
    MAX_ZRAM_CAP_GB = 8.0
    return round(min(float(total_ram_gb) * max_ratio, MAX_ZRAM_CAP_GB), 2)

def verify_path_security(requested_path: str, base_dir: str) -> bool:
    """Prevents path traversal vulnerabilities on the media server."""
    if not isinstance(requested_path, str) or not isinstance(base_dir, str):
        return False
    try:
        base = Path(base_dir).resolve()
        target = (base / requested_path).resolve()
        return target.is_relative_to(base) and target.is_file()
    except (ValueError, TypeError, RuntimeError):
        return False

def format_telemetry_payload(cpu_pct: float, ram_pct: float, cpu_temp: float, active_model: str) -> dict:
    """Formats raw hardware stats into a standardized JSON response."""
    CRITICAL_TEMP_C = 85.0
    safe_cpu = float(cpu_pct) if isinstance(cpu_pct, (int, float)) else 0.0
    safe_ram = float(ram_pct) if isinstance(ram_pct, (int, float)) else 0.0
    safe_temp = float(cpu_temp) if isinstance(cpu_temp, (int, float)) else -1.0
    safe_model = str(active_model).strip() if isinstance(active_model, str) and active_model.strip() else "None"
    
    return {
        "status": "online",
        "cpu_usage_pct": round(safe_cpu, 1),
        "ram_usage_pct": round(safe_ram, 1),
        "cpu_temp_celsius": round(safe_temp, 1) if safe_temp > 0 else -1.0,
        "thermal_alert": safe_temp >= CRITICAL_TEMP_C,
        "active_model": safe_model,
        "timestamp": int(time.time())
    }

def sanitize_mdns_hostname(raw_name: str) -> str:
    """Sanitizes user input string into a valid mDNS domain prefix."""
    if not isinstance(raw_name, str) or not raw_name.strip():
        return "slabos"
    clean = raw_name.lower().replace(" ", "-").replace("_", "-")
    clean = "".join(c for c in clean if c.isalnum() or c == "-")
    clean = "-".join(filter(None, clean.split("-")))[:63]
    return clean if clean else "slabos"

def generate_auth_pin(length: int = 4) -> str:
    """Compatibility wrapper for the v0.2 authentication subsystem."""
    from slabos.auth.service import generate_auth_pin as _generate_auth_pin
    return _generate_auth_pin(length)

def verify_api_pin(provided_pin: str, expected_pin: str) -> bool:
    """Compatibility wrapper for PIN verification."""
    from slabos.auth.service import verify_api_pin as _verify_api_pin
    return _verify_api_pin(provided_pin, expected_pin)

def create_share_token(filepath: str, secret_key: str, expiry_seconds: int = 86400) -> str:
    """Compatibility wrapper for share-token generation."""
    from slabos.auth.service import create_share_token as _create_share_token
    return _create_share_token(filepath, secret_key, expiry_seconds)

def verify_token_access(token: str, active_tokens: dict) -> bool:
    """Compatibility wrapper for share-token verification."""
    from slabos.auth.service import verify_token_access as _verify_token_access
    return _verify_token_access(token, active_tokens)

def load_or_create_config() -> dict:
    """Compatibility wrapper for the v0.2 configuration subsystem."""
    from slabos.config.manager import ConfigManager
    return ConfigManager().load_or_create()

# =============================================================================
# SECTION 2: HARDWARE & CAPABILITY TELEMETRY
# =============================================================================

def detect_capabilities() -> dict:
    """Compatibility wrapper for the v0.2 hardware subsystem."""
    from slabos.hardware.detector import HardwareDetector
    return HardwareDetector().detect_capabilities()

def get_system_vitals() -> dict:
    """Compatibility wrapper for the v0.2 hardware subsystem."""
    from slabos.hardware.detector import HardwareDetector
    return HardwareDetector().get_system_vitals()

def get_installed_models() -> list:
    """Queries the local Ollama instance for installed models."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')[1:] 
        return [line.split()[0] for line in lines if line]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

def check_vision_capabilities(models: list) -> bool:
    """Checks if installed models support multimodal vision processing."""
    vision_keywords = ["llava", "qwen2-vl", "moondream", "vision"]
    return any(any(kw in model.lower() for kw in vision_keywords) for model in models)

# =============================================================================
# SECTION 3: NETWORKING & ASCII GENERATION
# =============================================================================

def generate_ascii_qr(url: str) -> str:
    """Generates a scannable ASCII text representation of a URL."""
    if not isinstance(url, str) or not url.strip(): return ""
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(url.strip())
        qr.make(fit=True)
        stream = io.StringIO()
        qr.print_ascii(out=stream)
        return stream.getvalue()
    except Exception:
        return ""

def register_mdns_service(hostname: str, port: int = 3000) -> Zeroconf | None:
    """Broadcasts the mDNS hostname across the local network."""
    clean_host = sanitize_mdns_hostname(hostname)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip_bytes = socket.inet_aton(local_ip)
    except Exception:
        ip_bytes = b"\x7f\x00\x00\x01"

    info = ServiceInfo(
        "_http._tcp.local.",
        f"{clean_host} Web Server._http._tcp.local.",
        addresses=[ip_bytes],
        port=port,
        properties={"version": "1.0.0", "system": "slabos"},
        server=f"{clean_host}.local.",
    )
    try:
        zeroconf = Zeroconf()
        zeroconf.register_service(info)
        return zeroconf
    except Exception:
        return None

def setup_media_directory(raw_path: str) -> str:
    """Validates and securely creates the shared media directory."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        raw_path = "./media"
    path_obj = Path(raw_path.strip()).resolve()
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        return str(path_obj)
    except Exception as e:
        print(f"\n[!] FILE SYSTEM ERROR: {e}")
        return ""

# =============================================================================
# SECTION 4: TERMINAL WIZARD
# =============================================================================

def render_banner(title: str = "SlabOS", subtitle: str = "Portable Local AI Node & Media Server") -> None:
    """Renders the styled Cyberpunk ASCII banner."""
    try:
        banner_art = pyfiglet.figlet_format(title.strip(), font="slant")
        styled_content = f"[bold cyan]{banner_art}[/bold cyan][dim white]{subtitle}[/dim white]"
        console.print(Panel(Align.center(styled_content), expand=False, border_style="bright_blue"))
    except Exception:
        print(f"=== {title} ===\n{subtitle}")

def run_interactive_wizard() -> dict:
    """Executes the terminal prompt wizard."""
    render_banner()
    mode_choices = {
        "1. Full Server Mode (AI + Media + Network)": "full",
        "2. Media Server Only": "media",
        "3. AI Node Only": "ai",
        "4. Exit": "exit"
    }
    selected_mode = questionary.select("Select Operation Mode:", choices=list(mode_choices.keys())).ask()
    if not selected_mode or mode_choices.get(selected_mode) == "exit":
        sys.exit(0)

    clean_mode = mode_choices[selected_mode]
    hostname = questionary.text("Enter mDNS Hostname (Press Enter for default: slabos):", default="slabos").ask() or "slabos"
    
    media_dir = "./media"
    if clean_mode in ["full", "media"]:
        media_dir = questionary.path("Where should we store your media? (Press Enter for default: ./media):", default="./media").ask() or "./media"

    return {"mode": clean_mode, "hostname": hostname.strip(), "media_dir": media_dir.strip()}

def setup_ollama_model(model_name: str) -> bool:
    """Automates downloading and verifying AI models."""
    if not shutil.which("ollama"):
        print("\n[!] CRITICAL: Ollama binary not found. Install from https://ollama.com/")
        return False
    print(f"\n[System] Verifying/Downloading model: {model_name}...")
    try:
        subprocess.run(["ollama", "pull", model_name], check=True)
        print(f"[bold green]✔ Node '{model_name}' is primed![/bold green]")
        return True
    except subprocess.CalledProcessError:
        return False

def select_ai_model(recommended_model: str, current_mode: str) -> str:
    """Prompts the user to select an AI model."""
    if not recommended_model:
        print("\n[!] Insufficient disk space for AI. Maintaining 5GB safety buffer.")
        return ""

    installed_models = get_installed_models()
    
    if check_vision_capabilities(installed_models):
        print("[System] Multimodal Vision Capabilities: DETECTED & ACTIVE")
        
    choices = [f"1. Run Installed Recommended ({recommended_model})" if recommended_model in installed_models else f"1. Auto-Install Recommended ({recommended_model})"]
    choices.extend(["2. Select from Installed Models", "3. Enter Custom Model Name", "4. Skip AI Setup"])
    
    choice = questionary.select("How would you like to initialize the AI Node?", choices=choices).ask()
    
    if not choice or choice.startswith("4"):
        return ""
    if choice.startswith("2") and installed_models:
        return questionary.select("Select an installed model:", choices=installed_models).ask()
    if choice.startswith("3"):
        return questionary.text("Enter exact model name:").ask() or recommended_model
        
    return recommended_model

# =============================================================================
# SECTION 5: ENTRY POINT
# =============================================================================

def main() -> None:
    try:
        caps = detect_capabilities()
        vitals = get_system_vitals()
        sys_config = load_or_create_config()
        is_headless = "--headless" in sys.argv
        
        if is_headless:
            config = {
                "mode": sys_config.get("last_mode", "full"),
                "hostname": sys_config.get("last_hostname", "slabos"),
                "media_dir": sys_config.get("default_media_dir", "./media")
            }
            chosen_model = sys_config.get("last_ai_model", "Disabled")
            console.print("[bold green]Initiating Headless Auto-Boot Sequence...[/bold green]")
        else:
            config = run_interactive_wizard()
            sys_config["last_mode"] = config["mode"]
            sys_config["last_hostname"] = config["hostname"]
            sys_config["default_media_dir"] = config.get("media_dir", "./media")
        
        safe_media_path = setup_media_directory(config.get("media_dir", "./media")) if config["mode"] in ["full", "media"] else "Disabled"
        
        pin = sys_config["master_pin"]
        clean_host = sanitize_mdns_hostname(config["hostname"])
        server_url = f"http://{clean_host}.local:3000?pin={pin}"

        if not is_headless:
            recommended = recommend_ai_model(vitals.get("ram_total_gb", 8.0), caps.get("has_gpu", False), vitals.get("disk_free_gb", 50.0))
            if config["mode"] in ["full", "ai"]:
                chosen_model = select_ai_model(recommended, config["mode"])
                if chosen_model and not setup_ollama_model(chosen_model):
                    chosen_model = "Disabled"
            else:
                chosen_model = "Disabled"
            
            sys_config["last_ai_model"] = chosen_model
            with open("slabos_config.json", "w") as f:
                json.dump(sys_config, f, indent=4)
            
        render_banner()
        console.print(f"\n[bold green]✔ SlabOS Agent Active![/bold green]")
        console.print(f"[bold white]Domain:[/bold white] http://{clean_host}.local:3000")
        console.print(f"[bold white]Vault:[/bold white] {safe_media_path}")
        console.print(f"[bold white]Admin PIN:[/bold white] [bold yellow]{pin}[/bold yellow]")
        console.print(f"[bold white]AI Model:[/bold white] {chosen_model}")
        print(generate_ascii_qr(server_url))

        zc = register_mdns_service(clean_host, port=3000)
        
        console.print("\n[bold red]=========================================[/bold red]")
        console.print("[bold red] SERVER ACTIVE - PRESS CTRL+C TO SHUTDOWN [/bold red]")
        console.print("[bold red]=========================================[/bold red]\n")
        
        from server import run_web_server
        run_web_server(host="0.0.0.0", port=3000, pin=pin, media_dir=safe_media_path, active_model=chosen_model)

    except KeyboardInterrupt:
        console.print("\n[bold red]SlabOS shut down gracefully.[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]CRITICAL BOOT FAILURE: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()