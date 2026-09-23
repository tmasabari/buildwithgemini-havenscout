# HavenScout - Comprehensive Project Context & Resumption Guide

This document contains full technical details, credentials configuration, architectural breakdown, and step-by-step instructions to resume development and deployment of **HavenScout** in a fresh VM environment.

---

## 📌 Project Overview

- **Project Name**: HavenScout
- **Description**: An AI Real Estate & Apartment Finder agent built using the **Google Agent Development Kit (ADK)** and deployed to **Agent Runtime on Vertex AI**.
- **Key Capabilities**:
  - **Firestore Database Integration**: Search property listings, schedule property viewing tours, record listings, and compute move-in costs & affordability ratios.
  - **Google Maps REST APIs**: Convert street addresses to geographical coordinates (Geocoding API) and search nearby points of interest (Places API New).
  - **Gemini Image Generation**: Generates property interior decor previews using `gemini-3.1-flash-lite-image`, automatically saving them as ADK session artifacts and uploading to a public Google Cloud Storage bucket.
  - **A2UI v0.8 Rich Card Formatting**: Generates native A2UI JSON components (`Card`, `Column`, `Row`, `Text`, `Image`) rendered directly in the custom web chat UI.
  - **Sandbox Code Execution**: Runs Python code snippets safely in a managed Agent Engine sandbox using `AgentEngineSandboxCodeExecutor`.
  - **FastAPI Web Proxy & UI**: Includes a lightweight FastAPI frontend proxy in `./frontend` communicating over the **A2A protocol**.

---

## ⚙️ GCP Infrastructure & Credentials Metadata

| Resource | Value / Name | Notes |
| :--- | :--- | :--- |
| **GCP Project ID** | `qwiklabs-gcp-01-bd458d080332` | Hardcoded as string in Firestore/GCS tools |
| **GCP Region** | `us-east1` | Agent Runtime location |
| **Reasoning Engine Resource ID** | `projects/641471327587/locations/us-east1/reasoningEngines/5340611650107998208` | Agent Engine sandbox resource |
| **Public GCS Bucket** | `havenscout-media-qwiklabs-gcp-01-bd458d080332` | Public bucket for generated images |
| **Agent Service Account** | `service-641471327587@gcp-sa-aiplatform-re.iam.gserviceaccount.com` | Granted `roles/datastore.user` & `roles/storage.objectAdmin` |
| **Primary LLM Model** | `gemini-2.5-flash` | Used for tool calling and reasoning |
| **Image Model** | `gemini-3.1-flash-lite-image` | Executed in `global` region |

---

## 🔑 Environment Variables (`.env`)

Create a `.env` file in the project root (`./.env`) with the following settings:

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-01-bd458d080332
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_MAPS_API_KEY=AIzaSyChOXruBh6Fbads6EkpFydxVkhL_Pidghk
```

---

## 📁 Repository Structure

```
havenscout/
├── app/
│   ├── __init__.py
│   ├── agent.py                 # Core agent definition, prompt, model & CustomCodeExecutor
│   ├── a2ui_utils.py            # A2UI v0.8 schema callback & image sanitization
│   └── tools/
│       ├── __init__.py
│       ├── firestore_tools.py   # Firestore CRUD, move-in calculator & GCS image uploads
│       ├── google_maps_tools.py # Google Maps Geocoding & Places (New) REST tools
│       └── image_generation_tool.py # Gemini 3.1 Flash Lite Image generation tool
├── frontend/
│   ├── main.py                  # FastAPI proxy talking A2A protocol to Agent Runtime
│   ├── requirements.txt         # Frontend dependencies (fastapi, uvicorn, a2a-sdk)
│   └── static/
│       └── index.html           # Plain chat web UI with native A2UI card renderer
├── agents-cli-manifest.yaml     # Agent deployment manifest
├── deployment_metadata.json     # Active Reasoning Engine deployment metadata
├── pyproject.toml               # Python dependencies managed via uv
└── PROJECT_CONTEXT.md           # Project context & resumption guide (this file)
```

---

## 🛠️ Key Implementation & Fixes Reference

1. **Picklable Code Executor (`CustomCodeExecutor`)**:
   - `AgentEngineSandboxCodeExecutor` in ADK contains `threading.Lock()` which fails `cloudpickle` during `agents-cli deploy`.
   - Solved in [`app/agent.py`](file:///config/Desktop/Session1/havenscout/app/agent.py) via a custom subclass:
     ```python
     class CustomCodeExecutor(AgentEngineSandboxCodeExecutor):
         def __getstate__(self):
             state = self.__dict__.copy()
             state["_agent_engine_creation_lock"] = None
             return state

         def __setstate__(self, state):
             self.__dict__.update(state)
             self._agent_engine_creation_lock = threading.Lock()
     ```

2. **Memory Callback Safeguard**:
   - `generate_memories_callback` in [`app/agent.py`](file:///config/Desktop/Session1/havenscout/app/agent.py) wraps `add_session_to_memory()` in a `try...except` block so local testing without Vertex AI Memory Bank does not crash agent output.

3. **FastAPI A2A Proxy (`frontend/main.py`)**:
   - Connects to Agent Engine passthrough URL `https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/.../api/a2a/app`.
   - Authenticates via ADC and parses A2UI data parts tagged `application/json+a2ui`.

---

## 🚀 How to Resume in a New VM

### Step 1: Clone Repository & Setup Environment
```bash
git clone https://github.com/tmasabari/buildwithgemini-havenscout.git
cd buildwithgemini-havenscout

# Create .env file
cat <<'EOF' > .env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-01-bd458d080332
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_MAPS_API_KEY=AIzaSyChOXruBh6Fbads6EkpFydxVkhL_Pidghk
EOF
```

### Step 2: Install Python Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip
python -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt
```

### Step 3: Authenticate with GCP
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project qwiklabs-gcp-01-bd458d080332
```

### Step 4: Run Locally

#### Option A: Run CLI Agent Mode
```bash
agents-cli run "Find 2 bedroom apartments in Central Austin"
```

#### Option B: Run ADK Web Playground
```bash
uv run adk web --port 8080 --allow_origins "*"
# Open http://localhost:8080
```

#### Option C: Run FastAPI Web Proxy & Custom Chat UI
```bash
uv run python frontend/main.py
# Open http://localhost:8080
```

### Step 5: Redeploy to Agent Platform
```bash
agents-cli deploy --no-confirm-project
```
