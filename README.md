# LinPedia

LinPedia is a Linux terminal app for browsing Wikipedia without leaving your shell.

## Features

- Search Wikipedia article titles from CLI.
- Open clean plain-text summaries for articles.
- List internal links from any article.
- Read a random article instantly.
- Choose language with `--lang` (e.g., `en`, `fr`, `es`).

## Quick start

```bash
python3 linpedia.py --help
python3 linpedia.py search "linux"
python3 linpedia.py open "Linux"
python3 linpedia.py links "Linux" --limit 20
python3 linpedia.py random
```

## Command reference

### `search`
Search for article titles.

```bash
python3 linpedia.py search "terminal" --limit 5
```

### `open`
Open the intro summary of an article.

```bash
python3 linpedia.py open "GNU" --width 90
```

### `links`
Show linked article titles from a page.

```bash
python3 linpedia.py links "Linux" --limit 30
```

### `random`
Get a random Wikipedia article summary.

```bash
python3 linpedia.py random
```

## Language support

Use `--lang` to query another Wikipedia language edition:

```bash
python3 linpedia.py --lang fr search "Système d'exploitation"
python3 linpedia.py --lang fr open "Linux"
```

## Notes

- Internet connection is required.
- LinPedia uses the Wikipedia API directly (no third-party dependencies).

## Status

This is a functional MVP CLI and can be extended with paging, caching, and offline modes.
