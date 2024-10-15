"""Module defining a script for populating the database and object store with randomised data."""

import logging
from typing import Any

import requests
from faker import Faker

fake = Faker("en_GB")

# Various constants determining the result of the script
API_URL = "http://localhost:8002"
IMS_API_URL = "http://localhost:8000"
MAX_NUMBER_ATTACHMENTS_PER_ENTITY = 3
MAX_NUMBER_IMAGES_PER_ENTITY = 3
PROBABILITY_ENTITY_HAS_ATTACHMENTS = 0.2
PROBABILITY_ENTITY_HAS_IMAGES = 0.2
PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD = 0.5
SEED = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def optional_attachment_field(function):
    """Either returns the result of executing the given function, or None while taking into account the fields
    probability to be populated."""

    return function() if fake.random.random() < PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD else None


def generate_random_attachment(entity_id: str):
    """Generates randomised data for an attachment with a given entity ID."""

    return {
        "entity_id": entity_id,
        "file_name": fake.file_name(),
        "title": optional_attachment_field(lambda: fake.paragraph(nb_sentences=1)),
        "description": optional_attachment_field(lambda: fake.paragraph(nb_sentences=2)),
    }


def generate_random_image_metadata(entity_id: str):
    """Generates randomised data for an image with a given entity ID."""

    return {
        "entity_id": entity_id,
        "title": optional_attachment_field(lambda: fake.paragraph(nb_sentences=1)),
        "description": optional_attachment_field(lambda: fake.paragraph(nb_sentences=2)),
    }


def post(endpoint: str, json: dict) -> dict[str, Any]:
    """Posts an entity's data to the given endpoint.

    :return: JSON data from the response.
    """
    return requests.post(f"{API_URL}{endpoint}", json=json, timeout=10).json()


def create_attachment(attachment_data: dict) -> dict[str, Any]:
    """Creates an attachment given its metadata and uploads some file data to it."""

    attachment = post("/attachments", attachment_data)
    upload_info = attachment["upload_info"]
    requests.post(
        upload_info["url"],
        files={"file": fake.paragraph(nb_sentences=2)},
        data=upload_info["fields"],
        timeout=5,
    )

    return attachment


def create_image(image_metadata: dict) -> dict[str, Any]:
    """Creates an image given its metadata and uploads some file data to it."""

    with open("test/files/image.jpg", mode="rb") as file:
        image = requests.post(
            f"{API_URL}/images",
            data=image_metadata,
            files={"upload_file": ("image.jpg", file, "image/jpeg")},
            timeout=5,
        ).json()

    return image


def populate_random_attachments(existing_entity_ids: list[str]):
    """Randomly populates attachments for the given list of entity IDs."""

    for entity_id in existing_entity_ids:
        if fake.random.random() < PROBABILITY_ENTITY_HAS_ATTACHMENTS:
            for _ in range(0, fake.random.randint(0, MAX_NUMBER_ATTACHMENTS_PER_ENTITY)):
                attachment = generate_random_attachment(entity_id)
                create_attachment(attachment)


def populate_random_images(existing_entity_ids: list[str]):
    """Randomly populates images for the given list of entity IDs."""

    for entity_id in existing_entity_ids:
        if fake.random.random() < PROBABILITY_ENTITY_HAS_IMAGES:
            for _ in range(0, fake.random.randint(0, MAX_NUMBER_IMAGES_PER_ENTITY)):
                image_metadata = generate_random_image_metadata(entity_id)
                create_image(image_metadata)


def obtain_existing_ims_entities() -> list[str]:
    """Obtains existing IMS entities to generate attachments/images for and adds them to a global variable for later
    use."""

    catalogue_items = requests.get(f"{IMS_API_URL}/v1/catalogue-items", timeout=10).json()
    existing_entity_ids = [entity["id"] for entity in catalogue_items]

    items = requests.get(f"{IMS_API_URL}/v1/items", timeout=10).json()
    existing_entity_ids.extend([entity["id"] for entity in items])

    systems = requests.get(f"{IMS_API_URL}/v1/systems", timeout=10).json()
    existing_entity_ids.extend([entity["id"] for entity in systems])

    return existing_entity_ids


def generate_mock_data():
    """Generates mock data for all the entities."""

    logger.info("Obtaining a list of existing IMS entities...")
    existing_entity_ids = obtain_existing_ims_entities()

    logger.info("Populating attachments...")
    populate_random_attachments(existing_entity_ids)

    logger.info("Populating images...")
    populate_random_images(existing_entity_ids)


if __name__ == "__main__":
    generate_mock_data()
