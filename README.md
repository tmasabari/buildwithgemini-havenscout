# 🏡 HavenScout — AI Real Estate & Apartment Discovery Assistant

HavenScout is an intelligent real estate and apartment discovery assistant built with the **Google Agent Development Kit (ADK)**. It combines rich A2UI interactive UI cards, Firestore database lookups, Google Maps Places API, financial modeling tools, Vertex AI image/video generation, and long-term Memory Bank personalization.

![HavenScout Demo](demo.gif)

---

## ✨ Features & Architecture

HavenScout is powered by `gemini-2.5-flash` and implements the following capabilities wired directly in `app/`:

### 🏢 Apartment Discovery & Firestore Database
- **Property Search (`search_listings`)**: Queries rental property listings from Google Cloud Firestore database by city/neighborhood, max rent price, bedroom count, and pet policy.
- **Listing Management (`add_listing`)**: Registers new apartment listings into the Firestore database.
- **Tour Scheduling (`schedule_tour`)**: Books property viewings and tour dates for users.
- **ZIP Code Lookup (`get_zipcode_neighborhood_info`)**: Fetches neighborhood details for specific postal codes.

### 🎨 Generative Media (Vertex AI & Cloud Storage)
- **Property Image Generation (`generate_property_image` / `generate_interior_decor_image`)**: Generates realistic interior decor and architectural images using `gemini-3.1-flash-lite-image`.
- **Property Video Tour Generation (`generate_property_video`)**: Generates short property tour videos using Google's Omni model (`gemini-omni-flash-preview`) in the `global` location.
- **Cloud Storage Integration**: Video bytes are saved as ADK session artifacts via `ToolContext` and uploaded directly to public Google Cloud Storage (`havenscout-media-*`).

### 🗺️ Google Maps Location Services
- **Nearby Points of Interest (`find_nearby_places`)**: Finds coffee shops, parks, transit stops, and schools near target addresses using Google Maps Places API.
- **Geocoding (`geocode_address`)**: Converts street addresses to precise latitude/longitude coordinates.

### 💰 Financial Calculations & Code Execution
- **Move-In Cost Estimator (`calculate_move_in_costs`)**: Calculates total upfront move-in expenses (first month rent, security deposit, pet fees) and evaluates rent-to-income affordability.
- **Deposit Interest Calculator (`calculate_compound_interest`)**: Computes compound interest yields on security deposits or investments over multi-year periods.
- **Sandbox Code Execution (`execute_python_code`)**: Executes custom Python code using `AgentEngineSandboxCodeExecutor` on Vertex AI Agent Runtime.

### 📱 Rich Interactive UI (A2UI v0.8)
- **A2UI Basic Catalog**: Automatically structures apartment search results and property listings into clean, flat UI components (`Card`, `Column`, `Row`, `Text`, `Image`).

### 🧠 Long-Term Personalization (Memory Bank)
- **Memory Persistence (`PreloadMemoryTool` & `generate_memories_callback`)**: Automatically extracts and retains user preferences (budget limits, preferred neighborhoods, pet requirements) into Agent Platform Memory Bank across sessions.

---

## 🛠️ Project Structure

```
.
├── app/
│   ├── agent.py                 # Core ADK root agent configuration & tool wiring
│   ├── a2ui_utils.py            # A2UI response formatting & callbacks
│   ├── fast_api_app.py          # FastAPI application wrapper for ADK
│   └── tools/
│       ├── firestore_tools.py   # Firestore database operations & math tools
│       ├── google_maps_tools.py # Google Maps Places & Geocoding tools
│       └── image_tools.py       # Vertex AI Image & Video generation tools
├── frontend/
│   ├── main.py                  # FastAPI A2A proxy server
│   └── static/index.html        # Custom HavenScout web UI
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration & agent streaming tests
├── agents-cli-manifest.yaml    # Agents CLI project configuration
├── PROJECT_CONTEXT.md          # Complete project restoration & setup guide
└── pyproject.toml              # Project dependencies & Python setup
```

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.11+
- `uv` package manager (`uv tool install google-agents-cli` or `pip install uv`)
- Google Cloud SDK (`gcloud auth application-default login`)

### 2. Installation
Install project dependencies using `uv`:
```bash
uv sync
```

### 3. Running Tests
Execute unit and integration tests:
```bash
uv run pytest tests/unit tests/integration
```

### 4. Running Local Interactive Playground
Start the interactive local ADK agent playground:
```bash
agents-cli playground
```

### 5. Running the Web Frontend Locally
To launch the HavenScout web UI proxy locally, run:
```bash
uv run python frontend/main.py
```
*(The server will start on port 8080 by default).*

---

## 🔄 Restoring to a New GCP Account & Environment

For complete, step-by-step instructions on bootstrapping HavenScout from scratch in a **brand-new Google Cloud Account**, provisioning Firestore, creating public Cloud Storage buckets, setting IAM permissions, and binding Agent Engine resources, refer to:

👉 **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)**

---

## 📜 License
Copyright 2026 Google LLC. Licensed under the Apache License, Version 2.0.
