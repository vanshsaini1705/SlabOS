# SlabOS v0.2 Component Map

**Project:** SlabOS  
**Version target:** v0.2 Foundation / Reliability Upgrade  
**Purpose:** Exact beginner- and contributor-friendly map of the current v0.1 components, their responsibilities, planned v0.2 destinations, dependencies, call flow, and future extension boundaries.

> This document maps the current implementation to the planned v0.2 architecture. It is a migration guide, not a claim that every future component already exists.

---

# 1. How to Read This Document

Use this file to answer:

- Where is a feature currently implemented?
- Which exact function currently handles it?
- Where should it move in v0.2?
- What should call it after migration?
- What should it depend on?
- What should it not depend on?
- Where should future features such as RAG, MCP, React, or agents be added?

The main rule is:

```text
ONE RESPONSIBILITY
      ↓
ONE CLEAR OWNER
      ↓
SMALL PUBLIC INTERFACE
      ↓
MINIMAL DEPENDENCIES
```

---

# 2. Current Repository Baseline

Current v0.1 structure:

```text
SlabOS/
├── LICENSE
├── README.md
├── project.py
├── requirements.txt
├── server.py
└── templates/
    └── index.html
```

Current main responsibilities:

```text
project.py
    Boot
    Configuration
    Hardware detection
    Telemetry collection
    AI model recommendation/setup
    mDNS
    CLI wizard
    Startup

server.py
    FastAPI
    Authentication checks
    AI chat API
    Vision detection
    Media API
    External-drive detection
    Guest access
    Shutdown

templates/index.html
    Dashboard
    Telemetry UI
    AI chat UI
    Vision UI
    Media vault UI
    Admin UI
```

---

# 3. Global v0.2 Ownership Model

```text
slabos/
│
├── core/              Shared low-level infrastructure
├── config/            Application configuration
├── hardware/          Hardware discovery and telemetry
├── auth/              Authentication and authorization
├── ai/                AI/model/inference integration
├── storage/           Local vault and external-drive detection
├── network/           mDNS/network discovery
├── api/               HTTP/API controllers
└── main.py            Application orchestration
```

Frontend:

```text
templates/
static/
```

Tests:

```text
tests/
```

Documentation:

```text
docs/
```

---

# 4. Current `project.py` Function Map

## 4.1 `recommend_ai_model()`

### Current signature

```python
recommend_ai_model(
    ram_gb: float,
    has_gpu: bool,
    disk_free_gb: float = 50.0
) -> str
```

### Current purpose

Chooses an AI model based on RAM, GPU presence, and available disk space.

### Current inputs

```text
ram_gb
has_gpu
disk_free_gb
SAFETY_BUFFER_GB
```

### Current output

A model name string, or an empty string when disk space is insufficient.

### Current caller

```text
main()
```

### v0.2 destination

```text
slabos/ai/
```

Suggested owner:

```text
ModelRecommendationService
```

### Dependency rule

The recommendation layer should eventually consume a normalized hardware profile rather than probing the operating system itself.

### Future relationship

```text
Hardware Profile
      ↓
Model Recommendation
      ↓
AI Model Manager
```

---

# 5. `calculate_zram_size()`

### Current signature

```python
calculate_zram_size(
    total_ram_gb: float,
    max_ratio: float = 0.5
) -> float
```

### Current purpose

Calculates a compressed ZRAM allocation size.

### Current state

The function exists in the current source but is not part of the main boot flow.

### v0.2 destination

Preferred:

```text
slabos/hardware/
```

or a future dedicated system-optimization module if system optimization becomes an actual feature.

### Migration rule

Do not add ZRAM configuration behavior merely because this function exists. Preserve it as a utility until a real system-optimization feature is designed.

---

# 6. `verify_path_security()`

### Current signature

```python
verify_path_security(
    requested_path: str,
    base_dir: str
) -> bool
```

### Current purpose

Checks whether a requested file path remains inside an allowed base directory.

### v0.2 destination

```text
slabos/core/security.py
slabos/storage/paths.py
```

### Recommended design

Separate generic security helpers from storage-specific path policy:

```text
core/security.py
    generic security helpers

storage/paths.py
    storage-specific path validation
```

### Important

Every file operation should eventually use the centralized path-security layer.

---

# 7. `format_telemetry_payload()`

### Current signature

```python
format_telemetry_payload(
    cpu_pct: float,
    ram_pct: float,
    cpu_temp: float,
    active_model: str
) -> dict
```

### Current purpose

Creates a standardized telemetry dictionary.

### Current outputs

```text
status
cpu_usage_pct
ram_usage_pct
cpu_temp_celsius
thermal_alert
active_model
timestamp
```

### v0.2 destination

```text
slabos/hardware/telemetry.py
```

### Future relationship

```text
Hardware metrics
    ↓
TelemetryManager
    ↓
Normalized telemetry
    ↓
API
    ↓
Frontend
```

---

# 8. `sanitize_mdns_hostname()`

### Current signature

```python
sanitize_mdns_hostname(raw_name: str) -> str
```

### Current purpose

Converts user input into a safe mDNS hostname prefix.

### v0.2 destination

```text
slabos/network/mdns.py
```

### Owner

```text
MDNSService
```

No AI or storage module should need to understand hostname sanitization.

---

# 9. `generate_auth_pin()`

### Current signature

```python
generate_auth_pin(length: int = 4) -> str
```

### Current purpose

Generates a cryptographically secure numeric PIN.

### v0.2 destination

```text
slabos/auth/manager.py
```

### Dependency

```text
secrets
string
```

---

# 10. `verify_api_pin()`

### Current signature

```python
verify_api_pin(
    provided_pin: str,
    expected_pin: str
) -> bool
```

### Current purpose

Compares PINs using constant-time comparison.

### v0.2 destination

```text
slabos/auth/manager.py
```

### Rule

API routes should ask the authentication subsystem for an authorization decision rather than implementing their own credential comparison.

---

# 11. `create_share_token()`

### Current signature

```python
create_share_token(
    filepath: str,
    secret_key: str,
    expiry_seconds: int = 86400
) -> str
```

### Current purpose

Creates a time-based hashed share token.

### Current state

The function exists but is not fully integrated into the current guest-sharing flow.

### v0.2 destination

```text
slabos/auth/sessions.py
```

or, if used only for guest shares:

```text
slabos/auth/guests.py
```

### Future lifecycle

```text
create
validate
expire
revoke
cleanup
```

---

# 12. `verify_token_access()`

### Current signature

```python
verify_token_access(
    token: str,
    active_tokens: dict
) -> bool
```

### Current purpose

Checks token expiry and whether the token is active.

### Current limitation

The current guest route does not provide a complete token/session lifecycle around this helper.

### v0.2 destination

```text
slabos/auth/sessions.py
```

### Future session data

```text
token_id
created_at
expires_at
revoked_at
role
scope
```

---

# 13. `load_or_create_config()`

### Current signature

```python
load_or_create_config() -> dict
```

### Current purpose

Loads `slabos_config.json`, or creates default configuration.

### Current configuration keys

```text
master_pin
default_media_dir
guest_pins
last_mode
last_hostname
last_ai_model
```

### v0.2 destination

```text
slabos/config/manager.py
```

### New responsibilities

```text
load()
save()
validate()
defaults()
migrate()
```

### New schema location

```text
slabos/config/schema.py
```

---

# 14. `detect_capabilities()`

### Current signature

```python
detect_capabilities() -> dict
```

### Current outputs

```text
os
is_root
has_ollama
has_gpu
```

### Current dependencies

```text
platform
ctypes
os
shutil
```

### v0.2 destination

```text
slabos/hardware/detector.py
```

### Future output

A normalized `HardwareProfile` object.

---

# 15. `get_installed_models()`

### Current signature

```python
get_installed_models() -> list
```

### Current purpose

Runs `ollama list` and extracts installed model names.

### v0.2 destination

```text
slabos/ai/ollama.py
```

### Future interface

```text
OllamaAdapter.list_models()
```

---

# 16. `check_vision_capabilities()`

### Current signature

```python
check_vision_capabilities(models: list) -> bool
```

### Current purpose

Detects likely vision-capable models using model-name keywords.

### v0.2 destination

```text
slabos/ai/vision.py
```

### Future improvement

Prefer structured model metadata where the inference backend provides it, rather than relying only on string keywords.

---

# 17. `get_system_vitals()`

### Current signature

```python
get_system_vitals() -> dict
```

### Current outputs

```text
cpu_pct
ram_pct
ram_total_gb
cpu_temp
disk_pct
disk_total_gb
disk_free_gb
```

### Current dependency

```text
psutil
```

### v0.2 destination

```text
slabos/hardware/telemetry.py
```

### Future relationship

```text
HardwareDetector
        ↓
TelemetryManager
        ↓
HardwareSnapshot
```

---

# 18. `generate_ascii_qr()`

### Current signature

```python
generate_ascii_qr(url: str) -> str
```

### Current purpose

Generates a terminal-friendly QR representation.

### v0.2 destination

Could belong to:

```text
slabos/network/
```

or, if QR generation remains guest-specific:

```text
slabos/auth/guests.py
```

The final owner should be chosen when the guest/network services are implemented.

---

# 19. `register_mdns_service()`

### Current signature

```python
register_mdns_service(
    hostname: str,
    port: int = 3000
)
```

### Current purpose

Registers a local HTTP service through Zeroconf/mDNS.

### Current dependencies

```text
socket
zeroconf
```

### v0.2 destination

```text
slabos/network/mdns.py
```

### Future owner

```text
MDNSService
```

---

# 20. `setup_media_directory()`

### Current signature

```python
setup_media_directory(raw_path: str) -> str
```

### Current purpose

Creates and resolves the local media directory.

### v0.2 destination

```text
slabos/storage/vault.py
```

### Future owner

```text
LocalVault
```

---

# 21. `render_banner()`

### Current purpose

Renders the terminal banner using Rich and PyFiglet.

### v0.2 destination

Potential future CLI layer:

```text
slabos/cli/
```

For early v0.2 migration it may remain close to application bootstrap.

---

# 22. `run_interactive_wizard()`

### Current purpose

Collects:

```text
operation mode
hostname
media directory
```

### v0.2 destination

Preferred future location:

```text
slabos/cli/
```

### Rule

The wizard should call service interfaces rather than implementing service logic itself.

---

# 23. `setup_ollama_model()`

### Current signature

```python
setup_ollama_model(model_name: str) -> bool
```

### Current purpose

Checks for Ollama and pulls a model.

### v0.2 destination

```text
slabos/ai/ollama.py
```

### Future interface

```text
OllamaAdapter.pull_model(model_name)
```

---

# 24. `select_ai_model()`

### Current signature

```python
select_ai_model(
    recommended_model: str,
    current_mode: str
) -> str
```

### Current purpose

Provides interactive model-selection options.

### v0.2 destination

```text
slabos/ai/manager.py
```

### Future separation

Model-selection UI and model-selection policy should be separated.

```text
CLI/UI
   ↓
AIManager
   ↓
ModelRecommendationService
```

---

# 25. `main()`

### Current purpose

Central application orchestration.

### Current responsibilities

```text
detect capabilities
get system vitals
load config
check headless mode
run wizard
setup storage
load authentication
recommend AI model
install AI model
save config
register mDNS
start FastAPI
```

### v0.2 destination

```text
slabos/main.py
```

### Important architectural change

`main()` should become an orchestrator rather than a container for implementation logic.

Preferred concept:

```text
main()
  ↓
initialize_config()
  ↓
initialize_hardware()
  ↓
initialize_auth()
  ↓
initialize_storage()
  ↓
initialize_ai()
  ↓
initialize_network()
  ↓
start_api()
```

---

# 26. Current `server.py` Class Map

## `ChatPayload`

### Current fields

```text
prompt
model
images
```

### Current purpose

Validates AI chat request payloads.

### v0.2 destination

```text
slabos/api/ai.py
```

### Important v0.2 change

The client should not be trusted as the authority for which model the server executes. The API should resolve the active/authorized model through `AIManager`.

---

# 27. `check_access()`

### Current signature

```python
check_access(provided_pin: str) -> tuple[bool, bool]
```

### Current outputs

```text
is_authorized
is_admin
```

### v0.2 destination

```text
slabos/auth/manager.py
```

### Future output

A structured authentication result, for example:

```text
AuthenticatedIdentity
├── authenticated
├── user_id / guest_id
├── role
└── permissions
```

---

# 28. `get_usb_drives()`

### Current signature

```python
get_usb_drives() -> dict
```

### Current purpose

Detects partitions that appear to be externally mounted.

### v0.2 decision

**Option A is locked.**

SlabOS v0.2 will detect already-mounted external drives and will not perform OS-level automatic mounting.

### v0.2 destination

```text
slabos/storage/external.py
```

### Future owner

```text
ExternalDriveDetector
```

---

# 29. `resolve_vault_path()`

### Current signature

```python
resolve_vault_path(subpath: str) -> tuple[str, str]
```

### Current purpose

Maps a logical vault path to the configured local media directory or a detected external-drive path.

### v0.2 destination

Split responsibilities:

```text
slabos/storage/paths.py
slabos/storage/manager.py
```

### Target flow

```text
Logical path
   ↓
StorageManager
   ↓
Storage provider selection
   ↓
PathSecurity
   ↓
Resolved filesystem path
```

---

# 30. `serve_dashboard()`

### Current route

```text
GET /
```

### Current purpose

Renders `index.html` and passes runtime state such as:

```text
active_model
enable_ai
enable_media
is_admin
```

### v0.2 destination

```text
slabos/api/
```

### Rule

This remains a controller. It should not own authentication or service implementation.

---

# 31. `api_get_vitals()`

### Current route

```text
GET /api/vitals
```

### Current purpose

Checks authorization, collects system vitals, and returns a compact JSON payload.

### v0.2 destination

```text
slabos/api/health.py
```

or:

```text
slabos/api/system.py
```

### Preferred flow

```text
API
 ↓
AuthManager
 ↓
TelemetryManager
 ↓
Response formatter
```

---

# 32. `check_vision_support()`

### Current route

```text
GET /api/ai/check-vision
```

### Current purpose

Checks whether the active model name matches known vision keywords.

### v0.2 destination

```text
slabos/api/ai.py
```

with capability logic delegated to:

```text
slabos/ai/vision.py
```

---

# 33. `stream_ollama_generator()`

### Current signature

```python
stream_ollama_generator(
    prompt: str,
    model_name: str,
    images: List[str] = []
)
```

### Current purpose

Connects to the local Ollama generate endpoint and streams response data.

### v0.2 destination

```text
slabos/ai/ollama.py
```

### Future interface

```text
OllamaAdapter.stream()
```

The API should never need to know the Ollama HTTP implementation.

---

# 34. `api_chat_stream()`

### Current route

```text
POST /api/chat
```

### Current flow

```text
Request
 ↓
check_access()
 ↓
stream_ollama_generator()
 ↓
StreamingResponse
```

### v0.2 flow

```text
Request
 ↓
AuthManager
 ↓
AIManager
 ↓
OllamaAdapter
 ↓
StreamingResponse
```

### Destination

```text
slabos/api/ai.py
```

---

# 35. `execute_delayed_shutdown()`

### Current purpose

Delays and sends SIGINT to terminate the process.

### v0.2 destination

```text
slabos/api/system.py
```

or a dedicated system-control service.

### Security

Remote shutdown must remain admin-only.

---

# 36. `shutdown_server()`

### Current route

```text
POST /api/system/shutdown
```

### Current purpose

Validates the admin credential and initiates shutdown.

### v0.2 destination

```text
slabos/api/system.py
```

### Dependencies

```text
AuthManager
SystemControlService
```

---

# 37. `create_guest_pin()`

### Current route

```text
POST /api/system/guest
```

### Current purpose

Creates a guest PIN, stores it, builds a guest URL, and returns an SVG QR code.

### v0.2 target

Split into:

```text
API controller
    ↓
GuestManager
    ↓
Guest credential
    ↓
Expiry
    ↓
QR generation
```

### Destination

```text
slabos/api/auth.py
slabos/auth/guests.py
```

---

# 38. `list_media_files()`

### Current route

```text
GET /api/media/list
```

### Current purpose

Lists folders/files in a local vault or detected external drive.

### Current flow

```text
API
 ↓
check_access()
 ↓
resolve_vault_path()
 ↓
os.listdir()
```

### v0.2 flow

```text
API
 ↓
AuthManager
 ↓
StorageManager.list()
 ↓
Storage provider
```

### Destination

```text
slabos/api/media.py
```

---

# 39. `download_media()`

### Current route

```text
GET /api/media/download/{filepath:path}
```

### Current purpose

Resolves a file path and returns a `FileResponse`.

### v0.2 destination

```text
slabos/api/media.py
```

### Service used

```text
StorageManager.download()
```

---

# 40. `upload_media()`

### Current route

```text
POST /api/media/upload
```

### Current purpose

Receives an uploaded file and writes it to the selected directory.

### v0.2 protections

```text
filename validation
upload-size limits
path validation
collision handling
safe temporary writes
atomic finalization
```

### v0.2 flow

```text
API
 ↓
AuthManager
 ↓
StorageManager.upload()
 ↓
PathSecurity
 ↓
temporary write
 ↓
final storage
```

---

# 41. `create_folder()`

### Current route

```text
POST /api/media/mkdir
```

### v0.2 destination

```text
slabos/api/media.py
```

### Service

```text
StorageManager.create_folder()
```

---

# 42. `delete_item()`

### Current route

```text
POST /api/media/delete
```

### Current behavior

Deletes a file or directory.

### v0.2 destination

```text
slabos/api/media.py
```

### Service

```text
StorageManager.delete()
```

### Required security boundary

```text
PathSecurity
+
Authorization
```

---

# 43. `rename_item()`

### Current route

```text
POST /api/media/rename
```

### v0.2 destination

```text
slabos/api/media.py
```

### Service

```text
StorageManager.rename()
```

---

# 44. `run_web_server()`

### Current signature

```python
run_web_server(
    host: str,
    port: int,
    pin: str,
    media_dir: str,
    active_model: str
)
```

### Current purpose

Stores runtime state in `app.state` and starts Uvicorn.

### Current state

```text
session_pin
media_dir
active_model
enable_ai
enable_media
```

### v0.2 direction

Application services should be initialized before the API server starts.

A future `ApplicationContext` should contain:

```text
config
auth
hardware
ai
storage
network
```

---

# 45. Current API Map

Current API routes:

```text
GET  /
GET  /api/vitals
GET  /api/ai/check-vision
POST /api/chat
POST /api/system/shutdown
POST /api/system/guest
GET  /api/media/list
GET  /api/media/download/{filepath:path}
POST /api/media/upload
POST /api/media/mkdir
POST /api/media/delete
POST /api/media/rename
```

## v0.2 intended grouping

```text
/api/v1/health

/api/v1/system/*
/api/v1/auth/*
/api/v1/ai/*
/api/v1/storage/*
```

---

# 46. Current `index.html` JavaScript Map

## `fetchVitals()`

Current purpose:

- Calls `/api/vitals`
- Updates CPU
- Updates RAM
- Updates temperature
- Updates free disk

v0.2 source:

```text
static/js/telemetry.js
```

---

## `checkVisionCapability()`

Current purpose:

- Calls `/api/ai/check-vision`
- Enables/disables image input
- Updates capability indicator

v0.2 source:

```text
static/js/chat.js
```

---

## `triggerImageSelect()`

Current purpose:

Opens the image selector if the active model supports vision.

v0.2 source:

```text
static/js/chat.js
```

---

## `handleImageAttach()`

Current purpose:

Reads the selected image as Base64 for the chat request.

v0.2 source:

```text
static/js/chat.js
```

---

## `clearAttachedImage()`

Current purpose:

Clears the current image attachment.

v0.2 source:

```text
static/js/chat.js
```

---

## `handleEnter()`

Current purpose:

Submits chat when Enter is pressed.

v0.2 source:

```text
static/js/chat.js
```

---

## `sendChat()`

Current purpose:

- Collects prompt
- Adds user message
- Builds request payload
- Calls `/api/chat`
- Reads streaming response
- Updates AI message

v0.2 source:

```text
static/js/chat.js
```

---

## `fetchMediaList()`

Current purpose:

- Lists media
- Navigates folders
- Shows files/folders
- Provides actions

v0.2 source:

```text
static/js/media.js
```

---

## `uploadFile()`

Current purpose:

Uploads a selected file with `FormData`.

v0.2 source:

```text
static/js/media.js
```

---

## `createFolderPrompt()`

Current purpose:

Prompts for a folder name and calls the folder-creation API.

v0.2 source:

```text
static/js/media.js
```

---

## `deleteItem()`

Current purpose:

Confirms and deletes a file/folder.

v0.2 source:

```text
static/js/media.js
```

---

## `renameItem()`

Current purpose:

Prompts for a new name and calls the rename API.

v0.2 source:

```text
static/js/media.js
```

---

## `shutdownServer()`

Current purpose:

Calls the admin shutdown endpoint.

v0.2 source:

```text
static/js/admin.js
```

---

## `generateGuest()`

Current purpose:

Calls the guest endpoint and renders the returned QR.

v0.2 source:

```text
static/js/admin.js
```

---

# 47. Current Frontend State Variables

Current JavaScript state includes:

```text
pin
attachedBase64Image
isVisionSupported
currentVaultPath
```

v0.2 rule:

Do not create global state for unrelated modules.

Target:

```text
chat state
telemetry state
media state
admin state
```

Each module should own its own state.

---

# 48. v0.2 Main Classes and Responsibilities

## `ApplicationContext`

Holds initialized services:

```text
config
auth
hardware
ai
storage
network
```

---

## `ConfigManager`

```text
load()
save()
validate()
migrate()
get()
```

---

## `HardwareManager`

```text
get_profile()
get_telemetry()
```

---

## `HardwareProfile`

Normalized representation of the host system.

Potential fields:

```text
os
architecture
cpu
ram_total_gb
gpu
gpu_available
ollama_available
disk_total_gb
disk_free_gb
```

Exact final fields should follow the capabilities supported by each operating system.

---

## `AuthManager`

```text
authenticate()
create_guest()
validate_session()
revoke_session()
check_permission()
```

---

## `GuestManager`

```text
create_guest()
get_guest()
revoke_guest()
cleanup_expired()
```

---

## `AIManager`

```text
generate()
stream()
get_active_model()
get_available_models()
supports_vision()
```

---

## `OllamaAdapter`

```text
list_models()
pull_model()
generate()
stream()
```

---

## `VisionManager`

```text
supports_vision()
validate_image()
```

The exact methods may expand later.

---

## `StorageManager`

```text
list()
upload()
download()
create_folder()
delete()
rename()
get_storage_info()
```

---

## `LocalVault`

Responsible for operations against the configured local storage root.

---

## `ExternalDriveDetector`

Responsible only for discovering already-mounted external drives.

It must not become responsible for:

- User permissions
- AI
- Filesystem policy
- UI

---

## `PathSecurity`

```text
normalize()
resolve()
is_allowed()
validate_filename()
```

Exact method names can be finalized during implementation.

---

## `MDNSService`

```text
sanitize_hostname()
register()
unregister()
```

---

# 49. Exact v0.2 File Ownership

```text
slabos/core/logger.py
    Logging only

slabos/core/errors.py
    Typed application errors

slabos/core/security.py
    Generic security helpers

slabos/core/response.py
    Standard API responses

slabos/config/schema.py
    Configuration structure

slabos/config/manager.py
    Configuration lifecycle

slabos/hardware/detector.py
    Hardware discovery

slabos/hardware/profiles.py
    Hardware profile representation

slabos/hardware/telemetry.py
    Live metrics

slabos/auth/manager.py
    Authentication and authorization

slabos/auth/sessions.py
    Session/token lifecycle

slabos/auth/guests.py
    Guest lifecycle

slabos/ai/models.py
    Model data

slabos/ai/ollama.py
    Ollama integration

slabos/ai/vision.py
    Vision capability logic

slabos/ai/manager.py
    AI orchestration

slabos/storage/paths.py
    Path security for storage

slabos/storage/vault.py
    Local vault

slabos/storage/external.py
    External-drive detection

slabos/storage/manager.py
    Storage orchestration

slabos/network/mdns.py
    mDNS

slabos/api/health.py
    Health/status/telemetry routes

slabos/api/auth.py
    Authentication routes

slabos/api/system.py
    System routes

slabos/api/ai.py
    AI routes

slabos/api/media.py
    Storage/media routes

slabos/main.py
    Application startup/orchestration
```

---

# 50. Module Communication Rules

## Allowed service flow

```text
API
 ↓
Manager
 ↓
Adapter / Provider
 ↓
OS / External service
```

## AI

```text
api/ai.py
    ↓
AIManager
    ↓
OllamaAdapter
    ↓
Ollama
```

## Storage

```text
api/media.py
    ↓
StorageManager
    ↓
LocalVault / ExternalDrive
    ↓
Filesystem
```

## Authentication

```text
API
    ↓
AuthManager
    ↓
Session / Guest manager
```

## Telemetry

```text
API
    ↓
HardwareManager
    ↓
TelemetryManager
    ↓
Operating System
```

---

# 51. Forbidden Coupling

Avoid these relationships:

```text
Frontend
   X→ Filesystem

Frontend
   X→ Ollama directly

Storage
   X→ AIManager

AI
   X→ HTML

Auth
   X→ DOM

Hardware
   X→ Frontend state

API controller
   X→ direct raw filesystem operations

API controller
   X→ direct Ollama HTTP calls
```

---

# 52. Current → Future Call Flow

## Boot

```text
project.main()
      ↓
ConfigManager
      ↓
HardwareManager
      ↓
AuthManager
      ↓
StorageManager
      ↓
AIManager
      ↓
MDNSService
      ↓
API server
```

During migration, `project.main()` can remain a compatibility entry point while actual implementations move into services.

---

## AI chat

```text
/api/v1/ai/chat
      ↓
AuthManager
      ↓
AIManager
      ↓
OllamaAdapter
      ↓
Ollama
```

---

## Vision

```text
/api/v1/ai/capabilities
      ↓
AuthManager
      ↓
AIManager
      ↓
VisionManager
```

---

## File list

```text
/api/v1/storage/list
      ↓
AuthManager
      ↓
StorageManager
      ↓
PathSecurity
      ↓
LocalVault / ExternalDrive
```

---

## File upload

```text
/api/v1/storage/upload
      ↓
AuthManager
      ↓
StorageManager
      ↓
PathSecurity
      ↓
temporary write
      ↓
final storage
```

---

## Guest creation

```text
/api/v1/auth/guest
      ↓
AuthManager
      ↓
GuestManager
      ↓
expiry/token
      ↓
QR generation
      ↓
response
```

---

# 53. Application State Migration

Current state:

```text
app.state.session_pin
app.state.media_dir
app.state.active_model
app.state.enable_ai
app.state.enable_media
```

Target:

```text
ApplicationContext
├── config
├── auth
├── hardware
├── ai
├── storage
└── network
```

Migration should happen gradually.

Do not remove old state variables until all consumers have moved.

---

# 54. Configuration Variable Migration

Current:

```text
master_pin
default_media_dir
guest_pins
last_mode
last_hostname
last_ai_model
```

Target conceptual grouping:

```text
auth
    admin credential configuration
    guest configuration

storage
    media root
    storage settings

network
    hostname
    port

ai
    active model
    model settings

system
    mode
```

The exact persisted schema will be finalized in `config/schema.py`.

---

# 55. API Request/Response Contract Rule

API routes should be thin.

Preferred route pattern:

```text
Route handler
    ↓
Validate request
    ↓
Authenticate
    ↓
Call service
    ↓
Convert result to API response
```

Do not place core business logic directly inside FastAPI route functions.

---

# 56. Testing Ownership

```text
tests/test_config.py
    ConfigManager

tests/test_security.py
    Security + path handling

tests/test_auth.py
    AuthManager + GuestManager

tests/test_hardware.py
    HardwareDetector + profiles

tests/test_storage.py
    StorageManager + LocalVault + path rules

tests/test_ai.py
    AIManager + model logic

tests/test_api.py
    API contracts and integration paths
```

When a contributor changes one subsystem, the subsystem tests should be the first validation point.

---

# 57. Future Feature Placement

## React

```text
frontend/
```

Connects to:

```text
API
```

React must not import Python modules directly.

---

## RAG

```text
slabos/rag/
├── loader.py
├── chunker.py
├── embeddings.py
├── retriever.py
└── vector_store.py
```

Relationship:

```text
Storage
   ↓
RAG
   ↓
AIManager
```

---

## Vector database

```text
slabos/rag/vector_store.py
```

Do not place vector-database implementation directly inside `StorageManager`.

---

## MCP

```text
slabos/integrations/mcp/
```

Relationship:

```text
AI / Agents
      ↓
Tool layer
      ↓
MCP
```

---

## Agents

```text
slabos/agents/
```

Agents should call controlled tools and must respect authentication, authorization, and storage boundaries.

---

## Docker

```text
deployment/docker/
```

Docker configuration belongs to deployment infrastructure rather than core service modules.

---

## Multi-user

Primary ownership:

```text
slabos/auth/
```

Integration points:

```text
authentication
storage permissions
API
```

---

# 58. Contributor Decision Tree

When adding a feature, ask:

```text
Does it handle files?
    ↓ yes
storage/

Does it handle AI/models?
    ↓ yes
ai/

Does it authenticate users?
    ↓ yes
auth/

Does it inspect hardware?
    ↓ yes
hardware/

Does it expose HTTP?
    ↓ yes
api/

Does it affect mDNS/network discovery?
    ↓ yes
network/

Is it shared infrastructure?
    ↓ yes
core/

Is it configuration?
    ↓ yes
config/
```

If a feature spans multiple categories, keep the actual implementation in the smallest specialized subsystem and let managers coordinate the interaction.

---

# 59. Safe Change Examples

## Change Ollama endpoint

Modify:

```text
slabos/ai/ollama.py
```

Do not modify unrelated:

```text
storage/
auth/
hardware/
frontend/
```

unless the public API contract changes.

---

## Change local file implementation

Modify:

```text
slabos/storage/vault.py
```

The API should continue calling:

```text
StorageManager
```

---

## Change guest expiry policy

Modify:

```text
slabos/auth/guests.py
```

Do not put guest-expiry logic into every API route.

---

## Change telemetry collection

Modify:

```text
slabos/hardware/telemetry.py
```

The frontend should continue consuming the telemetry contract.

---

## Add a new API route

Modify the appropriate:

```text
slabos/api/*.py
```

and, if necessary, the related service module.

Do not place new business logic directly into `server.py`.

---

# 60. v0.2 Migration Rule

For each old function:

```text
OLD FUNCTION
     ↓
NEW OWNER
     ↓
NEW IMPLEMENTATION
     ↓
COMPATIBILITY WRAPPER
     ↓
TEST
```

Only after the new implementation is stable:

```text
compatibility wrapper
     ↓
mark deprecated
     ↓
later removal
```

This is intentionally slower than a complete rewrite because it reduces regression risk.

---

# 61. v0.2 Migration Order

Use this order:

```text
1. Documentation
2. Core
3. Configuration
4. Hardware
5. Authentication
6. Storage
7. AI
8. API
9. Frontend
10. Tests
11. Compatibility cleanup
```

Do not skip directly to RAG, MCP, or agents while the foundational boundaries are unfinished.

---

# 62. What a Contributor Should Not Need to Know

A contributor changing:

```text
slabos/storage/vault.py
```

should not need to understand:

```text
Ollama
mDNS
AI prompting
frontend HTML
```

A contributor changing:

```text
slabos/ai/ollama.py
```

should not need to understand:

```text
filesystem internals
guest PIN lifecycle
dashboard CSS
```

This is a primary design success criterion for SlabOS v0.2.

---

# 63. Final Ownership Summary

```text
BOOT
    main.py

CONFIG
    config/

HARDWARE
    hardware/

AUTH
    auth/

AI
    ai/

STORAGE
    storage/

NETWORK
    network/

API
    api/

FRONTEND
    templates/
    static/

ERRORS
    core/errors.py

LOGGING
    core/logger.py

SECURITY
    core/security.py
    storage/paths.py

TESTS
    tests/

DOCUMENTATION
    docs/
```

---

# 64. Canonical Rule

When in doubt about where new code belongs:

1. Put it in the subsystem that owns the responsibility.
2. Expose a small interface.
3. Keep implementation details behind that interface.
4. Do not make unrelated modules depend on implementation details.
5. Add a focused test.
6. Update `docs/ARCHITECTURE.md` and this component map when the architecture changes.

This document must remain synchronized with the real codebase as SlabOS evolves.
