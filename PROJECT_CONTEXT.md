# 🏡 HavenScout — Restoration & Bootstrap Guide (New GCP Account & Environment)

This document provides complete, step-by-step instructions to restore, reconfigure, deploy, and run **HavenScout** from total zero in a **brand-new Google Cloud Platform (GCP) account**, clean Virtual Machine (VM), or new developer environment.

---

## 📋 Table of Contents
1. [System Architecture & Capabilities](#-system-architecture--capabilities)
2. [Phase 1: Environment & New GCP Account Setup](#phase-1-environment--new-gcp-account-setup)
3. [Phase 2: Codebase & Environment Configuration](#phase-2-codebase--environment-configuration)
4. [Phase 3: Agent Deployment & Resource Binding](#phase-3-agent-deployment--resource-binding)
5. [Phase 4: Service Account IAM Permissions](#phase-4-service-account-iam-permissions)
6. [Phase 5: Cloud Run Frontend Deployment (Optional)](#phase-5-cloud-run-frontend-deployment-optional)
7. [Phase 6: Verification & Testing](#phase-6-verification--testing)
8. [Key Architecture Notes & Troubleshooting](#key-architecture-notes--troubleshooting)

---

## 📌 System Architecture & Capabilities

HavenScout is built using the **Google Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Runtime**.

### Integrated Tools & Google Cloud Services:
- **Google Cloud Firestore**: Rental listing database lookups (`search_listings`), listing registration (`add_listing`), tour scheduling (`schedule_tour`), and ZIP code neighborhood details (`get_zipcode_neighborhood_info`).
- **Google Cloud Storage**: Public bucket (`havenscout-media-<PROJECT_ID>`) hosting generated property images and video tour MP4 files.
- **Google Maps APIs**: Nearby point-of-interest search (`find_nearby_places`) using Places API (New) and address geocoding (`geocode_address`).
- **Vertex AI Image Generation**: Generates realistic property and decor imagery using `gemini-3.1-flash-lite-image`.
- **Vertex AI Video Generation**: Generates short property tour videos using Google's Omni model (`gemini-omni-flash-preview`) in the `global` region and saves artifacts via ADK `ToolContext`.
- **Financial Tools & Sandbox Code Execution**: Move-in upfront cost estimator (`calculate_move_in_costs`), security deposit compound interest calculator (`calculate_compound_interest`), and managed Python code execution (`execute_python_code`).
- **Structured A2UI Cards (v0.8)**: Emits native A2UI Basic Catalog components (`Card`, `Column`, `Row`, `Text`, `Image`) rendered cleanly in the chat interface.
- **Agent Platform Memory Bank**: Automatically persists user preferences, budget limits, and pet rules across sessions via `PreloadMemoryTool` and `generate_memories_callback`.

---

## Phase 1: Environment & New GCP Account Setup

### 1.1 Prerequisites Installation
Install Python 3.11+, `uv`, and `google-agents-cli` on the workstation:

```bash
# Install uv (Fast Python package manager)
curl -sSf https://astral.sh/uv/install.sh | sh

# Install Agents CLI
uv tool install google-agents-cli
```

### 1.2 Authenticate with New Google Account
Login to gcloud with your **new Google Account**:

```bash
gcloud auth login
gcloud auth application-default login
```

### 1.3 Create or Select New GCP Project
```bash
export PROJECT_ID="<YOUR_NEW_PROJECT_ID>"

# Set default project in gcloud
gcloud config set project $PROJECT_ID
```

### 1.4 Enable Required Google Cloud APIs
Enable all mandatory services for Agent Runtime, Firestore, Cloud Storage, and Google Maps:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  geocoding-backend.googleapis.com \
  places-backend.googleapis.com \
  run.googleapis.com
```

### 1.5 Provision Cloud Resources

#### A. Provision Cloud Firestore (Native Mode)
Create a Firestore Native database in region `us-east1`:
```bash
gcloud firestore databases create --location=us-east1 --type=firestore-native
```

#### B. Provision Public Media Bucket
Create a public Cloud Storage bucket for generated property images and videos:
```bash
export BUCKET_NAME="havenscout-media-${PROJECT_ID}"
gcloud storage buckets create "gs://${BUCKET_NAME}" --location=us-east1

# Allow public read access to media objects
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="allUsers" \
  --role="roles/storage.objectViewer"
```

### 1.6 Google Maps API Key Setup
1. Go to **Google Cloud Console -> APIs & Services -> Credentials**.
2. Create an API Key (`MAPS_API_KEY`).
3. Ensure **Geocoding API** and **Places API (New)** are enabled for this key.

---

## Phase 2: Codebase & Environment Configuration

### 2.1 Clone Repository & Install Virtual Environment
```bash
git clone https://github.com/tmasabari/buildwithgemini-havenscout.git
cd buildwithgemini-havenscout

# Sync virtual environment and dependencies
uv sync
```

### 2.2 Configure `.env` File
Create a `.env` file in the project root (`./.env`):

```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=<YOUR_NEW_PROJECT_ID>
GOOGLE_CLOUD_LOCATION=us-east1
GOOGLE_MAPS_API_KEY=<YOUR_NEW_MAPS_API_KEY>
```

### 2.3 Update Project & Bucket Constants in Code
Update the `PROJECT_ID` and `BUCKET_NAME` variables in the following tool files:

1. **`app/tools/firestore_tools.py`**:
   ```python
   PROJECT_ID = "<YOUR_NEW_PROJECT_ID>"
   BUCKET_NAME = "havenscout-media-<YOUR_NEW_PROJECT_ID>"
   ```

2. **`app/tools/image_tools.py`**:
   ```python
   PROJECT_ID = "<YOUR_NEW_PROJECT_ID>"
   BUCKET_NAME = "havenscout-media-<YOUR_NEW_PROJECT_ID>"
   ```

---

## Phase 3: Agent Deployment & Resource Binding

### 3.1 Initial Deployment
Deploy the agent code to Vertex AI Agent Runtime:

```bash
agents-cli deploy --no-confirm-project --project $PROJECT_ID --region us-east1
```

Once deployment completes, note down the **Agent Engine Resource Name** from the CLI output:
`projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>`

### 3.2 Update Resource Name in Source Code
Update the `agent_engine_resource_name` string in the following files:

1. **`app/agent.py`**:
   ```python
   code_executor = CustomCodeExecutor(
       agent_engine_resource_name="projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>"
   )
   ```

2. **`frontend/main.py`**:
   ```python
   RESOURCE = os.environ.get(
       "AGENT_ENGINE_RESOURCE_NAME",
       "projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>",
   )
   ```

3. **`deployment_metadata.json`**:
   Update `"remote_agent_runtime_id": "projects/<PROJECT_NUMBER>/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>"`.

### 3.3 Redeploy Agent
Redeploy to apply the updated resource binding:

```bash
agents-cli deploy --no-confirm-project --project $PROJECT_ID --region us-east1
```

---

## Phase 4: Service Account IAM Permissions

The deployed agent runs under an Agent Runtime service account (`service-<PROJECT_NUMBER>@gcp-sa-aiplatform-re.iam.gserviceaccount.com`). Grant it mandatory access to Firestore and Cloud Storage:

```bash
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

# 1. Grant Firestore Database User permission
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/datastore.user"

# 2. Grant Storage Object Admin permission on media bucket
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:$SA" \
  --role="roles/storage.objectAdmin"
```

---

## Phase 5: Cloud Run Frontend Deployment (Optional)

To host the HavenScout plain web UI on Google Cloud Run:

```bash
# 1. Deploy Cloud Run service
gcloud run deploy havenscout-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/${PROJECT_NUMBER}/locations/us-east1/reasoningEngines/<REASONING_ENGINE_ID>",AGENT_DIRECTORY="app"

# 2. Grant Cloud Run default Service Account permission to call Agent Engine
export RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$RUN_SA" \
  --role="roles/aiplatform.user"
```

---

## Phase 6: Verification & Testing

### 6.1 Run Automated Tests
Run unit and integration test suites:
```bash
uv run pytest tests/unit tests/integration
```

### 6.2 Test Agent via Playground
Launch the interactive local playground:
```bash
agents-cli playground
```

### 6.3 Test Web UI Locally
Launch the FastAPI A2A proxy server locally:
```bash
uv run python frontend/main.py
```
*(Server starts on port 8080).*

---

## Key Architecture Notes & Troubleshooting

1. **Cloudpickle Serialization Fix (`CustomCodeExecutor`)**:
   ADK's `AgentEngineSandboxCodeExecutor` contains `threading.Lock()` which breaks `cloudpickle` during `agents-cli deploy`. In `app/agent.py`, `CustomCodeExecutor` overrides `__getstate__` and `__setstate__` to serialize cleanly.
2. **Vertex AI Model Locations**:
   - `gemini-2.5-flash`: Main reasoning model in location `us-east1`.
   - `gemini-3.1-flash-lite-image`: Image generation model in location `global`.
   - `gemini-omni-flash-preview`: Video generation model in location `global`.
3. **A2UI v0.8 Handling**:
   `app/a2ui_utils.py` converts `<Image>` components with relative or non-HTTP URLs into clean text notes to prevent broken UI cards.
