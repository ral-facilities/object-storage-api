"""Module defining a CLI Script for some common development tasks."""

# Expect many arguments as this is a CLI script
# pylint:disable=too-many-arguments
# pylint:disable=too-many-positional-arguments

import logging
import subprocess
from io import TextIOWrapper
from typing import Annotated, Optional

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

DatabaseUsernameOption = Annotated[
    str, typer.Option("--db-username", "-dbu", help="Username for MongoDB authentication.", default_factory="root")
]
DatabasePasswordOption = Annotated[
    str,
    typer.Option("--db-password", "-dbp", help="Password for MongoDB authentication.", default_factory="example"),
]
MinIOHostOption = Annotated[
    str,
    typer.Option("--minio-host", "-mh", help="Host for MinIO.", default_factory="http://localhost:9000"),
]
MinIOUsernameOption = Annotated[
    str,
    typer.Option("--minio-username", "-mu", help="Username for MinIO authentication.", default_factory="root"),
]
MinIOPasswordOption = Annotated[
    str,
    typer.Option(
        "--minio-password", "-mp", help="Password for MinIO authentication.", default_factory="example_password"
    ),
]
YesOption = Annotated[
    bool,
    typer.Option(
        "--yes",
        "-y",
        help="Confirm without any prompts.",
        # See https://github.com/fastapi/typer/discussions/921 - unfortunately even this doesn't work right now
        # for setting a default. So have to define manually in each function its used.
        # default_factory=lambda: False,
        # show_default="False",
    ),
]


def exit_with_error(message: str):
    """Displays an error message in red and then exits."""

    console.print(f"[red bold]{message}[/]")
    raise typer.Exit(1)


def run_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """Runs a command using subprocess."""

    console.print(f"[cyan]Running command:[/] [green]{" ".join(args)}[/]")
    # Output using print to ensure order is correct for grouping on github actions (subprocess.run happens before print
    # for some reason)
    with subprocess.Popen(
        args, stdin=stdin, stdout=stdout if stdout is not None else subprocess.PIPE, universal_newlines=True
    ) as popen:
        if stdout is None:
            for stdout_line in iter(popen.stdout.readline, ""):
                console.print(stdout_line, end="")
            popen.stdout.close()
        return_code = popen.wait()

    if return_code != 0:
        exit_with_error("[red]An error occurred while running the last command![/]")


def run_mongodb_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """Runs a command within the mongodb container."""

    return run_command(
        [
            "docker",
            "exec",
            "-i",
            "object-storage-api-mongodb",
        ]
        + args,
        stdin=stdin,
        stdout=stdout,
    )


def get_mongodb_auth_args(db_username: str, db_password: str):
    """Returns MongoDB authentication arguments in a list."""

    return [
        "--username",
        db_username,
        "--password",
        db_password,
        "--authenticationDatabase=admin",
    ]


def set_minio_alias(minio_host: str, minio_username: str, minio_password: str):
    """Sets a MinIO alias named `object_storage` for use before MinIO commands."""

    run_command(
        [
            "docker",
            "exec",
            "-i",
            "object-storage-minio",
            "mc",
            "alias",
            "set",
            "object-storage",
            minio_host,
            minio_username,
            minio_password,
        ],
    )


def run_minio_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """Runs a command within the minio container."""

    return run_command(
        [
            "docker",
            "exec",
            "-i",
            "object-storage-minio",
        ]
        + args,
        stdin=stdin,
        stdout=stdout,
    )


def clear_existing_data(
    db_username: DatabaseUsernameOption,
    db_password: DatabasePasswordOption,
    minio_host: MinIOHostOption,
    minio_username: MinIOUsernameOption,
    minio_password: MinIOPasswordOption,
    yes: YesOption,
):
    """Clears any existing data in the database/MinIO. Requires confirmation if yes is false."""

    # Firstly confirm if ok with deleting
    if not yes:
        confirm = typer.confirm("This operation will remove all existing data, are you sure?")
        if not confirm:
            raise typer.Abort()

    # Delete the existing data
    console.print("Deleting database contents...")
    run_mongodb_command(
        ["mongosh", "object-storage"]
        + get_mongodb_auth_args(db_username, db_password)
        + [
            "--eval",
            "db.dropDatabase()",
        ]
    )
    console.print("Deleting MinIO bucket contents...")

    # Not ideal that this runs here - would either have to setup once as part of some sort of init (e.g.
    # could have an init for creating the buckets instead of using the minio/mc image) or would have to
    # somehow detect if it has already been done. Doesn't seem to be any harm in setting it again here
    # though.
    set_minio_alias(minio_host, minio_username, minio_password)

    run_minio_command(["mc", "rm", "--recursive", "--force", "object-storage/object-storage"])


@app.command()
def generate(
    db_username: DatabaseUsernameOption,
    db_password: DatabasePasswordOption,
    minio_host: MinIOHostOption,
    minio_username: MinIOUsernameOption,
    minio_password: MinIOPasswordOption,
    yes: YesOption = False,
    clear_existing: Annotated[
        bool,
        typer.Option(
            "--clear",
            "-c",
            help="Whether existing data should be cleared before generating the new data.",
        ),
    ] = False,
    entities: Annotated[
        Optional[list[str]],
        typer.Option("--entity", "-e", help="One or more entity IDs to generate attachments and images for."),
    ] = None,
    num_attachments: Annotated[
        Optional[int],
        typer.Option("--num-attachments", "-na", help="Specific number of attachments to generate for each entity."),
    ] = None,
    num_images: Annotated[
        Optional[int],
        typer.Option("--num-images", "-ni", help="Specific number of images to generate for each entity."),
    ] = None,
):
    """Generates new test data for the database and object storage (runs_generate_mock_data.py)."""

    if clear_existing:
        clear_existing_data(db_username, db_password, minio_host, minio_username, minio_password, yes)

    # Generate new data
    console.print("Generating new mock data...")
    try:
        # Import here only because CI wont install necessary packages to import it directly
        # pylint:disable=import-outside-toplevel
        from generate_mock_data import generate_mock_data

        generate_mock_data(entity_ids=entities, num_attachments=num_attachments, num_images=num_images)
    except ImportError:
        exit_with_error("Failed to find generate_mock_data.py")

    console.print("Success! :party_popper:")


@app.command()
def clear(
    db_username: DatabaseUsernameOption,
    db_password: DatabasePasswordOption,
    minio_host: MinIOHostOption,
    minio_username: MinIOUsernameOption,
    minio_password: MinIOPasswordOption,
    yes: YesOption = False,
):
    """Clears all data in MongoDB and MinIO."""

    clear_existing_data(db_username, db_password, minio_host, minio_username, minio_password, yes)
    console.print("Success! :party_popper:")


def main():
    """Entrypoint for the IMS Dev CLI."""
    app()


if __name__ == "__main__":
    main()
