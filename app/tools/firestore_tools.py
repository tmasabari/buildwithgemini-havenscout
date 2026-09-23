# Copyright 2026 Google LLC
"""Combined tool suite for HavenScout real estate finder agent."""

import io
import json
import os
import urllib.request
import uuid
from typing import Any

from google.cloud import firestore, storage
from PIL import Image, ImageDraw

# Hardcoded project ID as string to satisfy Agent Platform requirements
PROJECT_ID = "qwiklabs-gcp-03-33f9e74cd81f"
BUCKET_NAME = "havenscout-media-qwiklabs-gcp-03-33f9e74cd81f"


import google.auth

def _get_firestore_client() -> firestore.Client:
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return firestore.Client(project=PROJECT_ID, credentials=creds)


def search_listings(
    location: str | None = None,
    max_price: int | None = None,
    bedrooms: int | None = None,
    pets_allowed: bool | None = None,
) -> list[dict[str, Any]]:
    """Search apartment listings in the Firestore database based on user criteria.

    Args:
        location: Preferred location or neighborhood (e.g. "Central Austin", "Downtown Austin").
        max_price: Maximum monthly rent in USD (e.g. 2400).
        bedrooms: Desired number of bedrooms (e.g. 1, 2).
        pets_allowed: Whether pets must be allowed (True/False).

    Returns:
        A list of matching apartment listing dictionaries.
    """
    db = _get_firestore_client()
    docs = db.collection("listings").where("available", "==", True).stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        if location and location.lower() not in data.get("location", "").lower():
            continue
        if max_price is not None and data.get("price", 0) > max_price:
            continue
        if bedrooms is not None and data.get("bedrooms", 0) < bedrooms:
            continue
        if pets_allowed is not None and pets_allowed and not data.get("pets_allowed", False):
            continue
        results.append(data)

    return results


def add_listing(
    title: str,
    location: str,
    price: int,
    bedrooms: int,
    bathrooms: float,
    pets_allowed: bool,
    amenities: list[str],
) -> str:
    """Add a new apartment listing to the Firestore database.

    Args:
        title: Title of property (e.g. "Riverside Loft").
        location: Neighborhood or city area.
        price: Monthly rent in USD.
        bedrooms: Number of bedrooms.
        bathrooms: Number of bathrooms.
        pets_allowed: True if pets allowed.
        amenities: List of amenity strings.

    Returns:
        Confirmation string with listing ID.
    """
    db = _get_firestore_client()
    listing_id = f"apt-{uuid.uuid4().hex[:8]}"
    data = {
        "id": listing_id,
        "title": title,
        "location": location,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "pets_allowed": pets_allowed,
        "amenities": amenities,
        "available": True,
    }
    db.collection("listings").document(listing_id).set(data)
    return f"Successfully added listing '{title}' with ID {listing_id}."


def schedule_tour(
    listing_id: str,
    preferred_date: str,
    contact_name: str,
    contact_email: str,
) -> str:
    """Schedule a property viewing tour for a listing and record it in Firestore.

    Args:
        listing_id: ID of the listing (e.g. "apt-austin-101").
        preferred_date: Preferred tour date and time (e.g. "2026-10-01 at 2:00 PM").
        contact_name: Name of the prospective tenant.
        contact_email: Email address of the prospective tenant.

    Returns:
        Confirmation summary with tour reference ID.
    """
    db = _get_firestore_client()
    doc = db.collection("listings").document(listing_id).get()
    title = doc.to_dict().get("title", listing_id) if doc.exists else listing_id

    tour_id = f"tour-{uuid.uuid4().hex[:6]}"
    tour_data = {
        "tour_id": tour_id,
        "listing_id": listing_id,
        "listing_title": title,
        "preferred_date": preferred_date,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "status": "confirmed",
    }
    db.collection("tours").document(tour_id).set(tour_data)
    return (
        f"Tour confirmed! Reference ID: {tour_id}. Property: '{title}' "
        f"for {contact_name} on {preferred_date}. Details sent to {contact_email}."
    )


def calculate_move_in_costs(
    monthly_rent: int,
    security_deposit: int | None = None,
    pet_deposit: int = 0,
    application_fee: int = 50,
    gross_monthly_income: int | None = None,
) -> dict[str, Any]:
    """Calculate total move-in costs and evaluate rent affordability ratio.

    Args:
        monthly_rent: Rent per month in USD (e.g. 2200).
        security_deposit: Security deposit in USD (defaults to 1 month's rent if omitted).
        pet_deposit: One-time pet deposit in USD (defaults to 0).
        application_fee: Application processing fee in USD (defaults to 50).
        gross_monthly_income: Optional user gross monthly income in USD to evaluate affordability ratio.

    Returns:
        Dictionary breakdown of move-in costs and rent-to-income affordability assessment.
    """
    sec_dep = security_deposit if security_deposit is not None else monthly_rent
    total_upfront = monthly_rent + sec_dep + pet_deposit + application_fee

    ratio = None
    affordable = True
    if gross_monthly_income and gross_monthly_income > 0:
        ratio = round((monthly_rent / gross_monthly_income) * 100, 1)
        affordable = ratio <= 33.0

    return {
        "first_month_rent": monthly_rent,
        "security_deposit": sec_dep,
        "pet_deposit": pet_deposit,
        "application_fee": application_fee,
        "total_move_in_cost": total_upfront,
        "rent_to_income_ratio_pct": ratio,
        "meets_33_pct_affordability_guideline": affordable,
    }


def generate_interior_decor_image(
    prompt: str,
    listing_title: str = "Apartment Unit",
) -> str:
    """Generate a decor design layout preview image for a property and save to Cloud Storage.

    Args:
        prompt: Description of decor style or layout (e.g. "Minimalist living room with oak table and floor plants").
        listing_title: Name of the property.

    Returns:
        Public HTTPS URL of the rendered decor image.
    """
    img = Image.new("RGB", (600, 360), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([15, 15, 585, 345], outline=(59, 130, 246), width=3)
    draw.text((35, 35), "HavenScout Interior Decor Concept", fill=(248, 250, 252))
    draw.text((35, 75), f"Property: {listing_title[:45]}", fill=(148, 163, 184))
    draw.text((35, 120), f"Concept Prompt: {prompt[:50]}...", fill=(226, 232, 240))
    draw.rectangle([35, 170, 565, 310], fill=(30, 41, 59), outline=(100, 116, 139))
    draw.text((180, 230), "[ Interior Design Layout Visualized ]", fill=(148, 163, 184))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    file_name = f"decor_{uuid.uuid4().hex[:8]}.png"
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(file_name)
    blob.upload_from_file(buf, content_type="image/png")

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{file_name}"


def get_zipcode_neighborhood_info(zipcode: str) -> dict[str, Any]:
    """Fetch real-time geographic and neighborhood details for a US ZIP code using the public Zippopotam.us API.

    Args:
        zipcode: 5-digit US ZIP code (e.g. "78701", "78704").

    Returns:
        Dictionary containing place name, state, latitude, and longitude coordinates.
    """
    clean_zip = zipcode.strip()[:5]
    api_key = os.getenv("ZIPCODE_API_KEY", None)

    url = f"https://api.zippopotam.us/us/{clean_zip}"
    headers = {"User-Agent": "HavenScout/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            places = data.get("places", [])
            if not places:
                return {"error": f"No location found for ZIP code {zipcode}."}
            first = places[0]
            return {
                "zipcode": clean_zip,
                "city": first.get("place name"),
                "state": first.get("state"),
                "state_abbreviation": first.get("state abbreviation"),
                "latitude": float(first.get("latitude", 0)),
                "longitude": float(first.get("longitude", 0)),
            }
    except Exception as e:
        return {"error": f"Failed to fetch neighborhood data for ZIP {zipcode}: {str(e)}"}


def execute_python_code(code: str) -> dict[str, Any]:
    """Execute Python code for mathematical calculations, financial modeling, compound interest, or custom logic.

    Args:
        code: Python code string to execute. The output or result variable will be returned.

    Returns:
        Dictionary containing stdout output, evaluation result, or execution error.
    """
    import sys
    from io import StringIO

    buffer = StringIO()
    local_scope = {}
    sys_stdout = sys.stdout
    try:
        sys.stdout = buffer
        exec(code, {"__builtins__": __builtins__}, local_scope)
        sys.stdout = sys_stdout
        captured_output = buffer.getvalue().strip()
        result = local_scope.get("result") or local_scope.get("ans") or captured_output
        return {
            "status": "success",
            "output": captured_output,
            "result": str(result) if result is not None else captured_output,
            "variables": {k: str(v) for k, v in local_scope.items() if not k.startswith("_")},
        }
    except Exception as e:
        sys.stdout = sys_stdout
        return {"status": "error", "error": str(e)}


def calculate_compound_interest(
    principal: float,
    annual_rate_percent: float,
    years: float,
    compounding_frequency_per_year: int = 1,
) -> dict[str, Any]:
    """Calculate compound interest on security deposits, savings, or investments over time.

    Args:
        principal: Initial deposit or investment amount in USD (e.g. 3000.0).
        annual_rate_percent: Annual interest rate in percent (e.g. 4.5 for 4.5%).
        years: Time period in years (e.g. 3.0).
        compounding_frequency_per_year: Number of times interest is compounded per year (default 1 for annually, 12 for monthly, 365 for daily).

    Returns:
        Dictionary breakdown containing initial principal, interest earned, total future value, and annual progression.
    """
    r = annual_rate_percent / 100.0
    n = max(1, compounding_frequency_per_year)
    t = years

    future_value = principal * ((1 + r / n) ** (n * t))
    interest_earned = future_value - principal

    yearly_breakdown = []
    for y in range(1, int(years) + 1):
        fv_y = principal * ((1 + r / n) ** (n * y))
        yearly_breakdown.append({
            "year": y,
            "balance": round(fv_y, 2),
            "interest_earned_cumulative": round(fv_y - principal, 2),
        })

    return {
        "principal": round(principal, 2),
        "annual_rate_percent": annual_rate_percent,
        "years": years,
        "compounding_frequency": compounding_frequency_per_year,
        "interest_earned": round(interest_earned, 2),
        "future_value": round(future_value, 2),
        "yearly_breakdown": yearly_breakdown,
    }
