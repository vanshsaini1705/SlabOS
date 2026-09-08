from unittest.mock import Mock, patch

from slabos.hardware.detector import HardwareDetector


def test_detect_capabilities_reports_host_environment():
    detector = HardwareDetector()

    with patch("slabos.hardware.detector.platform.system", return_value="Linux"), \
         patch("slabos.hardware.detector.shutil.which") as which_mock:

        which_mock.side_effect = lambda name: (
            "/usr/bin/ollama" if name == "ollama"
            else "/usr/bin/nvidia-smi" if name == "nvidia-smi"
            else None
        )

        with patch("slabos.hardware.detector.os.geteuid", return_value=1000):
            capabilities = detector.detect_capabilities()

    assert capabilities == {
        "os": "linux",
        "is_root": False,
        "has_ollama": True,
        "has_gpu": True,
    }


def test_detect_capabilities_handles_privilege_detection_failure():
    detector = HardwareDetector()

    with patch("slabos.hardware.detector.platform.system", return_value="Linux"), \
         patch("slabos.hardware.detector.shutil.which", return_value=None), \
         patch(
             "slabos.hardware.detector.os.geteuid",
             side_effect=OSError("permission check failed"),
         ):

        capabilities = detector.detect_capabilities()

    assert capabilities["os"] == "linux"
    assert capabilities["is_root"] is False
    assert capabilities["has_ollama"] is False
    assert capabilities["has_gpu"] is False


def test_get_system_vitals_returns_expected_metrics():
    detector = HardwareDetector()

    memory = Mock()
    memory.percent = 42.5
    memory.total = 8 * (1024 ** 3)

    disk = Mock()
    disk.percent = 35.7
    disk.total = 100 * (1024 ** 3)
    disk.free = 64 * (1024 ** 3)

    with patch(
        "slabos.hardware.detector.psutil.cpu_percent",
        return_value=17.26,
    ), patch(
        "slabos.hardware.detector.psutil.virtual_memory",
        return_value=memory,
    ), patch(
        "slabos.hardware.detector.psutil.disk_usage",
        return_value=disk,
    ), patch(
        "slabos.hardware.detector.psutil.sensors_temperatures",
        return_value={},
    ):
        vitals = detector.get_system_vitals()

    assert vitals == {
        "cpu_pct": 17.3,
        "ram_pct": 42.5,
        "ram_total_gb": 8.0,
        "cpu_temp": -1.0,
        "disk_pct": 35.7,
        "disk_total_gb": 100.0,
        "disk_free_gb": 64.0,
    }