# SlabOS Development Roadmap

> **Current development line: v0.2 — Foundation / Reliability Upgrade**
>
> This roadmap explains what SlabOS should build next, in what order, and why. It separates current work from future ideas so the project can grow without losing a stable foundation.

---

## 1. Where We Are

SlabOS began as a compact working prototype built mainly around `project.py`, `server.py`, and `templates/index.html`.

The prototype already demonstrates the core product idea:

- local AI through Ollama
- browser-based interaction
- local media storage
- detection of already-mounted external drives
- hardware information and telemetry
- PIN-based access and guest access
- mDNS/local-network discovery
- interactive and headless startup

The current priority is **not** to add every advanced feature.

It is to make the foundation safer, clearer, and easier to extend.

---

## 2. The Road Ahead

```text
v0.1  Prototype
   │
   ▼
v0.2  Foundation / Reliability
   │
   ├── configuration
   ├── authentication
   ├── storage safety
   ├── AI boundary
   ├── hardware boundary
   ├── networking boundary
   ├── API cleanup
   ├── frontend separation
   ├── errors / logging
   └── tests
   │
   ▼
v0.3  Appliance Layer
   │
   ▼
v0.4  AI Model Manager + Hardware Intelligence
   │
   ▼
v0.5  Local Knowledge / RAG
   │
   ▼
v0.6  Multi-user Personal Server
   │
   ▼
v0.7  Plugin / App Ecosystem
   │
   ▼
v0.8  MCP + Agents
   │
   ▼
v1.0  Private AI Appliance
```

The versions after v0.2 are roadmap direction, not promises that every planned feature or implementation detail is already fixed.

---

## 3. v0.2 — Foundation / Reliability

### Goal

Keep the existing product behavior while reducing coupling and improving security, reliability, and maintainability.

### Recommended build order

```text
1. Baseline verification
2. Core shared boundaries
3. Configuration
4. Authentication / authorization
5. Storage
6. AI
7. Hardware
8. Network
9. API
10. Frontend
11. Errors / logging
12. Integration verification
```

The order is deliberately conservative. Each stage should leave the previous stage working.

---

## 4. Stage Details

### Stage 1 — Baseline Verification

**Purpose:** establish a known-good checkpoint before refactoring.

Verify:

- application startup
- current API behavior
- current dashboard behavior
- configuration loading
- AI path
- media operations
- external-drive detection

Add focused tests for the most important existing behavior before large structural changes.

**Done when:** the current baseline can be reproduced and failures can be distinguished from new regression.

---

### Stage 2 — Core Boundaries

**Purpose:** create shared foundations that other subsystems can use without duplicating logic.

Target responsibilities:

- common errors
- logging
- shared security helpers
- application-level shared concepts

Do not build a large framework here.

**Done when:** common cross-cutting behavior has clear ownership and feature modules do not need to reinvent it.

---

### Stage 3 — Configuration

**Purpose:** make persistent settings owned by one subsystem.

Protect the existing configuration keys where practical:

```text
master_pin
default_media_dir
guest_pins
last_mode
last_hostname
last_ai_model
```

Introduce clear load/save/validation behavior and migration/default handling where needed.

**Done when:** configuration can evolve without unrelated modules directly managing the persistence format.

---

### Stage 4 — Authentication & Authorization

**Purpose:** separate credential checking from permission decisions.

Focus on:

- admin access
- guest access
- session/token handling
- expiry and revocation planning
- permission checks

Keep these concepts separate:

```text
authentication → who is presenting credentials?
authorization  → what may that actor do?
```

**Done when:** privileged API actions rely on one clear authentication/authorization boundary instead of duplicated checks.

---

### Stage 5 — Storage

**Purpose:** make file operations safe and predictable.

The locked v0.2 storage decision is:

> **SlabOS detects already-mounted external/USB drives. It does not perform OS-level automatic mounting.**

Build around:

- path normalization and resolved containment
- local media root handling
- already-mounted external-drive discovery
- listing
- upload
- download
- folder creation
- delete
- rename
- filename validation
- upload-size limits
- safe temporary writes and finalization

**Done when:** API routes no longer need to understand filesystem security or storage discovery details.

---

### Stage 6 — AI

**Purpose:** isolate Ollama and model decisions from HTTP routes.

Target responsibilities:

- installed model discovery
- model recommendation
- active model management
- vision capability checks
- generation/streaming
- AI-specific errors

The server should remain authoritative over the active model.

**Done when:** the API can request AI work without directly managing Ollama internals or trusting arbitrary client model selection.

---

### Stage 7 — Hardware

**Purpose:** give the rest of the application a stable description of the host machine.

Current concepts:

- CPU
- RAM
- GPU availability
- CUDA awareness
- operating system/platform
- runtime vitals

Future hardware profiles may include `LOW`, `STANDARD`, `GPU`, and `HIGH`, but they should only be treated as implemented when the code supports them.

**Done when:** hardware information is returned through a clear contract instead of being repeatedly probed throughout the application.

---

### Stage 8 — Network

**Purpose:** isolate local-network behavior.

Current responsibilities include:

- hostname sanitization
- mDNS registration
- local URL handling
- QR representation

**Done when:** networking code owns networking behavior without becoming a catch-all utility layer.

---

### Stage 9 — API Cleanup

**Purpose:** make FastAPI routes thin and predictable.

Target flow:

```text
request
  ↓
validation
  ↓
authorization
  ↓
service call
  ↓
result
  ↓
HTTP response
```

Routes should coordinate services rather than contain storage, AI, or system internals.

**Done when:** business behavior lives behind subsystem boundaries and route handlers are easy to read and test.

---

### Stage 10 — Frontend Separation

**Purpose:** separate presentation concerns without unnecessarily redesigning the UI.

Target structure:

```text
frontend/
├── templates/
└── static/
    ├── css/
    └── js/
```

Keep the existing user-facing concepts recognizable while making JavaScript failures visible enough to debug.

**Done when:** HTML, styling, and browser behavior are separated and frontend modules own their own state where practical.

---

### Stage 11 — Errors & Logging

**Purpose:** make failures understandable and diagnosable.

Use a consistent path:

```text
failure
  ↓
owning subsystem
  ↓
application/domain error
  ↓
useful log
  ↓
safe API response
  ↓
clear user feedback
```

Do not expose sensitive internals just to make debugging easier.

**Done when:** important failures have predictable handling and useful diagnostics.

---

### Stage 12 — Integration Verification

**Purpose:** confirm that the refactored subsystems still behave as one application.

Verify at minimum:

- startup
- configuration persistence
- authentication
- storage operations
- external-drive detection
- AI generation
- hardware telemetry
- network discovery
- API behavior
- frontend behavior

**Done when:** the v0.2 foundation works as a complete system, not only as isolated modules.

---

## 5. What We Are Deliberately Not Building Yet

These remain outside the immediate v0.2 foundation work:

```text
RAG / local knowledge system
Vector database
MCP integration
Agents
Plugin/app ecosystem
Multi-user account system
Automatic USB mounting
Full appliance installer
Cloud synchronization
Distributed storage
```

They may influence boundaries, but they should not drive premature implementation.

---

## 6. Future Releases

### v0.3 — Appliance Layer

Planned focus:

- installer
- first-boot setup
- service-manager integration
- stronger CLI/lifecycle behavior
- clearer deployment story

### v0.4 — AI Model Manager + Hardware Intelligence

Planned focus:

- hardware-aware model selection
- model lifecycle management
- resource-aware behavior
- AI capability profiles

### v0.5 — Local Knowledge / RAG

Planned focus:

- document ingestion
- chunking
- embeddings
- retrieval
- vector storage
- local knowledge workflows

### v0.6 — Multi-user Personal Server

Planned focus:

- users
- permissions
- sessions/accounts
- stronger access separation

### v0.7 — Plugin / App Ecosystem

Planned focus:

- modular applications
- plugin model
- extension registration
- controlled installable capabilities

### v0.8 — MCP + Agents

Planned focus:

- MCP integration
- tool exposure
- agent orchestration
- controlled local automation

### v1.0 — Private AI Appliance

The long-term product direction is a private, local, extensible, hardware-aware, AI-native and storage-aware appliance that remains understandable to contributors.

---

## 7. Definition of Done for v0.2

v0.2 should be considered complete when:

- major subsystems have clear ownership
- existing core behavior still works
- configuration has a defined owner
- authentication and authorization are separated
- storage uses the locked Option A policy
- filesystem containment is handled centrally
- AI/model handling is separated from HTTP routes
- hardware information has a stable contract
- networking is separated from unrelated logic
- API routes are thin
- frontend concerns are separated
- errors and logging are consistent
- subsystem/API tests protect the important boundaries
- documentation matches the actual codebase

The goal is **not** maximum abstraction or maximum feature count.

The goal is a stronger foundation that makes the next features safer to build.

---

## 8. How We Work on the Roadmap

For each milestone:

```text
Inspect
  ↓
Explain
  ↓
Change one boundary
  ↓
Test
  ↓
Verify
  ↓
Document
  ↓
Commit
```

Do not skip from the prototype directly to advanced features because they are exciting. Stabilizing the foundation is what makes those features practical later.

> **Build the foundation once. Then keep extending it without breaking the parts that already work.**
