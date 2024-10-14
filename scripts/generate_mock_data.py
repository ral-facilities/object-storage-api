import logging
from typing import Any

import requests
from faker import Faker

fake = Faker("en_GB")

API_URL = "http://localhost:8002"
IMS_API_URL = "http://localhost:8000"
MAX_NUMBER_ATTACHMENTS_PER_ENTITY = 3
PROBABILITY_ENTITY_HAS_ATTACHMENTS = 0.2
PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD = 0.5
SEED = 0

logging.basicConfig(level=logging.INFO)


def optional_attachment_field(function):
    return function() if fake.random.random() < PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD else None


def generate_random_attachment(entity_id: str):
    return {
        "entity_id": entity_id,
        "file_name": fake.file_name(),
        "title": optional_attachment_field(lambda: fake.paragraph(nb_sentences=1)),
        "description": optional_attachment_field(lambda: fake.paragraph(nb_sentences=2)),
    }


def post(endpoint: str, json: dict) -> dict[str, Any]:
    """Posts an entity's data to the given endpoint

    :return: JSON data from the response.
    """
    return requests.post(f"{API_URL}{endpoint}", json=json, timeout=10).json()


def create_attachment(attachment_data: dict) -> dict[str, Any]:
    attachment = post("/attachments", attachment_data)
    upload_info = attachment["upload_info"]
    requests.post(
        upload_info["url"].replace("minio", "localhost"),
        files={"file": fake.paragraph(nb_sentences=2)},
        data=upload_info["fields"],
        timeout=5,
    )

    return attachment


def populate_attachments_for_entity(entity_id: str):
    if fake.random.random() < PROBABILITY_ENTITY_HAS_ATTACHMENTS:
        for _ in range(0, fake.random.randint(0, MAX_NUMBER_ATTACHMENTS_PER_ENTITY)):
            attachment = generate_random_attachment(entity_id)
            create_attachment(attachment)


def populate_attachments():
    logging.info("Generating attachments for catalogue items...")

    catalogue_items = requests.get(f"{IMS_API_URL}/v1/catalogue-items", timeout=10).json()
    for catalogue_item in catalogue_items:
        populate_attachments_for_entity(catalogue_item["id"])

    logging.info("Generating attachments for items...")
    items = requests.get(f"{IMS_API_URL}/v1/items", timeout=10).json()
    for item in items:
        populate_attachments_for_entity(item["id"])

    logging.info("Generating attachments for systems...")
    systems = requests.get(f"{IMS_API_URL}/v1/systems", timeout=10).json()
    for system in systems:
        populate_attachments_for_entity(system["id"])


def generate_mock_data():
    logging.info("Populating attachments...")
    populate_attachments()
