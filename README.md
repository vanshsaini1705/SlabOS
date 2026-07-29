
# 🖥️ SlabOS: The Portable Local AI Node & Media Server

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.140.9-009688?logo=fastapi&logoColor=white)
![Ollama](https://img.shields.io/badge/AI-Ollama-white?logo=ollama&logoColor=black)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)

**SlabOS** is a lightweight, headless server engine designed to transform repurposed hardware—like old laptops with broken screens ("slabtops") or aging desktops—into self-healing, locally hosted AI nodes and secure network storage servers. 

---

## 🌍 The Vision: Why We Built SlabOS

Every year, millions of highly capable computers are discarded as e-waste simply because their battery degraded or their screen cracked. However, the CPU, RAM, and motherboard inside are still incredibly powerful. 

SlabOS was engineered to rescue this hardware. By stripping away heavy, bloated desktop environments and running a highly optimized FastAPI engine in the background, we can turn "trash" into a private, offline AI assistant and media vault. 
* **Total Privacy:** Your data and AI prompts never leave your local Wi-Fi network. Zero cloud subscriptions. Zero data harvesting.
* **Sustainability:** Upcycling e-waste into a dedicated home server reduces environmental impact.
* **Democratized AI:** Low-barrier entry to running powerful open-source models like Llama 3, DeepSeek, and LLaVA entirely offline.

---

## ✨ Core Features

* **🧠 Multimodal AI Integration:** Chat with local LLMs and natively upload images to Vision models (like LLaVA) for image analysis. SlabOS automatically detects if your active model supports vision and toggles the UI accordingly.
* **📁 Secure Media Vault:** A fully functional, drag-and-drop file manager. Upload, rename, delete, and create folders directly from your browser.
* **💾 Dynamic USB Auto-Mounting:** Plug in a USB drive or external hard drive, and SlabOS instantly detects it and mounts it securely at the top of your vault.
* **📊 Live Hardware Telemetry:** Real-time polling of your server's CPU, RAM, Disk Space, and Thermal sensors.
* **🔐 Zero-Typing Guest Access:** Generate dynamic, Base64 QR codes from the Admin Center to grant temporary, secure dashboard access to phones on the same Wi-Fi network.
* **📡 mDNS Network Broadcasting:** Forget IP addresses. The server broadcasts itself locally, resolving automatically to `http://slabos.local:3000`.

---

## 🚀 Installation & Setup Guide

### Phase 1: Prerequisites
1. **Python 3.10+**: Ensure Python is installed and added to your system PATH.
2. **Ollama**: You must install [Ollama](https://ollama.com/) on the host machine to serve the AI models.

### Phase 2: Clone the Repository
Open your terminal or command prompt and download the project:
```bash
git clone https://github.com/vanshsaini1705/SlabOS.git

cd SlabOS
```

### Phase 3: The Virtual Environment (Explanation & Setup)

**What is a Virtual Environment (`venv`)?**
A virtual environment is simply an isolated folder that holds the specific Python libraries this project needs. This prevents SlabOS's requirements from conflicting with other Python projects on your computer. In the commands below, the second `venv` is just the *name* of the folder we are creating (you could name it `slabos_env`, but `venv` is the industry standard).

Find your specific Operating System below and run the commands in your terminal:

#### 🪟 For Windows Users

```cmd
# 1. Create the isolated folder named 'venv'
python -m venv venv

# 2. Activate it (Your terminal prompt will change to show (venv))
venv\Scripts\activate

# 3. Install the required libraries
pip install -r requirements.txt
```

#### 🍎 For macOS Users

```bash
# 1. Create the isolated folder named 'venv'
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install the required libraries
pip install -r requirements.txt
```

#### 🐧 For Linux Users (Debian / Ubuntu / Mint / Arch / Fedora)

*Note for Debian/Ubuntu users: You may need to install the virtual environment package first by running `sudo apt update && sudo apt install python3-venv`.*

```bash
# 1. Create the isolated folder named 'venv'
python3 -m venv venv

# 2. Activate it
source venv/bin/activate

# 3. Install the required libraries
pip install -r requirements.txt
```

---

## 💻 Running SlabOS

With your virtual environment activated, start the server interactively:

```bash
python project.py
```

A terminal wizard will appear. It will ask you to:

1. Choose your operating mode (AI + Media, Media Only, etc.).
2. Set your custom `mDNS` hostname (default: `slabos`).
3. Select an AI model. If you don't have one installed, SlabOS will automatically analyze your hardware and download the optimal model for your system.

---

## 🔄 Autorun: Booting Silently on Startup

**Why do this?**
To make SlabOS behave like a true "headless appliance" (like a router or a NAS), you want it to boot automatically when the computer turns on, without you having to open a terminal and type commands. We achieve this using the `--headless` flag, which skips the terminal wizard and uses your last saved configuration.

Find your specific Operating System below to set up background automation.

### 🪟 Windows Setup (Batch File Method)

1. Press `Win + R`, type `shell:startup`, and press Enter. This opens the Windows Startup folder.
2. Right-click inside the folder, select **New**, then **Text Document**. Name it `slabos_start.bat` (ensure the `.txt` extension is removed).
3. Right-click `slabos_start.bat`, click **Edit**, and paste the following (change the path to wherever you downloaded SlabOS):
```bat
@echo off
cd C:\Path\To\Your\SlabOS
call venv\Scripts\activate
start /B python project.py --headless
```


4. Save and close. SlabOS will now boot silently when you log into Windows.

* **How to Revert/Stop:** Simply delete the `slabos_start.bat` file from the Startup folder.

### 🍎 macOS Setup (launchd Method)

1. Open your terminal and create a startup script file:
```bash
nano ~/Library/LaunchAgents/com.slabos.startup.plist
```


2. Paste the following XML (update the `/path/to/SlabOS` strings to your actual paths):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "[http://www.apple.com/DTDs/PropertyList-1.0.dtd](http://www.apple.com/DTDs/PropertyList-1.0.dtd)">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.slabos.startup</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/SlabOS/venv/bin/python</string>
        <string>/path/to/SlabOS/project.py</string>
        <string>--headless</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/SlabOS</string>
</dict>
</plist>
```


3. Save (`Ctrl+O`, `Enter`) and exit (`Ctrl+X`).
4. Load the script into macOS:
```bash
launchctl load ~/Library/LaunchAgents/com.slabos.startup.plist
```



* **How to Revert/Stop:** Run `launchctl unload ~/Library/LaunchAgents/com.slabos.startup.plist` and delete the file.

### 🐧 Linux Setup (systemd Service Method)

1. Open your terminal and create a background service file:
```bash
sudo nano /etc/systemd/system/slabos.service
```


2. Paste this configuration. **CRITICAL:** Replace `YOUR_USERNAME` and `/path/to/SlabOS` with your actual Linux username and path.
```ini
[Unit]
Description=SlabOS Headless Node
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/path/to/SlabOS
ExecStart=/path/to/SlabOS/venv/bin/python /path/to/SlabOS/project.py --headless
Restart=always

[Install]
WantedBy=multi-user.target
```


3. Save (`Ctrl+O`, `Enter`) and exit (`Ctrl+X`).
4. Enable the service to run on boot:
```bash
sudo systemctl daemon-reload
sudo systemctl enable slabos.service
sudo systemctl start slabos.service
```



* **How to Revert/Stop:** Run `sudo systemctl disable slabos.service` and `sudo systemctl stop slabos.service`.

---

## 🛠️ Pro User Customization Guide

SlabOS is designed to be highly modular. If you are comfortable reading Python and HTML, you can safely modify the following specific files and paths to deeply customize your node:

### 1. The Dashboard (`templates/index.html`)

* **Theme Colors:** SlabOS uses a dark glassmorphism aesthetic. Open `index.html` and look at lines 10-15. You can change the `--neon-cyan` (`#00f3ff`) and `--neon-pink` (`#ff00ea`) hex codes to customize the entire UI's color scheme instantly.
* **Polling Rate:** On line 286, `setInterval(fetchVitals, 2000);` dictates how often the UI asks the server for CPU/RAM stats (2000ms = 2 seconds). Lower it to `500` for ultra-fast telemetry, or raise it to `5000` to save battery on the host.

### 2. The Core Engine (`project.py`)

* **AI Hardware Limits:** Locate `def recommend_ai_model()` (around line 43). SlabOS uses strict logic to decide which model to install based on your RAM. You can change `"qwen2.5:1.5b"` to your personal favorite small model (like `"phi3:mini"`), or lower the `SAFETY_BUFFER_GB` from `5.0` to `2.0` if you want to push a small hard drive to its absolute limit.
* **Broadcasting Port:** If port `3000` is taken by another app on your network, scroll to the absolute bottom of `project.py` (inside `def main()`) and change `port=3000` to `port=8080` in both the `register_mdns_service` and `run_web_server` function calls.

### 3. The API Routing (`server.py`)

* **Vision Model Triggers:** Locate `def check_vision_support()` (around line 125). If a brand-new multimodal Ollama model is released tomorrow (e.g., `super-vision-1`), you can simply add `"super-vision-1"` to the `vision_keywords` list on line 133 to instantly enable front-end image uploading for it.

---

## 📜 License & Author

**Author:** Vansh Saini

**License:** Released under the [GNU AGPLv3 License](LICENSE).

