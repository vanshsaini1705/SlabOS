# SlabOS Architecture

> **v0.2 — Foundation / Reliability Upgrade**
>
> SlabOS is a **local AI + storage/server platform** designed to give reusable computers a second life as private, self-hosted nodes.

## Start Here

SlabOS is **not a replacement operating system at this stage**. It is a small Python application that brings together local AI, storage, hardware information, networking, and a browser dashboard.

The purpose of **v0.2** is simple:

> **Keep the useful prototype, but make its boundaries clearer, its security stronger, and its code easier to extend.**

The project should grow one responsibility at a time instead of turning a few large files into a larger tightly-coupled system.

---

## 1. Mental Model

```text
                    ┌───────────────────┐
                    │     Browser       │
                    │  SlabOS Dashboard │
                    └─────────┬─────────┘
                              │ HTTP
                              ▼
                    ┌───────────────────┐
                    │     API Layer     │
                    │  FastAPI routes   │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
     ┌─────────┐         ┌─────────┐         ┌──────────┐
     │  Auth   │         │   AI    │         │ Storage  │
     │ access  │         │ Ollama  │         │ files    │
     └─────────┘         └─────────┘         └──────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                    ┌───────────────────┐
                    │ Core / Config /   │
                    │ shared app rules  │
                    └───────────────────┘

        Supporting areas: Hardware · Network · System · Tests
```

The important idea is **ownership**, not the exact folder names.

A route should coordinate a request, not own filesystem security. AI code should not own HTTP behavior. Networking code should not own configuration. Each subsystem should have a clear responsibility.

---

## 2. Current System — v0.1 Baseline

The current repository is intentionally compact:

```text
SlabOS/
├── project.py
├── server.py
├── requirements.txt
├── README.md
├── LICENSE
└── templates/
    └── index.html
```

### Current responsibilities

| Area | Current location | Main responsibility |
|---|---|---|
| Startup / setup | `project.py` | detection, configuration, wizard, model setup, startup orchestration |
| API / server | `server.py` | FastAPI app, access checks, AI, media, system actions |
| Frontend | `templates/index.html` | HTML, CSS and JavaScript dashboard |
| Configuration | runtime `slabos_config.json` | saved settings and state |
| Dependencies | `requirements.txt` | pinned Python dependencies |

This works as a prototype, but too many responsibilities are concentrated in `project.py` and `server.py`.

That is the main problem v0.2 is solving.

---

## 3. Current Runtime Flow

```text
project.py
   │
   ├─ detect capabilities
   ├─ read system vitals
   ├─ load/create config
   ├─ interactive or headless setup
   ├─ prepare media directory
   ├─ prepare authentication settings
   ├─ select/recommend AI model
   ├─ prepare Ollama model
   ├─ save configuration
   ├─ register local-network service
   │
   └──────────────► start FastAPI server
                         │
                         ▼
                      server.py
```

`project.py` is mainly the **setup/startup orchestrator**.

`server.py` is mainly the **web/API runtime**.

v0.2 should preserve the recognizable startup experience while moving responsibilities behind clearer boundaries.

---

## 4. Current API Surface

The current server includes:

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

The problem is not that these routes exist. The problem is that route code currently knows too much about the underlying work.

### v0.2 request flow

```text
HTTP request
      ↓
validation
      ↓
authentication / authorization
      ↓
domain or service call
      ↓
service result
      ↓
HTTP response
```

> **Routes coordinate. Services own behavior.**

---

## 5. v0.2 Target Architecture

The target structure is:

```text
SlabOS/
├── slabos/
│   ├── config/       # persistent configuration
│   ├── auth/         # authentication and authorization
│   ├── storage/      # files, paths, mounted-drive discovery
│   ├── ai/           # model management and Ollama integration
│   ├── hardware/     # machine capability detection and vitals
│   ├── network/      # hostname and mDNS behavior
│   ├── api/          # thin HTTP routes/controllers
│   ├── core/         # shared application concepts
│   ├── errors/       # common application errors
│   ├── logging/      # shared logging behavior
│   └── system/       # system/lifecycle actions
│
├── frontend/
│   ├── templates/
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

**This is a target architecture, not a claim that every directory already exists.**

The repository is always the implementation source of truth.

---

## 6. Who Owns What?

### Configuration

Owns persistent application settings such as the master PIN, media directory, guest PIN data, hostname, mode, and active AI model.

### Authentication & Authorization

Owns access decisions.

Keep these separate:

```text
authentication → who is presenting credentials?
authorization  → is that actor allowed to do this?
```

### Storage

Owns filesystem behavior:

- path normalization and containment
- media listing
- uploads/downloads
- folder creation
- delete/rename
- mounted external-drive discovery

The API should not implement these rules itself.

### AI

Owns:

- installed model discovery
- model recommendation/selection
- active model management
- vision capability checks
- Ollama generation

The server should not trust an arbitrary client-selected model as privileged state.

### Hardware

Owns machine capability information such as CPU, RAM, GPU availability, CUDA awareness, platform, and system vitals.

### Network

Owns hostname sanitization, mDNS registration, local URL information, and QR representation.

### System

Owns privileged lifecycle operations such as shutdown.

### API

Owns HTTP concerns:

- request parsing
- validation
- auth coordination
- service calls
- response formatting

### Frontend

Owns presentation and interaction. It displays state, collects input, calls APIs, and shows useful errors.

---

## 7. Locked Storage Decision — Option A

This decision is **locked for v0.2**:

> **SlabOS detects already-mounted external/USB drives. It does not perform OS-level automatic mounting.**

The intended flow is:

```text
Operating system
      ↓
mounts drive
      ↓
mounted filesystem
      ↓
SlabOS detects it
      ↓
Storage subsystem exposes it
```

This keeps v0.2 focused on application reliability instead of turning SlabOS into an OS-level mount manager.

Use this wording in documentation:

> **SlabOS detects and exposes already-mounted external storage.**

Do not describe v0.2 as automatically mounting USB drives.

---

## 8. Security Boundaries

Local-first does not automatically mean secure.

Security-sensitive areas include:

```text
PINs · guest access · tokens · paths · uploads · downloads
AI model selection · shutdown · future users · remote integrations
```

A healthy boundary is:

```text
authentication
      ↓
authorization
      ↓
validation
      ↓
business logic
```

Examples:

- A valid PIN does not mean every action is allowed.
- A valid request does not make an unsafe path safe.
- A safe path does not grant permission to modify it.

v0.2 should replace fragile string-prefix path checks with proper resolved-path containment and give uploads a clear validation/finalization boundary.

---

## 9. Frontend Direction

Today the dashboard is concentrated in:

```text
templates/index.html
```

v0.2 should separate presentation assets without requiring a visual rewrite:

```text
frontend/
├── templates/
│   └── index.html
└── static/
    ├── css/
    └── js/
```

The existing concepts should remain recognizable:

- System Vitals
- Secure AI Link
- vision/image support
- Secure Media Vault
- drag-and-drop upload
- Admin Command Center

---

## 10. Testing & Reliability

Tests exist to make refactoring safer, not to hit an arbitrary test count.

The v0.2 structure is:

```text
tests/
├── unit/
├── integration/
└── api/
```

Early protection should cover the most important boundaries:

- path containment
- authentication/authorization
- configuration persistence
- hardware detection contracts
- model selection
- media operations
- upload validation
- API authorization
- health/error behavior

---

## 11. Current → v0.2 Direction

```text
project.py
  ├─ config            → config/
  ├─ hardware          → hardware/
  ├─ AI/model logic    → ai/
  ├─ auth/security     → auth/
  ├─ storage helpers   → storage/
  ├─ network helpers   → network/
  └─ startup/CLI       → orchestration

server.py
  ├─ auth              → auth/
  ├─ media/files       → storage/
  ├─ Ollama            → ai/
  ├─ shutdown          → system/
  └─ HTTP routes       → api/
```

This migration should happen **incrementally**. Do not rewrite the whole project at once.

---

## 12. Future Extension Points

The architecture intentionally leaves room for later versions:

| Future | Intended area |
|---|---|
| Appliance / installer | `deployment/` |
| Hardware-aware AI | `slabos/ai/` + `slabos/hardware/` |
| RAG / local knowledge | `slabos/rag/` |
| Multi-user system | `slabos/auth/` |
| Plugins / apps | future extension layer |
| MCP | `slabos/integrations/mcp/` |
| Agents | `slabos/agents/` |

These are **future extension points**, not current implemented features.

---

## 13. Architecture Principles

SlabOS should stay:

- modular
- low-coupling
- local-first
- understandable to contributors
- safe to extend
- honest about implementation status

Prefer:

```text
small change
   ↓
clear owner
   ↓
focused test
   ↓
verify behavior
```

Avoid:

```text
one problem
   ↓
rewrite everything
```

Do not add abstractions, dependencies, services, or future features just because they look modern. Add them when they solve a real problem.

---

## 14. Source of Truth

When documentation and code disagree:

```text
1. Actual repository code
2. Tests / executable behavior
3. Master project context
4. Historical discussion
5. General assumptions
```

Always distinguish:

```text
CURRENT
v0.2 TARGET
FUTURE
```

Never document a planned subsystem as implemented.

---

## Final Mental Model

SlabOS is becoming more modular **before** becoming more complicated.

```text
v0.1 prototype
      ↓
v0.2 stronger foundation
      ↓
clear boundaries + safer storage + better tests
      ↓
future AI / RAG / multi-user / plugins / MCP / agents
      ↓
private AI appliance
```

> **Inspect first. Preserve what works. Change one boundary at a time. Test it. Document why.**
