import ctypes
import os
import platform
import shutil

import psutil


class HardwareDetector:
    """Detect host capabilities and collect live hardware telemetry."""

    BYTES_IN_GB = 1024 ** 3

    def detect_capabilities(self) -> dict:
        """Probe the host OS environment and available hardware."""
        current_os = platform.system().lower()
        is_admin = False

        try:
            if current_os == "windows":
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            elif hasattr(os, "geteuid"):
                is_admin = os.geteuid() == 0
        except Exception:
            pass

        has_gpu = (
            shutil.which("nvidia-smi") is not None
            or (current_os == "darwin" and platform.machine() == "arm64")
        )

        return {
            "os": current_os,
            "is_root": is_admin,
            "has_ollama": shutil.which("ollama") is not None,
            "has_gpu": has_gpu,
        }

    def get_system_vitals(self) -> dict:
        """Fetch live host hardware metrics."""
        cpu_pct = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()

        temp = -1.0
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()

                for key in [
                    "coretemp",
                    "cpu_thermal",
                    "k10temp",
                    "zenpower",
                    "cpu-thermal",
                ]:
                    if key in temps and temps[key]:
                        temp = round(temps[key][0].current, 1)
                        break
            except Exception:
                pass

        disk_pct = disk_total_gb = disk_free_gb = 0.0

        try:
            disk = psutil.disk_usage("/")
            disk_pct = round(disk.percent, 1)
            disk_total_gb = round(disk.total / self.BYTES_IN_GB, 2)
            disk_free_gb = round(disk.free / self.BYTES_IN_GB, 2)
        except Exception:
            pass

        return {
            "cpu_pct": round(cpu_pct, 1),
            "ram_pct": round(ram.percent, 1),
            "ram_total_gb": round(ram.total / self.BYTES_IN_GB, 2),
            "cpu_temp": temp,
            "disk_pct": disk_pct,
            "disk_total_gb": disk_total_gb,
            "disk_free_gb": disk_free_gb,
        }
