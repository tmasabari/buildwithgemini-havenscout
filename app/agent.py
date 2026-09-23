# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

# Ensure Vertex AI mode is explicitly enabled for Gemini LLM calls
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-01-bd458d080332")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-east1")

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types


from app.a2ui_utils import a2ui_callback
from app.tools.firestore_tools import (
    add_listing,
    calculate_move_in_costs,
    generate_interior_decor_image,
    get_zipcode_neighborhood_info,
    schedule_tour,
    search_listings,
)
from app.tools.google_maps_tools import find_nearby_places, geocode_address
from app.tools.image_tools import generate_property_image

# 1. Build A2UI System Prompt (v0.8 with Basic Catalog)
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are HavenScout, an intelligent real estate and apartment recommendation assistant. "
        "You remember the user's stated preferences, budget, preferred neighborhoods, pet requirements, "
        "and facts from previous conversations to personalize your apartment search and recommendations. "
        "Use search_listings to find apartments, add_listing to add new listings, schedule_tour to book property viewings, "
        "calculate_move_in_costs to compute total upfront move-in expenses and rent-to-income affordability, "
        "generate_interior_decor_image or generate_property_image to create realistic property and decor images using gemini-3.1-flash-lite-image, "
        "get_zipcode_neighborhood_info to fetch ZIP code info, geocode_address to convert addresses to coordinates, "
        "and find_nearby_places to search points of interest."
    ),
    workflow_description="Analyze the request, search listings, calculate costs, generate images, or fetch location details, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to store session memories into Memory Bank."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


# 2. Configure Agent Platform Sandbox Code Execution with cloudpickle support
import threading

class CustomCodeExecutor(AgentEngineSandboxCodeExecutor):
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_agent_engine_creation_lock"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._agent_engine_creation_lock = threading.Lock()


code_executor = CustomCodeExecutor(
    agent_engine_resource_name="projects/641471327587/locations/us-east1/reasoningEngines/5340611650107998208"
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_listings,
        add_listing,
        schedule_tour,
        calculate_move_in_costs,
        generate_interior_decor_image,
        generate_property_image,
        get_zipcode_neighborhood_info,
        geocode_address,
        find_nearby_places,
        get_weather,
        get_current_time,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
