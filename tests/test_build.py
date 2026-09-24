"""Check the distributable's actual resource graph and dependency integrity."""
import hashlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in {"script", "img"} or (tag == "link" and values.get("rel") in {"stylesheet", "icon", "preload"}):
            url = values.get("src") or values.get("href")
            if url:
                self.urls.append(url)


class WebsiteReleaseTests(unittest.TestCase):
    def test_all_html_and_css_dependencies_exist(self):
        site = ROOT / "dist/site"
        self.assertTrue((site / "index.html").is_file(), "Run tools/build.py first")
        html = list(site.rglob("*.html"))
        for source in html:
            parser = Resources()
            parser.feed(source.read_text(encoding="utf-8"))
            for url in parser.urls:
                path = urlsplit(url)
                self.assertFalse(path.scheme, f"External runtime resource in {source}: {url}")
                asset = site / path.path.lstrip("/") if path.path.startswith("/") else source.parent / path.path
                self.assertTrue(asset.is_file(), f"Missing resource: {source}: {url}")
        for source in site.rglob("*.css"):
            css = source.read_text(encoding="utf-8")
            urls = re.findall(r"url\(['\"]?([^)'\"]+)", css) + re.findall(r"@import ['\"]([^'\"]+)", css)
            for url in urls:
                self.assertTrue((source.parent / unquote(url)).is_file(), f"Missing CSS dependency: {source}: {url}")

    def test_every_page_links_the_imprint_and_privacy_policy(self):
        # German law requires the imprint to be reachable from every page, and
        # the GDPR requires the privacy policy to be easy to find.
        site = ROOT / "dist/site"
        pages = [page for page in site.rglob("*.html") if "design" not in page.relative_to(site).parts]
        self.assertTrue(pages, "Run tools/build.py first")
        for target in ["imprint", "privacy"]:
            self.assertTrue((site / target / "index.html").is_file())
            for page in pages:
                self.assertIn(f'href="/{target}/"', page.read_text(encoding="utf-8"), f"No {target} link: {page}")

    def test_design_package_is_upstream_and_versioned(self):
        lock = json.loads((ROOT / "design-system.lock.json").read_text())
        package = ROOT / "dist/site/design" / lock["version"]
        self.assertEqual(json.loads((package / "package.json").read_text())["version"], lock["version"])
        self.assertEqual(json.loads((package / "source.json").read_text()), lock)
        import zipfile
        with zipfile.ZipFile(io.BytesIO(build.design_archive(lock))) as archive:
            for asset in package.rglob("*"):
                if asset.is_file() and asset.name != "source.json":
                    upstream = f'slang-design-{lock["commit"]}/{asset.relative_to(package).as_posix()}'
                    self.assertEqual(asset.read_bytes(), archive.read(upstream), upstream)

    def test_dependency_checksum_mismatch_stops_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lock = {"sha256": hashlib.sha256(b"expected").hexdigest(), "url": "https://example.invalid/design.zip"}
            with patch.object(build, "ROOT", root), patch("urllib.request.urlopen", return_value=io.BytesIO(b"wrong")):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    build.design_archive(lock)
            self.assertFalse((root / ".cache").exists())


if __name__ == "__main__":
    unittest.main()
