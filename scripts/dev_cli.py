"""Module defining a CLI Script for some common development tasks."""

import argparse
import logging
import subprocess
import sys
from abc import ABC, abstractmethod
from io import TextIOWrapper
from typing import Optional


def run_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """Runs a command using subprocess."""

    logging.debug("Running command: %s", " ".join(args))
    # Output using print to ensure order is correct for grouping on github actions (subprocess.run happens before print
    # for some reason)
    with subprocess.Popen(
        args, stdin=stdin, stdout=stdout if stdout is not None else subprocess.PIPE, universal_newlines=True
    ) as popen:
        if stdout is None:
            for stdout_line in iter(popen.stdout.readline, ""):
                print(stdout_line, end="")
            popen.stdout.close()
        return_code = popen.wait()
    return return_code


def start_group(text: str, args: argparse.Namespace):
    """Print the start of a group for Github CI (to get collapsable sections)."""

    if args.ci:
        print(f"::group::{text}")
    else:
        logging.info(text)


def end_group(args: argparse.Namespace):
    """End of a group for Github CI."""

    if args.ci:
        print("::endgroup::")


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


def add_mongodb_auth_args(parser: argparse.ArgumentParser):
    """Adds common arguments for MongoDB authentication."""

    parser.add_argument("-dbu", "--db-username", default="root", help="Username for MongoDB authentication")
    parser.add_argument("-dbp", "--db-password", default="example", help="Password for MongoDB authentication")


def get_mongodb_auth_args(args: argparse.Namespace):
    """Returns arguments in a list to use the parser arguments defined in `add_mongodb_auth_args` above."""

    return [
        "--username",
        args.db_username,
        "--password",
        args.db_password,
        "--authenticationDatabase=admin",
    ]


def add_minio_alias_args(parser: argparse.ArgumentParser):
    """Adds common arguments for a MinIO alias."""

    parser.add_argument("-mu", "--minio-username", default="root", help="Username for MinIO authentication")
    parser.add_argument("-mp", "--minio-password", default="example_password", help="Password for MinIO authentication")
    parser.add_argument("-mh", "--minio-host", default="http://localhost:9000", help="Host for MinIO")


def set_minio_alias(args: argparse.Namespace):
    """Sets a MinIO alias named `object_storage` for use before MinIO commands using the parser arguments defined in
    `add_minio_alias_args` above."""

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
            args.minio_host,
            args.minio_username,
            args.minio_password,
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


class SubCommand(ABC):
    """Base class for a sub command."""

    def __init__(self, help_message: str):
        self.help_message = help_message

    @abstractmethod
    def setup(self, parser: argparse.ArgumentParser):
        """Setup the parser by adding any parameters here."""

    @abstractmethod
    def run(self, args: argparse.Namespace):
        """Run the command with the given parameters as added by 'setup'."""


class CommandGenerate(SubCommand):
    """Command to generate new test data for the database and object storage (runs generate_mock_data.py)

    - Deletes all existing data (after confirmation)
    - Runs generate_mock_data.py
    """

    def __init__(self):
        super().__init__(help_message="Generates new test data for the database and dumps it")

    def setup(self, parser: argparse.ArgumentParser):
        add_mongodb_auth_args(parser)
        add_minio_alias_args(parser)
        parser.add_argument(
            "-c",
            "--clear",
            action=argparse.BooleanOptionalAction,
            help="Whether existing data should be cleared before generating new data.",
        )
        parser.add_argument(
            "-e",
            "--entities",
            nargs="+",
            default=None,
            help="One or more entity IDs to generate attachments and images for.",
        )
        parser.add_argument(
            "-na",
            "--num-attachments",
            type=int,
            default=None,
            help="Specific number of attachments to generate for each entity.",
        )
        parser.add_argument(
            "-ni",
            "--num-images",
            type=int,
            default=None,
            help="Specific number of images to generate for each entity.",
        )

    def run(self, args: argparse.Namespace):
        if args.ci:
            sys.exit("Cannot use --ci with generate (currently has interactive input)")

        if args.clear:
            # Firstly confirm ok with deleting
            answer = input("This operation will replace all existing data, are you sure? ")
            if answer in ("y", "yes"):
                # Delete the existing data
                logging.info("Deleting database contents...")
                run_mongodb_command(
                    ["mongosh", "object-storage"]
                    + get_mongodb_auth_args(args)
                    + [
                        "--eval",
                        "db.dropDatabase()",
                    ]
                )
                logging.info("Deleting MinIO bucket contents...")

                # Not ideal that this runs here - would either have to setup once as part of some sort of init (e.g.
                # could have an init for creating the buckets instead of using the minio/mc image) or would have to
                # somehow detect if it has already been done. Doesn't seem to be any harm in setting it again here
                # though.
                set_minio_alias(args)

                run_minio_command(["mc", "rm", "--recursive", "--force", "object-storage/object-storage"])

        # Generate new data
        logging.info("Generating new mock data...")
        try:
            # Import here only because CI wont install necessary packages to import it directly
            # pylint:disable=import-outside-toplevel
            from generate_mock_data import generate_mock_data

            generate_mock_data(
                entity_ids=args.entities, num_attachments=args.num_attachments, num_images=args.num_images
            )
        except ImportError:
            logging.error("Failed to find generate_mock_data.py")


# List of subcommands
commands: dict[str, SubCommand] = {
    "generate": CommandGenerate(),
}


def main():
    """Runs CLI commands."""

    parser = argparse.ArgumentParser(prog="ObjectStorage Dev Script", description="Some commands for development")
    parser.add_argument(
        "--debug", action="store_true", help="Flag for setting the log level to debug to output more info"
    )
    parser.add_argument(
        "--ci", action="store_true", help="Flag for when running on Github CI (will output groups for collapsing)"
    )

    subparser = parser.add_subparsers(dest="command")

    for command_name, command in commands.items():
        command_parser = subparser.add_parser(command_name, help=command.help_message)
        command.setup(command_parser)

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    commands[args.command].run(args)


if __name__ == "__main__":
    main()
