"""Module defining a script for populating the database and object store with randomised data."""

import logging
from typing import Any

import requests
from faker import Faker
from faker_file.providers.docx_file import DocxFileProvider
from faker_file.providers.image.pil_generator import PilImageGenerator
from faker_file.providers.jpeg_file import GraphicJpegFileProvider
from faker_file.providers.pdf_file import PdfFileProvider
from faker_file.providers.pdf_file.generators.reportlab_generator import ReportlabPdfGenerator
from faker_file.providers.png_file import GraphicPngFileProvider
from faker_file.providers.txt_file import TxtFileProvider

fake = Faker("en_GB")
fake.add_provider(TxtFileProvider)
fake.add_provider(PdfFileProvider)
fake.add_provider(DocxFileProvider)
fake.add_provider(GraphicJpegFileProvider)
fake.add_provider(GraphicPngFileProvider)

# Various constants determining the result of the script
API_URL = "http://localhost:8002"
IMS_API_URL = "http://localhost:8000"
MAX_NUMBER_ATTACHMENTS_PER_ENTITY = 5
MAX_NUMBER_IMAGES_PER_ENTITY = 5
PROBABILITY_ENTITY_HAS_ATTACHMENTS = 0.3
PROBABILITY_ENTITY_HAS_IMAGES = 0.3
PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD = 0.5
ATTACHMENT_MIN_CHARS = 100
ATTACHMENT_MAX_CHARS = 1000
IMAGE_MIN_SIZE = 200
IMAGE_MAX_SIZE = 600
SEED = 0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def optional_attachment_field(function):
    """Either returns the result of executing the given function, or None while taking into account the fields
    probability to be populated."""

    return function() if fake.random.random() < PROBABILITY_ATTACHMENT_HAS_OPTIONAL_FIELD else None


def generate_random_attachment_metadata(entity_id: str):
    """Generates randomised metadata for an attachment with a given entity ID (purposefully excludes the filename as it
    will be determined later with the file data)."""

    return {
        "entity_id": entity_id,
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


def create_attachment(attachment_metadata: dict) -> dict[str, Any]:
    """Creates an attachment given its metadata and uploads some randomly generated file data to it."""

    file = None
    extension = fake.random.choice(["txt", "pdf", "docx"])

    params = {"raw": True, "max_nb_chars": fake.random.randint(ATTACHMENT_MIN_CHARS, ATTACHMENT_MAX_CHARS)}

    if extension == "txt":
        file = fake.txt_file(**params)
    elif extension == "pdf":
        # Use this generator as default requires wkhtmltopdf to be installed on the system separately
        # see https://faker-file.readthedocs.io/en/0.15.5/faker_file.providers.pdf_file.html
        file = fake.pdf_file(**params, pdf_generator_cls=ReportlabPdfGenerator)
    elif extension == "docx":
        file = fake.docx_file(**params)

    file_name = fake.file_name(extension=extension)

    attachment = post("/attachments", {**attachment_metadata, "file_name": file_name})
    upload_info = attachment["upload_info"]
    requests.post(
        upload_info["url"],
        files={"file": file},
        data=upload_info["fields"],
        timeout=5,
    )

    return attachment


def create_image(image_metadata: dict) -> dict[str, Any]:
    """Creates an image given its metadata and uploads some file data to it."""

    file = None
    extension = fake.random.choice(["jpeg", "png"])

    params = {
        "image_generator_cls": PilImageGenerator,
        "raw": True,
        "size": (
            fake.random.randint(IMAGE_MIN_SIZE, IMAGE_MAX_SIZE),
            fake.random.randint(IMAGE_MIN_SIZE, IMAGE_MAX_SIZE),
        ),
    }

    # Use PIL generator as default requires wkhtmltopdf to be installed on the system separately
    # see https://faker-file.readthedocs.io/en/latest/creating_images.html
    # Also avoid having text in it as Rocky 8 cannot load fonts presumably due to lacking any being installed
    if extension == "jpeg":
        file = fake.graphic_jpeg_file(**params)
    elif extension == "png":
        file = fake.graphic_png_file(**params)

    file_name = fake.file_name(extension=extension)

    image = requests.post(
        f"{API_URL}/images",
        data=image_metadata,
        files={"upload_file": (file_name, file, f"image/{extension}")},
        timeout=5,
    ).json()

    return image


def populate_random_attachments(existing_entity_ids: list[str], exclude_existence_check=False):
    """Randomly populates attachments for the given list of entity IDs."""

    for entity_id in existing_entity_ids:
        if exclude_existence_check or fake.random.random() < PROBABILITY_ENTITY_HAS_ATTACHMENTS:
            for _ in range(0, fake.random.randint(1, MAX_NUMBER_ATTACHMENTS_PER_ENTITY)):
                attachment_metadata = generate_random_attachment_metadata(entity_id)
                create_attachment(attachment_metadata)


def populate_random_images(existing_entity_ids: list[str], exclude_existence_check=False):
    """Randomly populates images for the given list of entity IDs."""

    for entity_id in existing_entity_ids:
        if exclude_existence_check or fake.random.random() < PROBABILITY_ENTITY_HAS_IMAGES:
            for _ in range(0, fake.random.randint(1, MAX_NUMBER_IMAGES_PER_ENTITY)):
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


def generate_mock_data(entity_ids: list[str] = None):
    """Generates mock data for all the entities."""

    existing_entity_ids = entity_ids
    exclude_existence_check = False

    if not entity_ids:
        logger.info("Obtaining a list of existing IMS entities...")
        existing_entity_ids = obtain_existing_ims_entities()
    else:
        exclude_existence_check = True

    logger.info("Populating attachments...")
    populate_random_attachments(existing_entity_ids, exclude_existence_check)

    logger.info("Populating images...")
    populate_random_images(existing_entity_ids, exclude_existence_check)


if __name__ == "__main__":
    generate_mock_data()
