#!/usr/bin/env python3
"""LinPedia: browse Wikipedia from the Linux terminal."""

from __future__ import annotations

import argparse
import json
import re
import sys
import textwrap
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any



class LinpediaError(Exception):
    """Known LinPedia runtime error."""


@dataclass
class WikiClient:
    language: str = "en"
    timeout: int = 10

    @property
    def api_url(self) -> str:
        return f"https://{self.language}.wikipedia.org/w/api.php"

    def _request(self, params: dict[str, Any]) -> dict[str, Any] | list[Any]:
        query = urllib.parse.urlencode(params)
        url = f"{self.api_url}?{query}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "LinPedia/0.1 (+https://wikipedia.org)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001 - show friendly error
            raise LinpediaError(f"Wikipedia request failed: {exc}") from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise LinpediaError("Wikipedia response was not valid JSON") from exc

    def search(self, term: str, limit: int = 10) -> list[dict[str, str]]:
        response = self._request(
            {
                "action": "opensearch",
                "search": term,
                "limit": limit,
                "namespace": 0,
                "format": "json",
            }
        )
        if not isinstance(response, list) or len(response) < 4:
            raise LinpediaError("Unexpected search response format")

        titles = response[1]
        descriptions = response[2]
        urls = response[3]

        results: list[dict[str, str]] = []
        for idx, title in enumerate(titles):
            results.append(
                {
                    "title": str(title),
                    "description": str(descriptions[idx]) if idx < len(descriptions) else "",
                    "url": str(urls[idx]) if idx < len(urls) else "",
                }
            )
        return results

    def summary(self, title: str) -> tuple[str, str]:
        response = self._request(
            {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "redirects": 1,
                "titles": title,
                "format": "json",
            }
        )

        pages = response.get("query", {}).get("pages", {})
        if not pages:
            raise LinpediaError("No page found")

        page = next(iter(pages.values()))
        real_title = page.get("title", title)
        extract = page.get("extract", "")
        if not extract:
            raise LinpediaError(f"No extract available for '{real_title}'")
        return real_title, str(extract)

    def links(self, title: str, limit: int = 50) -> list[str]:
        response = self._request(
            {
                "action": "query",
                "prop": "links",
                "plnamespace": 0,
                "pllimit": min(limit, 500),
                "redirects": 1,
                "titles": title,
                "format": "json",
            }
        )

        pages = response.get("query", {}).get("pages", {})
        if not pages:
            raise LinpediaError("No page found")

        page = next(iter(pages.values()))
        links = page.get("links", [])
        if not links:
            return []
        return [str(item.get("title", "")).strip() for item in links if item.get("title")]

    def random_title(self) -> str:
        response = self._request(
            {
                "action": "query",
                "list": "random",
                "rnnamespace": 0,
                "rnlimit": 1,
                "format": "json",
            }
        )
        random_entries = response.get("query", {}).get("random", [])
        if not random_entries:
            raise LinpediaError("Random article request returned no entries")
        return str(random_entries[0].get("title", ""))


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return text


def print_wrapped(text: str, width: int = 100) -> None:
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            print()
            continue
        print(textwrap.fill(paragraph, width=width))


def cmd_search(client: WikiClient, args: argparse.Namespace) -> int:
    results = client.search(args.term, args.limit)
    if not results:
        print("No results found.")
        return 0

    for i, row in enumerate(results, start=1):
        print(f"{i:>2}. {row['title']}")
        if row["description"]:
            print(f"    {row['description']}")
        if row["url"]:
            print(f"    {row['url']}")
        print()
    return 0


def cmd_open(client: WikiClient, args: argparse.Namespace) -> int:
    title, summary = client.summary(args.title)
    print(f"# {title}\n")
    print_wrapped(clean_text(summary), width=args.width)
    return 0


def cmd_links(client: WikiClient, args: argparse.Namespace) -> int:
    items = client.links(args.title, limit=args.limit)
    if not items:
        print("No links found.")
        return 0

    for idx, item in enumerate(items, start=1):
        print(f"{idx:>2}. {item}")
    return 0


def cmd_random(client: WikiClient, args: argparse.Namespace) -> int:
    title = client.random_title()
    title, summary = client.summary(title)
    print(f"# {title}\n")
    print_wrapped(clean_text(summary), width=args.width)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="linpedia",
        description="Browse Wikipedia from your Linux terminal.",
    )
    parser.add_argument("--lang", default="en", help="Wikipedia language code (default: en)")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", required=True)

    p_search = subparsers.add_parser("search", help="Search for article titles")
    p_search.add_argument("term", help="Search term")
    p_search.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    p_search.set_defaults(func=cmd_search)

    p_open = subparsers.add_parser("open", help="Open article summary")
    p_open.add_argument("title", help="Article title")
    p_open.add_argument("--width", type=int, default=100, help="Wrap width")
    p_open.set_defaults(func=cmd_open)

    p_links = subparsers.add_parser("links", help="List links from an article")
    p_links.add_argument("title", help="Article title")
    p_links.add_argument("--limit", type=int, default=50, help="Max links to show")
    p_links.set_defaults(func=cmd_links)

    p_random = subparsers.add_parser("random", help="Open a random article summary")
    p_random.add_argument("--width", type=int, default=100, help="Wrap width")
    p_random.set_defaults(func=cmd_random)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    client = WikiClient(language=args.lang, timeout=args.timeout)

    try:
        return args.func(client, args)
    except LinpediaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
