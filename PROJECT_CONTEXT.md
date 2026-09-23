# HavenScout - Complete Re-Creation & Resumption Guide (From Scratch)

This document provides a complete, step-by-step guide to rebuild, reconfigure, deploy, and run **HavenScout** from total zero in a brand-new Google Cloud Platform (GCP) project, clean Virtual Machine (VM), or fresh developer workspace.

---

## 📋 Table of Contents
1. [Overview & Capabilities](#-overview--capabilities)
2. [Phase 1: Environment & New GCP Project Setup](#phase-1-environment--new-gcp-project-setup)
3. [Phase 2: Codebase Configuration](#phase-2-codebase-configuration)
4. [Phase 3: Deploying Agent to Agent Platform](#phase-3-deploying-agent-to-agent-platform)
5. [Phase 4: Setting Service Account IAM Permissions](#phase-4-setting-service-account-iam-permissions)
6. [Phase 5: Running Local Web UI & Testing](#phase-5-running-local-web-ui--testing)
7. [Architecture Reference & Code Quirks](#architecture-reference--code-quirks)

---

## 📌 Overview & Capabilities

- **Framework**: Built with **Google Agent Development Kit (ADK)** and deployed on **Vertex AI Agent Runtime**.
- **Features**:
  - **Firestore DB**: Search properties, schedule viewings, record new listings, compute move-in costs & rent affordability ratios.
  - **Google Maps REST APIs**: Geocoding API (address -> lat/long) and Places API New (nearby venues & points of interest).
  - **Gemini Image Generation**: Generates interior decor images using `gemini-3.1-flash-lite-image`, uploads to a public Cloud Storage bucket, and registers ADK session artifacts.
  - **Rich A2UI Cards**: Emits native A2UI v0.8 cards (`Card`, `Column`, `Row`, `Text`, `Image`) rendered in the chat UI.
  - **Sandbox Code Execution**: Runs Python code safely in a managed Agent Engine sandbox using `CustomCodeExecutor`.
  - **FastAPI A2A Proxy & Web UI**: Includes a FastAPI proxy in `./frontend` talking to the deployed agent over the **A2A protocol**.

---

## Phase 1: Environment & New GCP Project Setup

### 1.1 Clone Repository & Install Dependencies
```bash
git clone https://github.com/tmasabari/buildwithgemini-havenscout.git
cd buildwithgemini-havenscout

# Create virtual environment and install packages using uv (recommended)
uv sync

# Or using standard python/pip:
python3 -m venv .venv
source .venv/bin/activate
pip install -r frontend/requirements.txt
```

### 1.2 Authenticate & Select GCP Project
```bash
gcloud auth login
gcloud auth application-default login

# Set your active GCP project ID
export PROJECT_ID="<YOUR_NEW_PROJECT_ID>"
gcloud config set project $PROJECT_ID
```

### 1.3 Enable Required Google Cloud APIs
```bash
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  geocoding-backend.googleapis.com \
  places-backend.googleapis.com
```

### 1.4 Provision Firestore Database & Public GCS Bucket
```bash
# Create Firestore Native Database in us-east1
gcloud firestore databases create --location=us-east1 --type=firestore-native

# Create Public GCS Bucket for Generated Images
export BUCKET_NAME="havenscout-media-${PROJECT_ID}"
gcloud storage buckets create "gs://${BUCKET_NAME}" --location=us-east1
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="allUsers" \
  --role="roles/storage.objectViewer"
```

### 1.5 Obtain Google Maps API Key
1. Go to **Google Cloud Console -> APIs & Services -> Credentials**.
2. Create an API Key and ensure **Geocoding API** and **Places API (New)** are enabled for it.

---

## Phase 2: Codebase Configuration

### 2.1 Create Local `.env` File
Create a `.env` file in the project root (`./.env`):

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=<YOUR_NEW_PROJECT_ID>
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_MAPS_API_KEY=<YOUR_NEW_GOOGLE_MAPS_API_KEY>
```

### 2.2 Update Hardcoded Project & Bucket Names in Source Code
Update lines 15-16 in [`app/tools/firestore_tools.py`](file:///config/Desktop/Session1/havenscout/app/tools/firestore_tools.py):

```python
PROJECT_ID = "<YOUR_NEW_PROJECT_ID>"
BUCKET_NAME = "havenscout-media-<YOUR_NEW_PROJECT_ID>"
```

---

## Phase 3: Deploying Agent to Agent Platform

### 3.1 Initial Deployment Command
Deploy your agent to Vertex AI Agent Runtime:

```bash
agents-cli deploy --no-confirm-project
```

Once deployment finishes, copy the generated **Reasoning Engine Resource Name**:
`projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>`

### 3.2 Update Reasoning Engine Resource IDs in Code
Update the `agent_engine_resource_name` string in:

1. **[`app/agent.py`](file:///config/Desktop/Session1/havenscout/app/agent.py)**:
   ```python
   code_executor = CustomCodeExecutor(
       agent_engine_resource_name="projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>"
   )
   ```

2. **[`frontend/main.py`](file:///config/Desktop/Session1/havenscout/frontend/main.py)**:
   ```python
   RESOURCE = os.environ.get(
       "AGENT_ENGINE_RESOURCE_NAME",
       "projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>",
   )
   ```

3. **[`deployment_metadata.json`](file:///config/Desktop/Session1/havenscout/deployment_metadata.json)**:
   Update `"remote_agent_runtime_id"`.

---

## Phase 4: Setting Service Account IAM Permissions

Your deployed agent runs under an Agent Runtime service account (`service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`). Grant it the required permissions:

```bash
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# Grant Firestore Database User permission
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/datastore.user"

# Grant Storage Object Admin permission on the media bucket
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:$SA" \
  --role="roles/storage.objectAdmin"
```

---

## Phase 5: Running Local Web UI & Testing

### 5.1 Run Local CLI Query Test
```bash
agents-cli run "Find 2 bedroom apartments in Central Austin"
```

### 5.2 Run ADK Web Playground
```bash
uv run adk web --port 8080 --allow_origins "*"
# Access at http://localhost:8080
```

### 5.3 Run FastAPI Proxy & Chat Web UI
```bash
uv run python frontend/main.py
# Access at http://localhost:8080
```

---

## Architecture Reference & Code Quirks

1. **Cloudpickle Serialization Fix (`CustomCodeExecutor`)**:
   ADK's `AgentEngineSandboxCodeExecutor` contains `threading.Lock()` which breaks `cloudpickle` during `agents-cli deploy`. In [`app/agent.py`](file:///config/Desktop/Session1/havenscout/app/agent.py), `CustomCodeExecutor` handles state serialization cleanly:
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

2. **Vertex AI Model Naming**:
   Use `gemini-2.5-flash` for agent reasoning in `us-east1` (do not use `gemini-flash-latest` which returns 404 in Vertex AI).

3. **A2UI v0.8 & Image Sanitization**:
   [`app/a2ui_utils.py`](file:///config/Desktop/Session1/havenscout/app/a2ui_utils.py) converts `<Image>` components with relative or non-HTTP URLs into text notes so cards render cleanly without broken image icons.
