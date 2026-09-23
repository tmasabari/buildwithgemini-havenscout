# Copyright 2026 Google LLC
"""Google Maps REST API tools for Geocoding and Places (New) APIs."""

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def geocode_address(address: str) -> dict[str, Any]:
    """Convert a human-readable street address or location name into geographic coordinates using Google Maps Geocoding API.

    Args:
        address: Full address or location name (e.g. "100 Congress Ave, Austin, TX").

    Returns:
        Dictionary containing key fields: name, address, and location (latitude/longitude).
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    req = urllib.request.Request(url, headers={"User-Agent": "HavenScout/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("results", [])
            if not results:
                return {"error": f"No geocoding results found for address: {address}"}

            first = results[0]
            loc = first.get("geometry", {}).get("location", {})
            return {
                "name": address,
                "address": first.get("formatted_address"),
                "location": {
                    "latitude": loc.get("lat"),
                    "longitude": loc.get("lng"),
                },
            }
    except Exception as e:
        return {"error": f"Geocoding API request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "restaurant",
    radius_meters: int = 1500,
) -> list[dict[str, Any]]:
    """Find nearby points of interest (restaurants, supermarkets, parks, schools, etc.) using Google Places API (New).

    Args:
        latitude: Center latitude coordinate (e.g. 30.26397).
        longitude: Center longitude coordinate (e.g. -97.74482).
        place_type: Type of place to search for (e.g. "restaurant", "supermarket", "park", "coffee_shop", "school").
        radius_meters: Search radius in meters (default 1500 meters / ~0.9 miles).

    Returns:
        List of nearby place dictionaries containing key fields: name, address, and location.
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return [{"error": "GOOGLE_MAPS_API_KEY environment variable is not configured."}]

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "includedTypes": [place_type.lower().strip()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            places_raw = data.get("places", [])
            results = []
            for item in places_raw:
                display_name = item.get("displayName", {}).get("text", "Unknown Place")
                formatted_address = item.get("formattedAddress", "")
                loc = item.get("location", {})
                results.append({
                    "name": display_name,
                    "address": formatted_address,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                })
            return results
    except Exception as e:
        return [{"error": f"Places API (New) request failed: {str(e)}"}]
