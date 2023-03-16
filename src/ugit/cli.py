import argparse
import os

from . import data


def main() -> None:
    args = parse_args()
    args.func(args)


def parse_args() -> None:
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    return parser.parse_args()


def init(args: argparse.Namespace) -> None:
    data.init()
    print(f"Initializated empty ugit reposiroty in {os.getcwd()}/{data.GIT_DIR}")
