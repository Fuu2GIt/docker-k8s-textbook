#!/usr/bin/env python3
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
import build


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.bad_assets = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
        if tag in {"img", "script", "source"} and values.get("src"):
            self.hrefs.append(values["src"])
            if values["src"].startswith(("http://", "https://", "//")):
                self.bad_assets.append(values["src"])
        if tag == "link" and values.get("href"):
            self.hrefs.append(values["href"])
            if "stylesheet" in values.get("rel", "") and values["href"].startswith(("http://", "https://", "//")):
                self.bad_assets.append(values["href"])


def main():
    complete = "--complete" in sys.argv
    build.main()
    docs = ROOT / "docs"
    errors = []
    pages = list(docs.rglob("*.html"))
    parsed = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        collector = Collector()
        collector.feed(text)
        parsed[page] = collector
        errors.extend(f"{page}: 外部アセット {asset}" for asset in collector.bad_assets)
    for page, collector in parsed.items():
        for href in collector.hrefs:
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, fragment = href.partition("#")
            path = (page.parent / target).resolve() if target else page
            try:
                path.relative_to(docs.resolve())
            except ValueError:
                errors.append(f"{page}: サイト外へのリンク {href}")
                continue
            if target and not path.is_file():
                errors.append(f"{page}: リンク先がありません {href}")
                continue
            if fragment:
                owner = parsed.get(path)
                if owner is None or unquote(fragment) not in owner.ids:
                    errors.append(f"{page}: 見出しがありません {href}")
    outline_ids = [chapter["id"] for chapter in build.load_outline()[1]]
    written = sorted(path.stem for path in (docs / "chapters").glob("*.html"))
    if complete and written != outline_ids:
        errors.append(f"21章が揃っていません: {written}")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"checked {len(pages)} pages, chapters {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
