"""Render the imprint and privacy policy from per-deployment legal data.

The wording depends on the legal framework and the facts on the deployment, so
neither is written into the site. legal/legal.json holds the operator's details
and the privacy settings the servers run with; legal/<templates>/ holds the
wording for one framework (eu-de: GDPR, TDDDG and the German imprint duty).
Another jurisdiction provides its own data and, where its law differs, its own
templates.

The build also publishes the settings the policy states as
site/privacy-settings.json. The infrastructure's release tool refuses to install
a website whose stated settings differ from the host's, so the policy cannot
promise something the servers do not do.
"""
import datetime
import html
import json
from pathlib import Path
from string import Template

CLIENT_ADDRESS_MODES = ("full", "truncated", "none")
# Mirrors slang-infra's slang_cloud.privacy; every value must be stated.
PRIVACY_KEYS = {
    "request_logs": ["client_address"],
    "server_logs": ["retention_days"],
    "execution_history": ["retention_days", "max_events_per_deployment", "max_logs_per_deployment"],
    "backups": ["retention_days"],
    "sign_in": ["session_days"],
}
PAGES = {"imprint": "imprint.html", "privacy": "privacy.html"}


def check_privacy(settings):
    problems = []
    if set(settings) != set(PRIVACY_KEYS):
        problems.append(f"privacy must have exactly the sections {', '.join(PRIVACY_KEYS)}")
    for section, keys in PRIVACY_KEYS.items():
        values = settings.get(section, {})
        if set(values) != set(keys):
            problems.append(f"privacy.{section} must have exactly {', '.join(keys)}")
            continue
        for key, value in values.items():
            if (section, key) == ("request_logs", "client_address"):
                if value not in CLIENT_ADDRESS_MODES:
                    problems.append(f"privacy.{section}.{key} must be one of {', '.join(CLIENT_ADDRESS_MODES)}")
            elif isinstance(value, bool) or not isinstance(value, int) or value < 1:
                problems.append(f"privacy.{section}.{key} must be a positive whole number")
    if problems:
        raise ValueError("Invalid legal data: " + "; ".join(problems))
    return settings


def number(value):
    return f"{value:,}"


def days(value):
    return "1 day" if value == 1 else f"{value} days"


def joined(items):
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def context(data, templates):
    """Template values; data values are HTML-escaped, generated markup is not."""
    e = html.escape
    privacy = check_privacy(data["privacy"])
    controller, authority, hosting = data["controller"], data["supervisory_authority"], data["hosting"]
    mode = privacy["request_logs"]["client_address"]
    log_days = privacy["server_logs"]["retention_days"]
    history = privacy["execution_history"]
    design = data.get("design_reference")
    common_fields = ("the time, the requested address (which includes any search terms you enter in the "
                     "studio), the response status, the referring page and your browser identification")
    request_log_fields = {
        "full": "your IP address, " + common_fields,
        "truncated": "a shortened form of your IP address, with its last part removed, " + common_fields,
        "none": common_fields + ". They do not record your IP address",
    }[mode]
    ip_summary = {
        "full": f"Our request logs record IP addresses and are deleted after {days(log_days)}.",
        "truncated": "Our request logs record only shortened IP addresses.",
        "none": "Our request logs do not record IP addresses.",
    }[mode]
    design_section = ""
    if design:
        design_section = Template((templates / "design-reference.html").read_text(encoding="utf-8")).substitute(
            design_address=e(design["address"]), design_host=e(design["host"]),
            design_privacy_statement=e(design["privacy_statement"]))
    updated = datetime.date.fromisoformat(data["policy_updated"])
    return {
        "controller_name": e(controller["name"]),
        "controller_address": "<br>".join(e(line) for line in controller["address"]),
        "email": e(controller["email"]),
        "phone": e(controller["phone"]),
        "phone_href": "".join(ch for ch in controller["phone"] if ch.isdigit() or ch == "+"),
        "representative": e(controller["representative"]),
        "register": "<br>".join(e(line) for line in controller["register"]),
        "vat_id": e(controller["vat_id"]),
        "authority_name": e(authority["name"]),
        "authority_address": e(authority["address"]),
        "authority_url": e(authority["url"]),
        "authority_host": e(authority["url"].split("//", 1)[-1].rstrip("/")),
        "hosting_provider": e(hosting["provider"]),
        "hosting_address": e(hosting["address"]),
        "hosting_location": e(hosting["location"]),
        "hosting_country": e(hosting["country"]),
        "covered": joined([f"<strong>{e(item)}</strong>" for item in data["covered"]]),
        "policy_updated": f"{updated.day} {updated:%B %Y}",
        "ip_summary": ip_summary,
        "design_summary": " The only exception is the design reference, which GitHub hosts." if design else "",
        "design_section": design_section,
        "transfer_sentence": ("Apart from the design reference, no data is transferred outside the EU."
                              if design else "No data is transferred outside the EU."),
        "request_log_fields": request_log_fields,
        "log_retention": days(log_days),
        "session_lifetime": days(privacy["sign_in"]["session_days"]),
        "history_retention": days(history["retention_days"]),
        "history_events": number(history["max_events_per_deployment"]),
        "history_logs": number(history["max_logs_per_deployment"]),
        "backup_retention": days(privacy["backups"]["retention_days"]),
    }


def render(data_path, site):
    """Write the legal pages and stated settings into a built site directory."""
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    templates = Path(data_path).resolve().parent / data["templates"]
    values = context(data, templates)
    for page, name in PAGES.items():
        text = Template((templates / name).read_text(encoding="utf-8")).substitute(values)
        target = Path(site) / page / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    (Path(site) / "privacy-settings.json").write_text(
        json.dumps(data["privacy"], indent=2) + "\n", encoding="utf-8", newline="\n")
