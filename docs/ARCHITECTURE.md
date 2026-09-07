# SlabOS Architecture

**Project:** SlabOS  
**Architecture document:** v0.2 Foundation / Reliability Upgrade  
**Purpose:** Define the current system, the v0.2 target architecture, exact component ownership, dependency boundaries, migration rules, and future extension points.

> This document is an architectural guide. It is intentionally written so a beginner contributor can understand where a change belongs without reading the entire codebase.

---

# 1. Project Identity

SlabOS is a lightweight, self-hosted local AI and media-server platform intended to reuse existing computer hardware as a private local network node.

The current project combines:

- Local AI through Ollama
- Browser-based AI chat
- Optional image input for supported vision models
- Local file storage
- Detection of already-mounted external/USB drives
- Hardware telemetry
- PIN-based authentication
- Guest access
- mDNS local-network discovery
- Headless startup

The original project vision also emphasizes privacy, sustainability, reuse of old hardware, and low-barrier local AI.

### Important terminology

For v0.2, SlabOS should be described as a **local AI + storage/server platform or appliance layer**, not as a replacement operating system.

---

# 2. v0.1 Baseline

The current repository is intentionally compact:

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

The v0.1 implementation is the baseline that v0.2 must preserve during migration.

### Main responsibilities of the current files

| File | Current responsibility |
|---|---|
| `project.py` | Boot process, configuration, hardware detection, AI setup, mDNS, wizard |
| `server.py` | FastAPI application, authentication checks, AI API, media API, system API |
| `templates/index.html` | Dashboard UI, telemetry display, AI chat, media vault, admin UI |
| `requirements.txt` | Python dependency versions |
| `README.md` | Product description, installation, startup, customization |
| `LICENSE` | Repository license |

---

# 3. Core Architectural Principle

The primary design rule for v0.2 and later versions is:

> **A subsystem exposes a stable interface and hides its implementation details.**

This means a contributor should be able to change the internals of one subsystem without modifying unrelated subsystems.

For example:

```text
Change Ollama implementation
        ↓
AI subsystem changes
        ↓
Frontend does not need to change
```

or:

```text
Change storage implementation
        ↓
Storage subsystem changes
        ↓
AI and authentication do not need to change
```

The project should prefer:

- Small modules
- Clear ownership
- Stable interfaces
- Dependency injection where useful
- Typed inputs and outputs
- Centralized errors
- Centralized logging
- Isolated tests
- Backward-compatible migration where practical

---

# 4. High-Level v0.2 Architecture

```text
                         SlabOS
                            |
                            v
                   Application / Core
                            |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
   Configuration       Hardware Manager    Network Manager
        |                   |                   |
        v                   v                   v
   Config Schema       Hardware Profile        mDNS
                            |
                            v
                       Telemetry
                            |
                            v
                    Service Layer
          +----------------+----------------+
          |                                 |
          v                                 v
      AuthManager                      AIManager
          |                                 |
          v                                 v
   Session / Guest                  OllamaAdapter
                                             |
                                             v
                                           Ollama

                    Service Layer
                           |
                           v
                    StorageManager
                      /           \
                     /             \
                    v               v
               LocalVault    ExternalDriveDetector
                    |
                    v
                Filesystem

                    Service Layer
                           |
                           v
                       API Layer
                           |
                           v
                       Frontend
```

---

# 5. Dependency Direction

The preferred dependency direction is:

```text
Frontend
   ↓
API
   ↓
Service Managers
   ↓
Infrastructure / Adapters
   ↓
Operating System / External Services
```

Core utilities should be lower-level than application services:

```text
API
 ↓
AI / Storage / Auth / Hardware
 ↓
Core
```

### Dependency rules

A subsystem should not import unrelated implementation details.

#### Storage may depend on

- Core logging
- Core security
- Storage provider abstractions
- Configuration

Storage should not depend on:

- HTML
- Frontend state
- Ollama implementation
- AI prompt logic

#### AI may depend on

- Core logging
- Configuration
- Hardware profile
- Inference adapters

AI should not depend on:

- HTML
- Frontend DOM
- Storage implementation details
- Guest-session implementation

#### Authentication may depend on

- Configuration
- Core security
- Core logging

Authentication should not depend on:

- Ollama internals
- Frontend DOM
- Storage provider implementation

---

# 6. Current `project.py` Map

`project.py` currently combines several responsibilities. During migration, these functions should be moved behind subsystem boundaries rather than rewritten without mapping.

## 6.1 Current functions

```text
recommend_ai_model(ram_gb, has_gpu, disk_free_gb=50.0)
calculate_zram_size(total_ram_gb, max_ratio=0.5)
verify_path_security(requested_path, base_dir)
format_telemetry_payload(cpu_pct, ram_pct, cpu_temp, active_model)
sanitize_mdns_hostname(raw_name)
generate_auth_pin(length=4)
verify_api_pin(provided_pin, expected_pin)
create_share_token(filepath, secret_key, expiry_seconds=86400)
verify_token_access(token, active_tokens)
load_or_create_config()
detect_capabilities()
get_installed_models()
check_vision_capabilities(models)
get_system_vitals()
generate_ascii_qr(url)
register_mdns_service(hostname, port=3000)
setup_media_directory(raw_path)
render_banner(title="SlabOS", subtitle="Portable Local AI Node & Media Server")
run_interactive_wizard()
setup_ollama_model(model_name)
select_ai_model(recommended_model, current_mode)
main()
```

## 6.2 Current configuration values

The current persisted configuration contains:

```text
master_pin
default_media_dir
guest_pins
last_mode
last_hostname
last_ai_model
```

## 6.3 Future ownership map

| Current function | v0.2 target owner |
|---|---|
| `recommend_ai_model()` | `slabos/ai/` model recommendation service |
| `calculate_zram_size()` | `slabos/hardware/` or future system optimization module |
| `verify_path_security()` | `slabos/core/security.py` + `slabos/storage/paths.py` |
| `format_telemetry_payload()` | `slabos/hardware/telemetry.py` |
| `sanitize_mdns_hostname()` | `slabos/network/mdns.py` |
| `generate_auth_pin()` | `slabos/auth/manager.py` |
| `verify_api_pin()` | `slabos/auth/manager.py` |
| `create_share_token()` | `slabos/auth/sessions.py` or `guests.py` |
| `verify_token_access()` | `slabos/auth/sessions.py` |
| `load_or_create_config()` | `slabos/config/manager.py` |
| `detect_capabilities()` | `slabos/hardware/detector.py` |
| `get_installed_models()` | `slabos/ai/ollama.py` |
| `check_vision_capabilities()` | `slabos/ai/vision.py` |
| `get_system_vitals()` | `slabos/hardware/telemetry.py` |
| `generate_ascii_qr()` | `slabos/network/` or `slabos/auth/guests.py` |
| `register_mdns_service()` | `slabos/network/mdns.py` |
| `setup_media_directory()` | `slabos/storage/vault.py` |
| `render_banner()` | `slabos/core/` or CLI layer |
| `run_interactive_wizard()` | `slabos/cli/` in a later cleanup |
| `setup_ollama_model()` | `slabos/ai/ollama.py` |
| `select_ai_model()` | `slabos/ai/manager.py` |
| `main()` | `slabos/main.py` |

### Migration rule

The original names should be kept as compatibility wrappers where practical during the transition.

Example:

```text
Old caller
    ↓
project.recommend_ai_model()
    ↓
New ModelRecommendationService
```

This allows migration without breaking everything at once.

---

# 7. Current `server.py` Map

## 7.1 Current classes

```text
ChatPayload
```

Current fields:

```text
prompt
model
images
```

## 7.2 Current functions

```text
check_access(provided_pin)
get_usb_drives()
resolve_vault_path(subpath)
serve_dashboard()
api_get_vitals(pin)
check_vision_support(pin)
stream_ollama_generator(prompt, model_name, images=[])
api_chat_stream(payload, pin)
execute_delayed_shutdown()
shutdown_server(pin)
create_guest_pin(request, pin)
list_media_files(pin, subpath="")
download_media(filepath, pin)
upload_media(pin, subpath="", file)
create_folder(pin, subpath="", folder_name)
delete_item(pin, target_path)
rename_item(pin, old_path, new_name)
run_web_server(host, port, pin, media_dir, active_model)
```

## 7.3 Current application state

Current `app.state` values include:

```text
session_pin
media_dir
active_model
enable_ai
enable_media
```

## 7.4 Future ownership map

| Current component | v0.2 target |
|---|---|
| `check_access()` | `slabos/auth/manager.py` |
| `get_usb_drives()` | `slabos/storage/external.py` |
| `resolve_vault_path()` | `slabos/storage/paths.py` |
| `serve_dashboard()` | `slabos/api/` |
| `api_get_vitals()` | `slabos/api/health.py` or `system.py` |
| `check_vision_support()` | `slabos/ai/vision.py` + AI API |
| `stream_ollama_generator()` | `slabos/ai/ollama.py` |
| `api_chat_stream()` | `slabos/api/ai.py` |
| `execute_delayed_shutdown()` | `slabos/api/system.py` or system service |
| `shutdown_server()` | `slabos/api/system.py` |
| `create_guest_pin()` | `slabos/api/auth.py` + `slabos/auth/guests.py` |
| `list_media_files()` | `slabos/api/media.py` + `StorageManager` |
| `download_media()` | `slabos/api/media.py` + `StorageManager` |
| `upload_media()` | `slabos/api/media.py` + `StorageManager` |
| `create_folder()` | `slabos/api/media.py` + `StorageManager` |
| `delete_item()` | `slabos/api/media.py` + `StorageManager` |
| `rename_item()` | `slabos/api/media.py` + `StorageManager` |
| `run_web_server()` | `slabos/main.py` / server bootstrap |

---

# 8. Current Frontend Map

The current dashboard is implemented in:

```text
templates/index.html
```

The current UI contains:

- System Vitals
- Active AI model display
- Vision capability status
- AI chat
- Image attachment
- Media vault
- Folder navigation
- Upload
- Drag-and-drop upload
- Rename
- Delete
- Download/access
- Admin shutdown
- Guest QR generation

## Current frontend logic

The current JavaScript contains functions for:

```text
fetchVitals()
checkVisionCapability()
triggerImageSelect()
handleImageAttach()
clearAttachedImage()
handleEnter()
sendChat()
fetchMediaList()
uploadFile()
createFolderPrompt()
deleteItem()
renameItem()
shutdownServer()
generateGuest()
```

## v0.2 frontend target

```text
templates/
└── index.html

static/
├── css/
│   └── dashboard.css
└── js/
    ├── dashboard.js
    ├── telemetry.js
    ├── chat.js
    ├── media.js
    └── admin.js
```

The frontend should consume API contracts and should not know how Python services are implemented internally.

---

# 9. Storage Architecture

## 9.1 v0.2 storage decision

**Option A is locked.**

SlabOS v0.2 will:

- Detect already-mounted external/USB drives.
- Expose detected drives through the storage layer.
- Keep local vault storage.
- NOT perform OS-level automatic mounting.

The current implementation uses `psutil.disk_partitions()` to discover mounted partitions.

The README should eventually be updated so it does not describe this as automatic OS mounting.

## 9.2 Target structure

```text
slabos/storage/
├── manager.py
├── paths.py
├── vault.py
└── external.py
```

## 9.3 Responsibilities

### `paths.py`

Responsible for:

- Path normalization
- Path resolution
- Containment checks
- Path traversal protection

### `vault.py`

Responsible for:

- Local vault directory
- File operations against the local vault

### `external.py`

Responsible for:

- Detecting already-mounted external drives
- Returning normalized external-drive information

### `manager.py`

Responsible for:

- Selecting a storage provider
- Presenting a stable storage API
- Coordinating local and external storage

## 9.4 Stable storage interface

```text
StorageManager
├── list()
├── upload()
├── download()
├── create_folder()
├── delete()
├── rename()
└── get_storage_info()
```

The API layer should call `StorageManager`, not raw filesystem code.

---

# 10. Authentication Architecture

## 10.1 Current model

Current system:

```text
Master PIN → Admin
Guest PIN  → Guest
```

## 10.2 v0.2 target

```text
slabos/auth/
├── manager.py
├── sessions.py
└── guests.py
```

### `manager.py`

Responsible for:

- Authentication
- Role determination
- Permission checks

### `sessions.py`

Responsible for:

- Session/token lifecycle
- Expiry
- Validation
- Revocation

### `guests.py`

Responsible for:

- Guest creation
- Guest expiry
- Guest revocation
- Guest status

## 10.3 Guest lifecycle

```text
Admin
  ↓
Create guest
  ↓
Generate credential
  ↓
Store expiry
  ↓
Generate QR
  ↓
Guest connects
  ↓
Validate
  ↓
Active
  ↓
Expired or revoked
```

The existing token functions in `project.py` are candidates for integration into this lifecycle.

---

# 11. Security Architecture

All filesystem operations should use a centralized security boundary.

Preferred flow:

```text
Input path
   ↓
Normalize
   ↓
Resolve absolute path
   ↓
Determine allowed storage root
   ↓
Containment validation
   ↓
Permission validation
   ↓
Filesystem operation
```

Security checks should be applied consistently to:

- Directory listing
- Upload
- Download
- Rename
- Delete
- Folder creation

Additional v0.2 security goals:

- Safe filename handling
- Upload-size limits
- Clear file-path validation
- No client-controlled authorization
- No client-controlled active AI model execution
- Safe error messages
- Guest expiry/revocation
- Request logging without secrets

---

# 12. AI Architecture

## 12.1 Current AI flow

```text
Browser
  ↓
POST /api/chat
  ↓
check_access()
  ↓
stream_ollama_generator()
  ↓
Ollama
  ↓
Streaming response
  ↓
Browser
```

## 12.2 v0.2 target

```text
Browser
  ↓
AI API
  ↓
AuthManager
  ↓
AIManager
  ↓
ModelManager / model selection
  ↓
OllamaAdapter
  ↓
Ollama
```

## 12.3 Target files

```text
slabos/ai/
├── manager.py
├── models.py
├── ollama.py
└── vision.py
```

### `manager.py`

Responsible for:

- Active model
- AI service coordination
- Generation interface
- Model-level validation

### `models.py`

Responsible for:

- Model metadata
- Model records
- Model recommendation structures

### `ollama.py`

Responsible for:

- Ollama communication
- Installed-model listing
- Model pulling
- Generation streaming

### `vision.py`

Responsible for:

- Vision capability determination
- Vision-related validation

## 12.4 Important rule

The frontend must not be the authority for which model the server executes.

The server should validate/use its configured active model through `AIManager`.

---

# 13. Hardware Architecture

## 13.1 Current information collected

Current hardware/capability code can determine:

```text
OS
Administrative/root status
Ollama availability
GPU presence
CPU usage
RAM usage
RAM total
CPU temperature when available
Disk usage
Disk total
Disk free
```

## 13.2 v0.2 target

```text
slabos/hardware/
├── detector.py
├── profiles.py
└── telemetry.py
```

### `detector.py`

Discovers system capabilities.

### `profiles.py`

Represents a normalized hardware profile.

### `telemetry.py`

Provides live system metrics.

Target abstraction:

```text
HardwareManager
├── get_profile()
└── get_telemetry()
```

---

# 14. Configuration Architecture

Target:

```text
slabos/config/
├── manager.py
└── schema.py
```

### `schema.py`

Defines the shape and validation rules of SlabOS configuration.

### `manager.py`

Responsible for:

- Loading
- Validating
- Saving
- Migration
- Defaults
- Reset/recovery

The configuration should eventually be versioned:

```json
{
  "version": 2,
  "auth": {},
  "storage": {},
  "ai": {},
  "network": {},
  "system": {}
}
```

The exact schema can evolve, but versioning must exist before major migrations are introduced.

---

# 15. Core Layer

Target:

```text
slabos/core/
├── logger.py
├── errors.py
├── security.py
└── response.py
```

## `logger.py`

Central logging.

Suggested categories:

```text
BOOT
AUTH
AI
STORAGE
NETWORK
SYSTEM
API
SECURITY
```

Suggested levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

## `errors.py`

Typed internal errors, such as:

```text
ConfigurationError
AuthenticationError
AuthorizationError
StorageError
PathSecurityError
AIError
ModelUnavailableError
NetworkError
HardwareError
```

## `security.py`

Reusable low-level security helpers.

## `response.py`

Standardized API response/error formatting.

---

# 16. Network Architecture

Target:

```text
slabos/network/
└── mdns.py
```

Responsible for:

- Hostname sanitization
- Local address discovery
- mDNS registration
- mDNS cleanup

The current mDNS behavior should remain isolated from AI and storage.

---

# 17. API Architecture

Target:

```text
slabos/api/
├── health.py
├── auth.py
├── system.py
├── ai.py
└── media.py
```

## Proposed v0.2 API groups

```text
/api/v1/health

/api/v1/system/status
/api/v1/system/telemetry

/api/v1/auth/login
/api/v1/auth/guest
/api/v1/auth/logout

/api/v1/ai/models
/api/v1/ai/capabilities
/api/v1/ai/chat

/api/v1/storage/list
/api/v1/storage/upload
/api/v1/storage/download/{path}
/api/v1/storage/folder
/api/v1/storage/delete
/api/v1/storage/rename
```

### Migration policy

Existing v0.1 routes should not be removed immediately.

Where practical:

```text
Old API
   ↓
Compatibility wrapper
   ↓
New service
```

This prevents an architectural rewrite from becoming a functionality rewrite.

---

# 18. Application State

Current state is stored through:

```text
app.state.session_pin
app.state.media_dir
app.state.active_model
app.state.enable_ai
app.state.enable_media
```

v0.2 should gradually move toward an application context:

```text
ApplicationContext
├── config
├── auth
├── hardware
├── ai
├── storage
└── network
```

The exact implementation can be introduced incrementally.

---

# 19. Request Flow Reference

## AI request

```text
User
 ↓
Frontend chat
 ↓
AI API
 ↓
Authentication
 ↓
AIManager
 ↓
OllamaAdapter
 ↓
Ollama
 ↓
Stream
 ↓
Frontend
```

## File upload

```text
User
 ↓
Frontend
 ↓
Storage API
 ↓
Authentication
 ↓
Path Security
 ↓
StorageManager
 ↓
LocalVault / ExternalDrive
 ↓
Filesystem
```

## Telemetry

```text
Frontend
 ↓
Telemetry API
 ↓
TelemetryManager
 ↓
HardwareDetector / OS metrics
 ↓
HardwareProfile / snapshot
 ↓
Frontend
```

## Guest access

```text
Admin
 ↓
GuestManager
 ↓
Guest credential + expiry
 ↓
QR
 ↓
Guest browser
 ↓
Authentication
 ↓
Permission check
 ↓
Service
```

---

# 20. Error Flow

All service errors should follow:

```text
Subsystem
   ↓
Typed internal exception
   ↓
Central error handler
   ↓
Logger
   ↓
Safe API response
   ↓
Frontend
```

Avoid returning raw internal exceptions whenever possible.

Example future response:

```json
{
  "error": {
    "code": "AI_MODEL_UNAVAILABLE",
    "message": "The configured AI model is unavailable.",
    "request_id": "SLAB-123456"
  }
}
```

---

# 21. Request Tracking

v0.2 should introduce a request identifier.

Preferred flow:

```text
Incoming request
      ↓
Request ID created
      ↓
API
      ↓
Service
      ↓
Logger
      ↓
Response
```

The request ID should appear in logs and safe error responses.

---

# 22. Testing Architecture

Target:

```text
tests/
├── test_config.py
├── test_security.py
├── test_auth.py
├── test_hardware.py
├── test_storage.py
├── test_ai.py
└── test_api.py
```

## Test strategy

### Unit tests

Test a single function/class without requiring the whole application.

### Integration tests

Test service-to-service behavior.

### API tests

Test request/response contracts.

### Regression tests

Protect the v0.1 behavior that v0.2 must preserve.

---

# 23. Frontend Migration

The current `index.html` is a working prototype and should not be discarded.

Migration sequence:

```text
Current index.html
      ↓
Extract CSS
      ↓
Extract JavaScript
      ↓
Keep same UI behavior
      ↓
Connect to stable API
      ↓
Improve UI later
```

The first frontend refactor should focus on separation, not a complete visual redesign.

A future React frontend should be treated as a client of the API, not as a rewrite of backend service logic.

---

# 24. v0.2 Migration Strategy

Do not replace the entire v0.1 implementation in a single commit.

Recommended order:

```text
1. Documentation
2. Core logging/errors/security
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

Each migration stage follows:

```text
Current implementation
        ↓
Create new subsystem
        ↓
Add tests
        ↓
Connect compatibility wrapper
        ↓
Run existing behavior
        ↓
Verify
        ↓
Commit
```

Only after the replacement is proven should obsolete code be removed.

---

# 25. Future Extension Boundaries

Future features must have an architectural home before they are implemented.

## RAG

Planned location:

```text
slabos/rag/
```

Relationship:

```text
Storage
   ↓
RAG
   ↓
AIManager
```

Possible future components:

```text
loader.py
chunker.py
embeddings.py
retriever.py
vector_store.py
```

## Vector database

Planned location:

```text
slabos/rag/vector_store.py
```

It should not be embedded directly inside `StorageManager` or `AIManager`.

## MCP

Planned location:

```text
slabos/integrations/mcp/
```

Relationship:

```text
AI / Agents
    ↓
Tools
    ↓
MCP
```

## Agents

Planned location:

```text
slabos/agents/
```

Agents should use controlled tools rather than directly changing filesystem or system internals.

## React

Planned location:

```text
frontend/
```

It should consume the SlabOS API.

## Docker

Planned location:

```text
deployment/docker/
```

## Multi-user support

Planned location:

```text
slabos/auth/
```

with connections to:

```text
Authentication
Storage permissions
API
```

## App ecosystem

Planned future location:

```text
apps/
plugins/
integrations/
```

Exact structure will be defined when that version is designed.

---

# 26. Future Version Direction

The intended high-level evolution is:

```text
v0.1
Current prototype
   ↓
v0.2
Foundation + reliability
   ↓
v0.3
Appliance + installation + service management
   ↓
v0.4
AI model management + hardware intelligence
   ↓
v0.5
Local knowledge / RAG
   ↓
v0.6
Multi-user personal server
   ↓
v0.7
Application / plugin ecosystem
   ↓
v0.8
MCP + agent capabilities
   ↓
v1.0
Private AI appliance
```

Future versions are not part of the v0.2 implementation scope unless explicitly promoted.

---

# 27. Features Explicitly Outside v0.2

Do not add these during the foundation migration:

```text
RAG
Vector databases
MCP
Agents
Multi-user accounts
App marketplace
Docker ecosystem
Cloud synchronization
Distributed storage
OS-level automatic USB mounting
```

They remain documented future extension points.

---

# 28. Contributor Change Guide

A contributor should use this table first.

| Change wanted | Main location |
|---|---|
| AI behavior | `slabos/ai/` |
| Ollama communication | `slabos/ai/ollama.py` |
| Model metadata | `slabos/ai/models.py` |
| Vision support | `slabos/ai/vision.py` |
| File operations | `slabos/storage/` |
| Path security | `slabos/storage/paths.py` / `slabos/core/security.py` |
| External-drive detection | `slabos/storage/external.py` |
| Storage coordination | `slabos/storage/manager.py` |
| Authentication | `slabos/auth/` |
| Guest access | `slabos/auth/guests.py` |
| Sessions/tokens | `slabos/auth/sessions.py` |
| Hardware discovery | `slabos/hardware/detector.py` |
| Hardware profiles | `slabos/hardware/profiles.py` |
| Telemetry | `slabos/hardware/telemetry.py` |
| Configuration | `slabos/config/` |
| mDNS/network | `slabos/network/mdns.py` |
| API endpoints | `slabos/api/` |
| Error handling | `slabos/core/errors.py` |
| Logging | `slabos/core/logger.py` |
| Frontend layout | `templates/` |
| Frontend styles | `static/css/` |
| Frontend behavior | `static/js/` |
| Tests | `tests/` |
| Architecture documentation | `docs/` |

---

# 29. Definition of Done for v0.2 Architecture

The architecture phase is complete when:

- The major subsystems have clear ownership.
- Current v0.1 behavior has a migration path.
- Existing functions are mapped to future modules.
- APIs have an intended ownership boundary.
- Storage uses the Option A policy.
- Authentication has a defined session/guest lifecycle.
- AI communication is behind an adapter/manager.
- Hardware information is normalized.
- Logging and errors are centralized.
- Testing is organized by subsystem.
- Frontend implementation is separated from backend implementation.
- Future features have defined extension locations.
- Documentation tells contributors where to make changes.
- No future feature requires putting unrelated logic into `project.py` or `server.py`.

---

# 30. Architecture Maintenance Rule

This document must be updated whenever the architecture changes.

When adding or moving a subsystem, update:

```text
docs/ARCHITECTURE.md
docs/COMPONENT_MAP.md
docs/DEVELOPMENT_ROADMAP.md
CHANGELOG.md
```

Do not allow the code and architecture documentation to diverge.

The documentation is part of the product.

---

# 31. Current Known Issues to Track

These are documented as v0.2 work items, not as already-fixed behavior.

### License inconsistency

The current `project.py` header identifies MIT while the README identifies AGPLv3. This must be resolved before community contribution workflows are finalized.

### External-drive wording

The README currently describes automatic USB mounting, while the current implementation detects mounted partitions. v0.2 should use accurate wording unless true OS-level mounting is implemented later.

### Guest lifecycle

Guest credentials are currently stored as active entries without a complete expiry/revocation lifecycle. v0.2 should implement explicit guest lifecycle management.

### Filesystem security

The current API uses path checks that should be centralized into a robust resolved-path containment mechanism.

### Upload validation

The upload path needs stronger filename validation, limits, and safer write behavior.

### Client-controlled model selection

The API currently accepts the requested model from the client. v0.2 should make the configured/authorized active model server-authoritative.

---

# 32. Final Architecture Rule

The long-term SlabOS rule is:

> **Add new functionality through a dedicated module and stable interface whenever practical. Do not put unrelated functionality into an existing large file simply because it is convenient.**

The objective is not maximum abstraction.

The objective is:

```text
Simple to understand
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

That is the architecture standard for SlabOS v0.2 and future versions.

---

## Source baseline checked for this document

This architecture document was checked against the current uploaded SlabOS source snapshot:

- `project.py`
- `server.py`
- `templates/index.html`
- `README.md`
- `requirements.txt`

The function, class, configuration-key, application-state, and API names recorded in this document were cross-checked against those uploaded files before this document was produced.
