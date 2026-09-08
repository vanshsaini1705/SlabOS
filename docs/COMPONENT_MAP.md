# SlabOS Component Map

> **v0.2 Foundation / Reliability Upgrade**
>
> A practical guide to where SlabOS responsibilities live today, where they are moving in v0.2, and where contributors should make changes.

---

## Start Here

The most important question this document answers is:

> **“I need to change something. Where should I look?”**

SlabOS is currently a compact prototype. Much of the implementation still lives in `project.py` and `server.py`.

v0.2 is gradually moving those responsibilities behind clearer subsystem boundaries.

```text
ONE RESPONSIBILITY
        ↓
ONE OWNER
        ↓
SMALL INTERFACE
        ↓
MINIMAL COUPLING
        ↓
FOCUSED TEST
```

### Current vs target

```text
TODAY
project.py + server.py
        ↓
many responsibilities mixed together

v0.2
clear subsystem owners
        ↓
services / adapters / controllers
        ↓
easier to change safely
```

> **Important:** paths under `slabos/` are v0.2 targets unless the repository already contains them.

The repository remains the source of truth.

---

## 1. Current Repository

The known v0.1 baseline is:

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

### Current responsibility split

```text
project.py
├── startup / boot
├── configuration
├── hardware detection
├── telemetry
├── AI model recommendation/setup
├── mDNS
├── CLI wizard
└── application orchestration

server.py
├── FastAPI
├── authentication checks
├── AI chat
├── vision checks
├── media operations
├── mounted-drive discovery
├── guest access
└── system shutdown

templates/index.html
├── HTML
├── CSS
└── JavaScript
```

This is the starting point for the v0.2 migration.

---

## 2. v0.2 Ownership Map

The target ownership model is:

```text
slabos/
├── core/        shared infrastructure
├── config/      persistent configuration
├── hardware/    hardware discovery + telemetry
├── auth/        authentication + authorization
├── ai/          models + Ollama integration
├── storage/     media + path/security + external drives
├── network/     mDNS/network helpers
├── api/         thin HTTP controllers
├── system/      system lifecycle actions
└── main.py      application orchestration
```

Frontend:

```text
frontend/
├── templates/
└── static/
    ├── css/
    └── js/
```

Tests:

```text
tests/
├── unit/
├── integration/
└── api/
```

---

## 3. The Ownership Rule

When deciding where code belongs, ask:

```text
What responsibility does this code own?
```

Then place it close to that owner.

| Responsibility | Owner |
|---|---|
| Configuration | `config/` |
| Authentication / authorization | `auth/` |
| Files and media | `storage/` |
| AI / models / Ollama | `ai/` |
| Hardware information | `hardware/` |
| mDNS / network discovery | `network/` |
| HTTP routing | `api/` |
| System lifecycle | `system/` |
| Shared low-level behavior | `core/` |
| Browser presentation | `frontend/` |

A route may coordinate several owners, but it should not become the owner of all of them.

> **Routes coordinate. Services own behavior.**

---

# 4. Configuration

## Current

```text
project.py
```

### `load_or_create_config()`

```python
load_or_create_config() -> dict
```

**Does today**

Loads `slabos_config.json`, or creates default configuration.

**Known keys**

```text
master_pin
default_media_dir
guest_pins
last_mode
last_hostname
last_ai_model
```

**v0.2 destination**

```text
slabos/config/manager.py
```

**Likely responsibilities**

```text
load()
save()
validate()
defaults()
migrate()
```

**Why it moves**

Configuration should have one owner instead of being mixed into startup logic.

**Do not**

- silently rename persisted keys
- break existing configuration without migration/default handling
- let unrelated subsystems read the raw configuration file directly

---

# 5. Hardware

## Current

```text
project.py
```

## `detect_capabilities()`

```python
detect_capabilities() -> dict
```

**Current role**

Detects host capabilities such as:

```text
OS
root status
Ollama availability
GPU availability
```

**v0.2 destination**

```text
slabos/hardware/detector.py
```

**Target direction**

Expose a normalized hardware description instead of making every subsystem probe the operating system itself.

---

## `get_system_vitals()`

```python
get_system_vitals() -> dict
```

**Current role**

Provides information such as:

```text
CPU usage
RAM usage
RAM total
CPU temperature
disk usage
disk total
disk free
```

**Dependency**

```text
psutil
```

**v0.2 destination**

```text
slabos/hardware/telemetry.py
```

---

## `format_telemetry_payload()`

```python
format_telemetry_payload(
    cpu_pct: float,
    ram_pct: float,
    cpu_temp: float,
    active_model: str
) -> dict
```

**Current role**

Normalizes runtime telemetry into the API-facing shape.

**Target**

```text
slabos/hardware/telemetry.py
```

Conceptually:

```text
OS metrics
   ↓
TelemetryManager
   ↓
normalized telemetry
   ↓
API
   ↓
frontend
```

---

## `calculate_zram_size()`

```python
calculate_zram_size(
    total_ram_gb: float,
    max_ratio: float = 0.5
) -> float
```

**Current role**

Calculates a possible ZRAM size.

**Important**

The helper exists, but it is not part of the active main flow.

**v0.2 rule**

Do not turn this into a new system-optimization feature just because the helper exists.

A future implementation may place it under:

```text
slabos/hardware/
```

or a dedicated system-optimization area if that feature is actually designed.

---

# 6. Authentication

## Current

Authentication logic is mainly in:

```text
server.py
project.py
```

## `verify_api_pin()`

```python
verify_api_pin(
    provided_pin: str,
    expected_pin: str
) -> bool
```

**Role**

Compares PIN values safely.

**v0.2 destination**

```text
slabos/auth/manager.py
```

---

## `generate_auth_pin()`

```python
generate_auth_pin(length: int = 4) -> str
```

**Role**

Generates a secure numeric PIN.

**v0.2 destination**

```text
slabos/auth/manager.py
```

---

## `check_access()`

```python
check_access(provided_pin: str) -> tuple[bool, bool]
```

**Current location**

```text
server.py
```

**Current role**

Decides whether the supplied PIN is accepted and whether the caller is an admin.

**v0.2 destination**

```text
slabos/auth/manager.py
```

**Target direction**

Return a structured identity/authorization result rather than forcing routes to understand authentication internals.

Conceptually:

```text
request
  ↓
AuthManager
  ↓
authenticated identity
  ↓
authorization decision
```

---

## Guest access

### `create_guest_pin()`

```text
POST /api/system/guest
```

**Current role**

Creates guest access information and returns guest-related data to the client.

**v0.2 destination**

```text
slabos/api/auth.py
slabos/auth/guests.py
```

**Target ownership**

```text
API controller
    ↓
GuestManager
    ↓
credential / expiry / scope
    ↓
response
```

Guest lifecycle should eventually include:

```text
create
validate
expire
revoke
cleanup
```

---

## Share tokens

### `create_share_token()`

```python
create_share_token(
    filepath: str,
    secret_key: str,
    expiry_seconds: int = 86400
) -> str
```

### `verify_token_access()`

```python
verify_token_access(
    token: str,
    active_tokens: dict
) -> bool
```

**Current state**

These helpers exist, but the complete guest/session lifecycle is not yet implemented around them.

**Possible destination**

```text
slabos/auth/sessions.py
```

or, for guest-only sharing:

```text
slabos/auth/guests.py
```

**Rule**

Avoid maintaining several overlapping credential systems without a clear reason.

---

# 7. Storage

## Current

Storage responsibilities are spread across:

```text
project.py
server.py
```

The v0.2 storage boundary is one of the most important refactors.

---

## Locked decision — Option A

> **SlabOS detects already-mounted external/USB drives. It does not perform OS-level automatic mounting in v0.2.**

Conceptually:

```text
Operating system
      ↓
mounted drive
      ↓
SlabOS detects it
      ↓
storage subsystem exposes it
```

Do not document v0.2 as an automatic USB mounting system.

---

## `setup_media_directory()`

```python
setup_media_directory(raw_path: str) -> str
```

**Current role**

Prepares the configured local media directory.

**v0.2 destination**

```text
slabos/storage/vault.py
```

---

## `verify_path_security()`

```python
verify_path_security(
    requested_path: str,
    base_dir: str
) -> bool
```

**Current role**

Checks whether a requested path is inside an allowed storage boundary.

**v0.2 direction**

Split responsibility between:

```text
slabos/core/security.py
slabos/storage/paths.py
```

Generic security helpers belong in `core`.

Storage-specific path rules belong in `storage`.

The final path decision should use normalized/resolved paths rather than relying on string prefixes.

---

## `get_usb_drives()`

```python
get_usb_drives() -> dict
```

**Current role**

Inspects mounted partitions and identifies usable external storage.

**Current dependency**

```python
psutil.disk_partitions(all=False)
```

**v0.2 destination**

```text
slabos/storage/external.py
```

**Target owner**

```text
ExternalDriveDetector
```

It should detect storage only.

It should not own:

```text
authentication
AI
UI
permission policy
```

---

## `resolve_vault_path()`

```python
resolve_vault_path(subpath: str) -> tuple[str, str]
```

**Current role**

Maps a logical vault path to the configured local media root or an available external-drive path.

**v0.2 direction**

```text
logical path
    ↓
StorageManager
    ↓
storage provider
    ↓
PathSecurity
    ↓
resolved path
```

Possible destinations:

```text
slabos/storage/paths.py
slabos/storage/manager.py
```

---

## Media operations

### `list_media_files()`

```text
GET /api/media/list
```

Target service:

```text
StorageManager.list()
```

### `download_media()`

```text
GET /api/media/download/{filepath:path}
```

Target service:

```text
StorageManager.download()
```

### `upload_media()`

```text
POST /api/media/upload
```

Target service:

```text
StorageManager.upload()
```

v0.2 upload handling should include:

```text
filename validation
size limits
path validation
collision handling
safe temporary writes
atomic finalization
```

### `create_folder()`

```text
POST /api/media/mkdir
```

Target:

```text
StorageManager.create_folder()
```

### `delete_item()`

```text
POST /api/media/delete
```

Target:

```text
StorageManager.delete()
```

Required boundary:

```text
authorization
    +
PathSecurity
```

### `rename_item()`

```text
POST /api/media/rename
```

Target:

```text
StorageManager.rename()
```

### Storage target structure

```text
slabos/storage/
├── paths.py
├── vault.py
├── external.py
└── manager.py
```

A simple mental model:

```text
API
 ↓
StorageManager
 ├── LocalVault
 ├── ExternalDriveDetector
 └── PathSecurity
```

---

# 8. AI

## Current

AI setup is mainly in:

```text
project.py
```

and AI runtime calls are mainly in:

```text
server.py
```

---

## `recommend_ai_model()`

```python
recommend_ai_model(
    ram_gb: float,
    has_gpu: bool,
    disk_free_gb: float = 50.0
) -> str
```

**Current role**

Chooses a model based on available hardware/resources.

**v0.2 destination**

```text
slabos/ai/
```

The important future relationship is:

```text
Hardware profile
      ↓
model recommendation
      ↓
AI model manager
```

The recommendation layer should consume normalized hardware data rather than independently probing the machine.

---

## `get_installed_models()`

```python
get_installed_models() -> list
```

**Current role**

Reads installed Ollama models.

**v0.2 destination**

```text
slabos/ai/ollama.py
```

Possible adapter interface:

```text
OllamaAdapter.list_models()
```

---

## `setup_ollama_model()`

```python
setup_ollama_model(model_name: str) -> bool
```

**Current role**

Checks Ollama availability and prepares/pulls a model.

**v0.2 destination**

```text
slabos/ai/ollama.py
```

Possible adapter operation:

```text
OllamaAdapter.pull_model()
```

---

## `select_ai_model()`

```python
select_ai_model(
    recommended_model: str,
    current_mode: str
) -> str
```

**Current role**

Interactive model selection.

**v0.2 destination**

```text
slabos/ai/manager.py
```

Keep selection policy separate from CLI/UI behavior.

```text
CLI
 ↓
AIManager
 ↓
model policy
```

---

## `check_vision_capabilities()`

```python
check_vision_capabilities(models: list) -> bool
```

**Current role**

Determines whether a known model appears vision-capable.

**v0.2 destination**

```text
slabos/ai/vision.py
```

The implementation may eventually rely more on model metadata instead of model-name keywords.

---

## `stream_ollama_generator()`

```python
stream_ollama_generator(
    prompt: str,
    model_name: str,
    images: List[str] = []
)
```

**Current role**

Calls the local Ollama generation endpoint and streams output.

**v0.2 destination**

```text
slabos/ai/ollama.py
```

The API should not contain raw Ollama HTTP implementation.

---

## `AIManager`

Target responsibility:

```text
slabos/ai/manager.py
```

Conceptually owns:

```text
generate()
stream()
get_active_model()
get_available_models()
supports_vision()
```

The active model should become a **server-authoritative** decision.

A client request must not be trusted to redefine privileged model state.

---

# 9. API

## Current

```text
server.py
```

The current API contains both route handling and service logic.

v0.2 makes routes thinner.

---

## `ChatPayload`

Current fields:

```text
prompt
model
images
```

Current model input should not remain a privileged authority.

Target flow:

```text
request
  ↓
API validation
  ↓
authorization
  ↓
AIManager
  ↓
OllamaAdapter
  ↓
response stream
```

---

## Current route map

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

These routes represent the current baseline.

Do not change them unnecessarily during the refactor.

---

## Target API grouping

The target organization is by responsibility:

```text
api/
├── health.py
├── auth.py
├── system.py
├── ai.py
└── media.py
```

The exact final filenames can change during implementation.

The important boundary is:

```text
HTTP
 ↓
validation
 ↓
authorization
 ↓
service
 ↓
HTTP response
```

---

# 10. API Route Ownership

| Current endpoint | Domain owner | v0.2 controller |
|---|---|---|
| `/` | dashboard | `api/` |
| `/api/vitals` | hardware | `api/health.py` |
| `/api/ai/check-vision` | AI | `api/ai.py` |
| `/api/chat` | AI | `api/ai.py` |
| `/api/system/shutdown` | system | `api/system.py` |
| `/api/system/guest` | auth | `api/auth.py` |
| `/api/media/list` | storage | `api/media.py` |
| `/api/media/download/...` | storage | `api/media.py` |
| `/api/media/upload` | storage | `api/media.py` |
| `/api/media/mkdir` | storage | `api/media.py` |
| `/api/media/delete` | storage | `api/media.py` |
| `/api/media/rename` | storage | `api/media.py` |

Controllers should coordinate services, not reimplement them.

---

# 11. System

## `execute_delayed_shutdown()`

```python
execute_delayed_shutdown()
```

**Current role**

Performs delayed process shutdown behavior.

**v0.2 destination**

```text
slabos/system/
```

or a dedicated system-control service.

---

## `shutdown_server()`

```text
POST /api/system/shutdown
```

**Security requirement**

Shutdown must remain explicitly authorized and admin-only.

Target relationship:

```text
API
 ↓
AuthManager
 ↓
SystemControlService
```

---

# 12. Network

## `sanitize_mdns_hostname()`

```python
sanitize_mdns_hostname(raw_name: str) -> str
```

**Current role**

Sanitizes a hostname before mDNS registration.

**v0.2 destination**

```text
slabos/network/mdns.py
```

---

## `register_mdns_service()`

```python
register_mdns_service(
    hostname: str,
    port: int = 3000
)
```

**Current role**

Registers the local service through Zeroconf/mDNS.

**Dependencies**

```text
socket
zeroconf
```

**v0.2 destination**

```text
slabos/network/mdns.py
```

---

## `generate_ascii_qr()`

```python
generate_ascii_qr(url: str) -> str
```

**Current role**

Creates a terminal-friendly QR representation.

Potential ownership:

```text
slabos/network/
```

If QR generation later becomes specifically tied to guest access, it may belong under auth/guest handling.

Final ownership can be decided when that feature is implemented.

---

# 13. Application Startup

## `main()`

```python
main() -> None
```

**Current role**

Coordinates startup.

Conceptually:

```text
detect capabilities
      ↓
read vitals
      ↓
load configuration
      ↓
interactive/headless setup
      ↓
prepare storage
      ↓
prepare authentication
      ↓
select AI model
      ↓
prepare Ollama
      ↓
save configuration
      ↓
register network service
      ↓
start API server
```

**v0.2 destination**

```text
slabos/main.py
```

The major change is not “delete `main()`”.

The goal is:

> **Make the entry point an orchestrator, not a container for business logic.**

---

## `run_interactive_wizard()`

**Current role**

Collects startup choices such as:

```text
mode
hostname
media directory
```

Potential v0.2 location:

```text
slabos/cli/
```

The wizard should call service interfaces instead of directly implementing storage, AI, or auth behavior.

---

## `render_banner()`

**Current role**

Displays the terminal startup banner.

Possible future location:

```text
slabos/cli/
```

For early v0.2 work, it may remain close to bootstrap code.

---

# 14. Frontend

## Current

```text
templates/index.html
```

Today this file combines:

```text
HTML
CSS
JavaScript
```

v0.2 separates these concerns without requiring a visual redesign.

Target:

```text
frontend/
├── templates/
│   └── index.html
└── static/
    ├── css/
    └── js/
```

---

## Current frontend state

```text
pin
attachedBase64Image
isVisionSupported
currentVaultPath
```

Target direction:

```text
chat state
telemetry state
media state
admin state
```

Each module should own its own state rather than creating one giant global state object.

---

## Current JavaScript functions

### Telemetry

`fetchVitals()`

```text
/api/vitals
```

Target:

```text
static/js/telemetry.js
```

---

### Chat / vision

`checkVisionCapability()`

```text
/api/ai/check-vision
```

`triggerImageSelect()`

`handleImageAttach()`

`clearAttachedImage()`

`handleEnter()`

`sendChat()`

Target:

```text
static/js/chat.js
```

`sendChat()` is responsible for:

```text
collect prompt
build request
send request
read stream
update AI message
```

---

### Media

`fetchMediaList()`

`uploadFile()`

`createFolderPrompt()`

`deleteItem()`

`renameItem()`

Target:

```text
static/js/media.js
```

---

### Admin

`shutdownServer()`

`generateGuest()`

Target:

```text
static/js/admin.js
```

The browser should call the API. It should not directly access filesystems or Ollama.

---

# 15. Core Shared Infrastructure

The target `core/` area is for genuinely shared concerns.

Possible ownership:

```text
slabos/core/
├── errors.py
├── logger.py
└── security.py
```

### `errors.py`

Shared, typed application errors.

### `logger.py`

Central logging behavior.

### `security.py`

Generic security helpers that are not specific to one storage path or UI operation.

Avoid turning `core/` into a dumping ground.

> If a piece of code belongs to one domain, keep it in that domain.

---

# 16. Suggested v0.2 Target Tree

```text
SlabOS/
│
├── slabos/
│   ├── core/
│   │   ├── errors.py
│   │   ├── logger.py
│   │   └── security.py
│   │
│   ├── config/
│   │   ├── schema.py
│   │   └── manager.py
│   │
│   ├── hardware/
│   │   ├── detector.py
│   │   ├── profiles.py
│   │   └── telemetry.py
│   │
│   ├── auth/
│   │   ├── manager.py
│   │   ├── sessions.py
│   │   └── guests.py
│   │
│   ├── ai/
│   │   ├── models.py
│   │   ├── ollama.py
│   │   ├── vision.py
│   │   └── manager.py
│   │
│   ├── storage/
│   │   ├── paths.py
│   │   ├── vault.py
│   │   ├── external.py
│   │   └── manager.py
│   │
│   ├── network/
│   │   └── mdns.py
│   │
│   ├── api/
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── system.py
│   │   ├── ai.py
│   │   └── media.py
│   │
│   ├── system/
│   │   └── ...
│   │
│   └── main.py
│
├── frontend/
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       └── js/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
│
├── docs/
├── deployment/
├── project.py
├── server.py
├── requirements.txt
└── README.md
```

This tree is a **migration target**, not a claim that all of it exists today.

---

# 17. Communication Rules

The preferred dependency direction is:

```text
API
 ↓
Manager / Service
 ↓
Adapter / Provider
 ↓
OS or external service
```

Examples:

### AI

```text
api/ai.py
    ↓
AIManager
    ↓
OllamaAdapter
    ↓
Ollama
```

### Storage

```text
api/media.py
    ↓
StorageManager
    ↓
LocalVault / ExternalDrive
    ↓
filesystem
```

### Authentication

```text
API
 ↓
AuthManager
 ↓
Session / Guest manager
```

### Hardware

```text
API
 ↓
HardwareManager
 ↓
TelemetryManager
 ↓
operating system
```

---

# 18. Coupling to Avoid

These relationships should not become normal architecture:

```text
Frontend  ──X──> filesystem
Frontend  ──X──> Ollama directly

Storage   ──X──> AIManager
AI        ──X──> HTML
Auth      ──X──> DOM
Hardware  ──X──> frontend state

API       ──X──> raw filesystem operations
API       ──X──> raw Ollama HTTP calls
```

The reason is simple:

> A change in one subsystem should not force unrelated subsystems to change.

---

# 19. Where Should I Edit?

## “I need to change file upload.”

Start with:

```text
storage/
```

Then verify the API controller still matches the storage contract.

---

## “I need to change model selection.”

Start with:

```text
ai/
```

Do not put model-selection policy into the HTTP route.

---

## “I need to change PIN behavior.”

Start with:

```text
auth/
```

Do not duplicate PIN logic across routes.

---

## “I need to change mDNS.”

Start with:

```text
network/
```

---

## “I need to change hardware detection.”

Start with:

```text
hardware/
```

---

## “I need a new API endpoint.”

Start with:

```text
api/
```

Then identify the subsystem that actually owns the behavior.

---

## “I need to change dashboard behavior.”

Start with:

```text
frontend/
```

Then update the API contract only when required.

---

# 20. Current Function → Target Owner

| Current function | Target owner |
|---|---|
| `load_or_create_config()` | `config/` |
| `detect_capabilities()` | `hardware/` |
| `get_system_vitals()` | `hardware/` |
| `format_telemetry_payload()` | `hardware/telemetry.py` |
| `recommend_ai_model()` | `ai/` |
| `get_installed_models()` | `ai/ollama.py` |
| `check_vision_capabilities()` | `ai/vision.py` |
| `setup_ollama_model()` | `ai/ollama.py` |
| `select_ai_model()` | `ai/manager.py` |
| `verify_api_pin()` | `auth/` |
| `generate_auth_pin()` | `auth/` |
| `check_access()` | `auth/manager.py` |
| `create_share_token()` | `auth/sessions.py` or `auth/guests.py` |
| `verify_token_access()` | `auth/sessions.py` |
| `verify_path_security()` | `storage/paths.py` + shared security |
| `setup_media_directory()` | `storage/vault.py` |
| `get_usb_drives()` | `storage/external.py` |
| `resolve_vault_path()` | `storage/manager.py` + `storage/paths.py` |
| `sanitize_mdns_hostname()` | `network/mdns.py` |
| `register_mdns_service()` | `network/mdns.py` |
| `generate_ascii_qr()` | `network/` or guest-specific code |
| `main()` | `slabos/main.py` |
| `run_interactive_wizard()` | `cli/` or bootstrap |
| `render_banner()` | CLI/bootstrap |
| `stream_ollama_generator()` | `ai/ollama.py` |

---

# 21. Current API / Frontend → Target Owner

| Current code | Target owner |
|---|---|
| `serve_dashboard()` | `api/` |
| `api_get_vitals()` | `api/health.py` |
| `check_vision_support()` | `api/ai.py` |
| `api_chat_stream()` | `api/ai.py` |
| `shutdown_server()` | `api/system.py` |
| `create_guest_pin()` | `api/auth.py` |
| `list_media_files()` | `api/media.py` |
| `download_media()` | `api/media.py` |
| `upload_media()` | `api/media.py` |
| `create_folder()` | `api/media.py` |
| `delete_item()` | `api/media.py` |
| `rename_item()` | `api/media.py` |
| `fetchVitals()` | `static/js/telemetry.js` |
| `checkVisionCapability()` | `static/js/chat.js` |
| `sendChat()` | `static/js/chat.js` |
| `fetchMediaList()` | `static/js/media.js` |
| `uploadFile()` | `static/js/media.js` |
| `createFolderPrompt()` | `static/js/media.js` |
| `deleteItem()` | `static/js/media.js` |
| `renameItem()` | `static/js/media.js` |
| `shutdownServer()` | `static/js/admin.js` |
| `generateGuest()` | `static/js/admin.js` |

---

# 22. Testing Ownership

Tests should follow subsystem ownership.

Suggested structure:

```text
tests/
├── unit/
│   ├── test_config.py
│   ├── test_security.py
│   ├── test_auth.py
│   ├── test_hardware.py
│   ├── test_storage.py
│   └── test_ai.py
│
├── integration/
│   └── ...
│
└── api/
    └── test_api.py
```

High-value early coverage:

```text
path containment
authentication decisions
configuration loading/saving
hardware contracts
model selection
media operations
upload validation
API authorization
health behavior
error behavior
```

The purpose is not a specific test count.

The purpose is to protect subsystem boundaries during refactoring.

---

# 23. Migration Pattern

Do not move everything at once.

Use:

```text
CURRENT FUNCTION
       ↓
IDENTIFY OWNER
       ↓
NEW SERVICE / MODULE
       ↓
SMALL COMPATIBILITY LAYER
       ↓
FOCUSED TEST
       ↓
VERIFY BEHAVIOR
       ↓
REMOVE OLD PATH LATER
```

This keeps v0.2 incremental.

The existing entry points can remain during migration where doing so preserves compatibility.

---

# 24. Future Extension Points

These are **future**, not current implementations.

### RAG

Potential area:

```text
slabos/rag/
```

Possible pieces:

```text
loader.py
chunker.py
embeddings.py
retriever.py
vector_store.py
```

Conceptually:

```text
storage
   ↓
RAG
   ↓
AIManager
```

---

### Multi-user

Primary ownership:

```text
slabos/auth/
```

It will eventually connect to:

```text
authentication
storage permissions
API
```

---

### Plugins / Apps

Future extension layer.

Do not build the ecosystem during the v0.2 foundation work.

---

### MCP

Potential location:

```text
slabos/integrations/mcp/
```

MCP should sit behind controlled tool boundaries.

---

### Agents

Potential location:

```text
slabos/agents/
```

Agents must still respect:

```text
authentication
authorization
storage boundaries
```

---

### Deployment / Docker

Potential location:

```text
deployment/docker/
```

Deployment infrastructure should remain separate from core service logic.

---

### React

Potential location:

```text
frontend/
```

React would consume the API rather than importing Python modules directly.

---

# 25. What a Contributor Should Not Need to Know

A contributor working on:

```text
slabos/storage/
```

should not need to understand:

```text
Ollama internals
mDNS implementation
dashboard CSS
AI prompting
```

A contributor working on:

```text
slabos/ai/
```

should not need to understand:

```text
filesystem path internals
guest credential lifecycle
dashboard DOM structure
```

That separation is one of the main success criteria of v0.2.

---

# 26. Quick Decision Tree

When adding code:

```text
Does it handle files?
    → storage/

Does it handle AI/models?
    → ai/

Does it authenticate or authorize?
    → auth/

Does it inspect hardware?
    → hardware/

Does it expose HTTP?
    → api/

Does it handle mDNS/network discovery?
    → network/

Does it control system lifecycle?
    → system/

Is it persistent configuration?
    → config/

Is it generic shared infrastructure?
    → core/

Is it browser UI behavior?
    → frontend/
```

When a feature crosses boundaries:

> Put the actual behavior in the smallest responsible subsystem and let a higher-level manager coordinate the interaction.

---

# 27. The v0.2 Rule to Remember

When in doubt:

```text
Find the owner
     ↓
Give it a small interface
     ↓
Keep implementation details private
     ↓
Add a focused test
     ↓
Update this map if ownership changes
```

The goal is not maximum abstraction.

The goal is:

```text
Easy to understand
        +
Safe to change
        +
Easy to test
        +
Easy to extend
        +
Easy for beginners
        +
Easy for contributors
```

---

## Final Note

This document describes the **migration map** from the compact v0.1 implementation to the cleaner v0.2 architecture.

It must remain synchronized with the real repository.

> **Inspect first. Find the owner. Make the smallest safe change. Test it. Then update the map.**
