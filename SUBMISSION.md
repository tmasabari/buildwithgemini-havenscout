# 🏆 HavenScout — Official Competition & Swag Submission Details

This document contains the official submission details for **HavenScout** for the **Build with Gemini / Google Cloud AI Hackathon**.

---

## 📌 Project Identification & Links

| Metadata Field | Value |
| :--- | :--- |
| **Project Name** | **HavenScout — AI Real Estate & Apartment Discovery Assistant** |
| **GitHub Repository** | [https://github.com/tmasabari/buildwithgemini-havenscout](https://github.com/tmasabari/buildwithgemini-havenscout) |
| **Deployed Web App URL** | [https://havenscout-frontend-538926441420.us-east1.run.app](https://havenscout-frontend-538926441420.us-east1.run.app) |
| **Reasoning Engine Resource Name** | `projects/538926441420/locations/us-east1/reasoningEngines/3569782202877083648` |
| **GCP Project ID** | `qwiklabs-gcp-03-33f9e74cd81f` |
| **Cloud Region** | `us-east1` (Agent Runtime & Cloud Run), `global` (Vertex AI Media Models) |
| **Framework** | Google Agent Development Kit (ADK) on Vertex AI Agent Runtime |

---

## 💡 Executive Summary

**HavenScout** is an intelligent, multi-tool real estate discovery assistant that redefines property searching. Built on top of the **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5 Flash**, HavenScout seamlessly integrates database queries, geospatial discovery, financial modeling, generative media, and personalized memory persistence into structured, interactive **A2UI cards**.

---

## ✨ Implemented Features & Technical Architecture

### 1. 🤖 Multi-Model Gemini Intelligence
- **Main Agent Reasoning (`gemini-2.5-flash`)**: Multi-turn planning, tool calling, and dialogue synthesis.
- **Interior Decor Image Generation (`gemini-3.1-flash-lite-image`)**: Realistic room decor and architectural imagery generation on Vertex AI.
- **Property Video Tour Generation (`gemini-omni-flash-preview`)**: Short property walkthrough video generation in location `global`.

### 2. 🗄️ Google Cloud Firestore Database
- **Listing Search (`search_listings`)**: Live query filtering by location, price, bedroom count, and pet rules.
- **Listing Management (`add_listing`)**: Dynamically inserts new rental listings into Cloud Firestore.
- **Tour Scheduling (`schedule_tour`)**: Registers viewing appointments for users.
- **ZIP Code Metadata (`get_zipcode_neighborhood_info`)**: Fetches neighborhood stats by postal code.

### 3. ☁️ Google Cloud Storage Bucket Integration
- Uploads generated image and video bytes directly to public Cloud Storage (`havenscout-media-qwiklabs-gcp-03-33f9e74cd81f`) and returns public HTTPS URLs.
- Registers artifacts into ADK session context via `ToolContext.save_artifact`.

### 4. 🗺️ Google Maps Geospatial Discovery
- **Nearby Places API (`find_nearby_places`)**: Locates coffee shops, parks, transit stops, and schools near properties.
- **Geocoding API (`geocode_address`)**: Converts addresses into latitude/longitude coordinates.

### 5. 🧮 Financial Calculators & Managed Sandbox Code Execution
- **Upfront Move-In Costs (`calculate_move_in_costs`)**: Calculates total move-in expenses and rent-to-income affordability ratios.
- **Security Deposit Yields (`calculate_compound_interest`)**: Computes multi-year compound interest on security deposits.
- **Sandbox Execution (`execute_python_code`)**: Runs custom Python calculations using `AgentEngineSandboxCodeExecutor`.

### 6. 📱 Structured A2UI (v0.8 Basic Catalog)
- Emits structured A2UI JSON array rendering flat UI components (`Card`, `Column`, `Row`, `Text`, `Image`).

### 7. 🧠 Agent Platform Memory Bank
- Retains user preferences (budget, pets, preferred neighborhoods) across chat turns via `PreloadMemoryTool` and `generate_memories_callback`.

---

## 🎬 Demo Assets
- **Inline Looping GIF**: [demo.gif](demo.gif) (embedded in `README.md`).
- **Demo Walkthrough Video**: [havenscout_demo_video.mp4](havenscout_demo_video.mp4) (mixed with upbeat lo-fi background music).

---

## 🧪 Verification & Test Suite
- **Unit & Integration Tests**: 100% passing test suite (`uv run pytest tests/unit tests/integration`).
