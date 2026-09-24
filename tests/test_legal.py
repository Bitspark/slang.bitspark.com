"""Legal pages are generated from per-deployment data, never written by hand."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import legal

DATA = json.loads((ROOT / "legal/legal.json").read_text(encoding="utf-8"))


def render(data):
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / "legal.json"
        # Templates are resolved next to the data file.
        shutil.copytree(ROOT / "legal" / data["templates"], Path(temp) / data["templates"])
        source.write_text(json.dumps(data), encoding="utf-8")
        site = Path(temp) / "site"
        legal.render(source, site)
        return {name: (site / name / "index.html").read_text(encoding="utf-8") for name in legal.PAGES} | {
            "settings": json.loads((site / "privacy-settings.json").read_text(encoding="utf-8"))}


class LegalPageTests(unittest.TestCase):
    def test_every_value_comes_from_the_data(self):
        pages = render(DATA)
        for page in ("imprint", "privacy"):
            self.assertNotIn("${", pages[page])
        for value in [DATA["controller"]["name"], DATA["controller"]["vat_id"], DATA["controller"]["email"],
                      *DATA["controller"]["address"], *DATA["controller"]["register"]]:
            self.assertIn(value, pages["imprint"])
        self.assertIn(DATA["supervisory_authority"]["name"], pages["privacy"])
        self.assertEqual(pages["settings"], DATA["privacy"])

    def test_client_address_setting_changes_the_policy(self):
        texts = {}
        for mode in legal.CLIENT_ADDRESS_MODES:
            data = copy.deepcopy(DATA)
            data["privacy"]["request_logs"]["client_address"] = mode
            texts[mode] = render(data)["privacy"]
        self.assertIn("They do not record your IP address", texts["none"])
        self.assertIn("a shortened form of your IP address", texts["truncated"])
        self.assertIn("receive: your IP address", texts["full"])
        self.assertEqual(len(set(texts.values())), 3)

    def test_retention_values_are_stated(self):
        data = copy.deepcopy(DATA)
        data["privacy"].update(server_logs={"retention_days": 14}, backups={"retention_days": 1},
                               sign_in={"session_days": 2},
                               execution_history={"retention_days": 90, "max_events_per_deployment": 2500,
                                                  "max_logs_per_deployment": 1})
        text = render(data)["privacy"]
        for phrase in ["deleted after 14 days", "Backups are kept for 1 day,", "<td>2 days, or until you sign out",
                       "keep them for 90 days, and at most 2,500 events and 1 log entries"]:
            self.assertIn(phrase, text)

    def test_design_reference_is_optional(self):
        data = copy.deepcopy(DATA)
        del data["design_reference"]
        text = render(data)["privacy"]
        self.assertNotIn("GitHub Pages", text)
        self.assertIn("No data is transferred outside the EU.", text)

    def test_incomplete_or_invalid_settings_stop_the_build(self):
        for change in [lambda p: p.pop("backups"), lambda p: p["sign_in"].update(session_days=0),
                       lambda p: p["request_logs"].update(client_address="some"),
                       lambda p: p["server_logs"].update(retention="7")]:
            data = copy.deepcopy(DATA)
            change(data["privacy"])
            with self.subTest(settings=data["privacy"]), self.assertRaisesRegex(ValueError, "Invalid legal data"):
                render(data)

    def test_data_is_escaped(self):
        data = copy.deepcopy(DATA)
        data["controller"]["name"] = "Example <b>GmbH</b> & Co."
        text = render(data)["imprint"]
        self.assertIn("Example &lt;b&gt;GmbH&lt;/b&gt; &amp; Co.", text)
        self.assertNotIn("<b>GmbH</b>", text)


if __name__ == "__main__":
    unittest.main()
