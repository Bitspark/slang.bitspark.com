"""Build a static, reproducible website release. Python 3.10+, no npm needed."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def design_archive(lock):
    cache = ROOT / ".cache" / (lock["sha256"] + ".zip")
    if cache.exists():
        data = cache.read_bytes()
    else:
        with urllib.request.urlopen(lock["url"], timeout=60) as response:
            data = response.read()
    if hashlib.sha256(data).hexdigest() != lock["sha256"]:
        raise ValueError("Slang Design checksum mismatch")
    cache.parent.mkdir(exist_ok=True)
    cache.write_bytes(data)
    return data


def build():
    lock = json.loads((ROOT / "design-system.lock.json").read_text())
    website = json.loads((ROOT / "website.json").read_text())
    data = design_archive(lock)
    dist = ROOT / "dist"
    if dist.resolve().parent != ROOT or dist.is_symlink():
        raise ValueError("Build output must stay inside this repository")
    if dist.exists():
        # Only this script's fixed, generated output directory is removed.
        shutil.rmtree(dist)
    dist.mkdir()
    shutil.copytree(ROOT / "site", dist / "site")
    design = dist / "site/design" / lock["version"]
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        prefix = "slang-design-" + lock["commit"] + "/"
        for item in archive.infolist():
            if item.is_dir() or not item.filename.startswith(prefix):
                continue
            relative = Path(item.filename[len(prefix):])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Invalid design asset path")
            if relative.parts[0] not in {"styles", "components", "assets", "LICENSE", "NOTICE", "package.json"}:
                continue
            target = design / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    (design / "source.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")
    (dist / "site/website-version.json").write_text(json.dumps(website, indent=2) + "\n", encoding="utf-8", newline="\n")
    for name in ["editor-head.html", "editor-shell.html", "LICENSE", "NOTICE"]:
        shutil.copyfile(ROOT / name, dist / name)
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    artifact = release / f'slang-website-v{website["version"]}.zip'
    with zipfile.ZipFile(artifact, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(dist.rglob("*"), key=lambda path: path.relative_to(dist).as_posix()):
            if source.is_file():
                info = zipfile.ZipInfo(source.relative_to(dist).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o644 << 16
                archive.writestr(info, source.read_bytes())
    checksum = hashlib.sha256(artifact.read_bytes()).hexdigest()
    artifact.with_suffix(".zip.sha256").write_text(f"{checksum}  {artifact.name}\n", encoding="utf-8")
    print(f"Built {artifact.name}: {checksum}")


if __name__ == "__main__":
    build()
