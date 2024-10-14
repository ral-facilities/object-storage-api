"""Module defining a CLI Script for some common development tasks"""

import argparse
import logging
import subprocess
import sys
from abc import ABC, abstractmethod
from io import TextIOWrapper
from typing import Optional


def run_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """
    Runs a command using subprocess
    """
    logging.debug("Running command: %s", " ".join(args))
    # Output using print to ensure order is correct for grouping on github actions (subprocess.run happens before print
    # for some reason)
    popen = subprocess.Popen(
        args, stdin=stdin, stdout=stdout if stdout is not None else subprocess.PIPE, universal_newlines=True
    )
    if stdout is None:
        for stdout_line in iter(popen.stdout.readline, ""):
            print(stdout_line, end="")
        popen.stdout.close()
    return_code = popen.wait()
    return return_code


def start_group(text: str, args: argparse.Namespace):
    """Print the start of a group for Github CI (to get collapsable sections)"""
    if args.ci:
        print(f"::group::{text}")
    else:
        logging.info(text)


def end_group(args: argparse.Namespace):
    """End of a group for Github CI"""
    if args.ci:
        print("::endgroup::")


def run_mongodb_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """
    Runs a command within the mongodb container
    """
    return run_command(
        [
            "docker",
            "exec",
            "-i",
            "object_storage_api_mongodb_container",
        ]
        + args,
        stdin=stdin,
        stdout=stdout,
    )


def add_mongodb_auth_args(parser: argparse.ArgumentParser):
    """Adds common arguments for MongoDB authentication"""

    parser.add_argument("-u", "--db-username", default="root", help="Username for MongoDB authentication")
    parser.add_argument("-p", "--db-password", default="example", help="Password for MongoDB authentication")


def get_mongodb_auth_args(args: argparse.Namespace):
    """Returns arguments in a list to use the parser arguments defined in add_mongodb_auth_args above"""
    return [
        "--username",
        args.db_username,
        "--password",
        args.db_password,
        "--authenticationDatabase=admin",
    ]


def run_minio_command(args: list[str], stdin: Optional[TextIOWrapper] = None, stdout: Optional[TextIOWrapper] = None):
    """
    Runs a command within the mongodb container
    """
    return run_command(
        [
            "docker",
            "exec",
            "-i",
            "object_storage_minio_mc_container",
        ]
        + args,
        stdin=stdin,
        stdout=stdout,
    )


class SubCommand(ABC):
    """Base class for a sub command"""

    def __init__(self, help_message: str):
        self.help_message = help_message

    @abstractmethod
    def setup(self, parser: argparse.ArgumentParser):
        """Setup the parser by adding any parameters here"""

    @abstractmethod
    def run(self, args: argparse.Namespace):
        """Run the command with the given parameters as added by 'setup'"""


class CommandGenerate(SubCommand):
    # TODO: Update comments
    """Command to generate new test data for the database (runs generate_mock_data.py)

    - Deletes all existing data (after confirmation)
    - Imports units
    - Runs generate_mock_data.py

    Has option to dump the data into './data/mock_data.dump'.
    """

    def __init__(self):
        super().__init__(help_message="Generates new test data for the database and dumps it")

    def setup(self, parser: argparse.ArgumentParser):
        add_mongodb_auth_args(parser)

        parser.add_argument(
            "-d", "--dump", action="store_true", help="Whether to dump the output into a file that can be committed"
        )

    def run(self, args: argparse.Namespace):
        if args.ci:
            sys.exit("Cannot use --ci with generate (currently has interactive input)")

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
            # run_minio_command(
            #     ["mc", "alias", "set", "object-storage", "http://localhost:9000", "root", "example_password"]
            # )
            run_minio_command(["mc", "rm", "--recursive", "--force", "object-storage/object-storage"])
            # Generate new data
            logging.info("Generating new mock data...")
            try:
                # Import here only because CI wont install necessary packages to import it directly
                from generate_mock_data import generate_mock_data

                generate_mock_data()
            except ImportError:
                logging.error("Failed to find generate_mock_data.py")


# List of subcommands
commands: dict[str, SubCommand] = {
    "generate": CommandGenerate(),
}


def main():
    """Runs CLI commands"""
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
