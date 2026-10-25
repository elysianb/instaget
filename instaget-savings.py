#!/usr/bin/env python3
# instaget-savings.py

import argparse
import json
import logging
import sys
from pathlib import Path

from instagrapi import Client


DEFAULT_SESSION_FILENAME = "instagram_session.json"


class SingleActionArgumentParser(argparse.ArgumentParser):
    def parse_args(self, args=None, namespace=None):
        parsed = super().parse_args(args=args, namespace=namespace)
        ensure_single_action(self, parsed)
        return parsed


def default_session_path():
    return Path.home() / DEFAULT_SESSION_FILENAME


def build_parser():
    parser = SingleActionArgumentParser(
        description=(
            "Instagram collection utilities for listing saved collections and exporting "
            "their media links. The script uses a session file stored by default in the "
            "current user's home directory so you don't need to log in every time."
        ),
        epilog=(
            "Examples:\n"
            "  py instaget-savings.py --list\n"
            "  py instaget-savings.py --list --username myuser --password mypass\n"
            "  py instaget-savings.py --get \"Animals\" output.txt\n"
            "  py instaget-savings.py --get \"Animals\" C:/temp/links.txt --username myuser --password mypass\n\n"
            "Notes:\n"
            "  * --list prints a JSON array of collections with their id and name.\n"
            "  * --get exports the direct Instagram URLs for all media in the chosen collection.\n"
            "  * If the session file exists and is valid, it is reused automatically.\n"
            "  * If the session is missing or invalid, you can supply --username and --password "
            "for the current run to refresh it.\n"
            "  * The default session path is: %%USERPROFILE%%\\instagram_session.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help='List all collections for the authenticated user as JSON: [ {"id": ..., "name": ...} ]',
    )
    parser.add_argument(
        "--get",
        nargs=2,
        metavar=("COLLECTION_NAME", "OUTPUT_FILE"),
        help=(
            "Export all public links from the given collection into a text file. "
            "The output file is created automatically if needed."
        ),
    )
    parser.add_argument(
        "--session",
        default=str(default_session_path()),
        help=(
            "Path to the Instagram session JSON file. Default: %%USERPROFILE%%\\instagram_session.json "
            "(example: C:\\Users\\YourName\\instagram_session.json)"
        ),
    )
    parser.add_argument(
        "--username",
        help="Instagram username used only when the session file is missing or invalid.",
    )
    parser.add_argument(
        "--password",
        help="Instagram password used only when the session file is missing or invalid.",
    )
    return parser


def ensure_single_action(parser, args):
    chosen_actions = [args.list, bool(args.get)]
    if sum(chosen_actions) != 1:
        parser.error(
            "Choose exactly one action: --list or --get COLLECTION_NAME OUTPUT_FILE"
        )


def resolve_session_path(args):
    return Path(args.session).expanduser()


def login_and_save(client, session_path, username=None, password=None):
    try:
        if session_path.exists():
            logging.info("Loading saved Instagram session from %s", session_path)
            client.load_settings(str(session_path))

            if username and password:
                logging.info("Credentials provided; refreshing the stored session.")
                client.login(username, password)
            else:
                sessionid = (
                    client.get_settings()
                    .get("cookies", {})
                    .get("sessionid", "")
                )

                if not sessionid:
                    raise RuntimeError(
                        "Saved session is missing a valid sessionid. "
                        "Provide --username and --password to refresh it, "
                        "or delete the old session file and retry."
                    )

                logging.info("Reusing sessionid from the saved session.")
                client.login_by_sessionid(sessionid)
        elif username and password:
            logging.info("No session file was found. Logging in and creating a new session.")
            client.login(username, password)
        else:
            raise RuntimeError(
                f"No session file was found at {session_path}. "
                "Provide --username and --password to create it."
            )

        logging.info("Saving the updated session to %s", session_path)
        client.dump_settings(str(session_path))
        logging.info("Session saved successfully.")
        return client

    except Exception as exc:
        logging.error("Authentication failed: %s", exc)
        raise


def list_collections(client):
    logging.info("Fetching collections for the authenticated user...")
    collections = client.collections()
    logging.info("Retrieved %d collections.", len(collections))

    payload = [{"id": str(item.id), "name": item.name} for item in collections]

    if not payload:
        print(json.dumps([], ensure_ascii=False))
        return []

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return collections


def export_collection(client, collection_name, output_file):
    logging.info("Looking for collection '%s'.", collection_name)
    collections = client.collections()
    collection = next(
        (
            item
            for item in collections
            if item.name.casefold() == collection_name.casefold()
        ),
        None,
    )

    if collection is None:
        names = [item.name for item in collections]
        raise ValueError(
            f"Collection '{collection_name}' was not found. "
            f"Available collections: {names}"
        )

    logging.info("Selected collection '%s' with id '%s'.", collection.name, collection.id)

    logging.info("Loading media items from collection '%s'...", collection.name)
    items = client.collection_medias(str(collection.id), amount=0)
    logging.info("Retrieved %d media items.", len(items))

    links = []
    for index, item in enumerate(items, start=1):
        code = getattr(item, "code", None)
        if not code:
            logging.warning("Skipping item #%d because it has no media code.", index)
            continue

        product_type = getattr(item, "product_type", None)
        route = "reel" if product_type == "clips" else "p"
        links.append(f"https://www.instagram.com/{route}/{code}/")

    logging.info("Removing duplicate links while preserving order.")
    links = list(dict.fromkeys(links))
    logging.info("Unique links count after deduplication: %d", len(links))

    output_path = Path(output_file).expanduser()
    logging.info("Creating output directory if needed: %s", output_path.parent)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_text = "\n".join(links) + ("\n" if links else "")
    output_path.write_text(output_text, encoding="utf-8")
    logging.info("Exported %d links to %s", len(links), output_path.resolve())

    print(f"Collection: {collection.name}")
    print(f"Media retrieved: {len(items)}")
    print(f"Links exported: {len(links)}")
    print(f"Output file: {output_path.resolve()}")
    return 0


def main(argv=None):
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    parser = build_parser()

    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)
    ensure_single_action(parser, args)

    session_path = resolve_session_path(args)
    logging.info("Session file path: %s", session_path)

    client = Client()

    try:
        if args.list:
            logging.info("Starting collection listing flow.")
            login_and_save(client, session_path, args.username, args.password)
            list_collections(client)
            return 0

        if args.get:
            collection_name, output_file = args.get
            logging.info("Starting export flow for '%s' to '%s'.", collection_name, output_file)
            login_and_save(client, session_path, args.username, args.password)
            export_collection(client, collection_name, output_file)
            return 0

    except Exception as exc:
        logging.error("Operation failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error("No valid action was selected.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
