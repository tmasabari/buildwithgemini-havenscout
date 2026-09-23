# Copyright 2026 Google LLC
import logging
import google.auth
from google.cloud import firestore

# Hardcoded project ID as required for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-03-33f9e74cd81f"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_firestore_database():
    """Seed the Firestore database with sample HavenScout apartment listings."""
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    db = firestore.Client(project=PROJECT_ID, credentials=creds)
    collection_ref = db.collection("listings")

    sample_listings = [
        {
            "id": "apt-austin-101",
            "title": "The Austin Modern Lofts",
            "location": "Central Austin",
            "price": 2200,
            "bedrooms": 2,
            "bathrooms": 2.0,
            "square_feet": 950,
            "pets_allowed": True,
            "amenities": ["in-unit laundry", "balcony", "swimming pool", "covered parking"],
            "available": True,
        },
        {
            "id": "apt-austin-102",
            "title": "Downtown Urban Executive Suite",
            "location": "Downtown Austin",
            "price": 2450,
            "bedrooms": 2,
            "bathrooms": 2.0,
            "square_feet": 1100,
            "pets_allowed": False,
            "amenities": ["in-unit laundry", "gym", "rooftop deck", "concierge"],
            "available": True,
        },
        {
            "id": "apt-austin-103",
            "title": "SoCo Garden Apartments",
            "location": "South Congress",
            "price": 1950,
            "bedrooms": 1,
            "bathrooms": 1.0,
            "square_feet": 750,
            "pets_allowed": True,
            "amenities": ["dog park", "in-unit laundry", "private patio"],
            "available": True,
        },
        {
            "id": "apt-austin-104",
            "title": "Hyde Park Historic Duplex",
            "location": "Central Austin",
            "price": 2100,
            "bedrooms": 2,
            "bathrooms": 1.5,
            "square_feet": 900,
            "pets_allowed": True,
            "amenities": ["hardwood floors", "shared yard", "washer/dryer hookups"],
            "available": True,
        },
    ]

    for item in sample_listings:
        doc_ref = collection_ref.document(item["id"])
        doc_ref.set(item)
        logger.info(f"Seeded listing: {item['id']} - {item['title']}")

    print(f"Successfully seeded {len(sample_listings)} listings into Firestore project '{PROJECT_ID}'.")


if __name__ == "__main__":
    seed_firestore_database()
