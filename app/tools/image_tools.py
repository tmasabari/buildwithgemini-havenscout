# Copyright 2026 Google LLC
"""Image generation tools for HavenScout real estate finder agent using Gemini image models."""

import uuid

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded project ID and public Cloud Storage bucket name
PROJECT_ID = "qwiklabs-gcp-01-bd458d080332"
BUCKET_NAME = "havenscout-media-qwiklabs-gcp-01-bd458d080332"


def generate_property_image(prompt: str, tool_context: ToolContext) -> str:
    """Generate a realistic property, floor plan, or interior decor image using gemini-3.1-flash-lite-image model in global region.

    Saves the generated image as a session artifact for the Playground's Artifacts panel,
    and uploads the image bytes to public Cloud Storage.

    Args:
        prompt: Detailed description of the apartment room, interior decor, or property (e.g. "A luxury modern living room with floor to ceiling windows in Austin TX").
        tool_context: ADK ToolContext to save the artifact to the session context.

    Returns:
        The public Cloud Storage HTTPS URL of the uploaded image (e.g. https://storage.googleapis.com/<bucket>/<object>).
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    candidate = response.candidates[0]
    part = candidate.content.parts[0]
    image_bytes = part.inline_data.data
    mime_type = part.inline_data.mime_type or "image/jpeg"

    ext = "png" if "png" in mime_type else "jpg"
    file_name = f"property_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact to Playground's Artifacts panel via tool_context
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=file_name, artifact=artifact_part)

    # 2. Upload image bytes to public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{file_name}"
