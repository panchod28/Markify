#!/usr/bin/env python3
"""
Genera THIRD_PARTY_LICENSES.txt con los textos de licencia de lo que viaja en los instaladores:

  - Python: todas las distribuciones del entorno del sidecar (menos herramientas solo de prueba o de empaquetado).
  - npm:    dependencias de producción de package-lock.json (las `dev` no se incluyen).
  - Rust:   crates de src-tauri (cargo metadata; es una cota superior: incluye los de las tres plataformas).

Los textos idénticos se agrupan para que el archivo no crezca. Lo que no trae archivo de licencia se lista con la
licencia que declara su metadato.

Uso (con el Python del entorno del sidecar, para ver sus distribuciones):
    sidecar/.venv/bin/python scripts/gen_licenses.py
    sidecar/.venv/bin/python scripts/gen_licenses.py --check    # falla si aparece GPL/AGPL (sin excepción conocida)
"""

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "THIRD_PARTY_LICENSES.txt"
NOT_SHIPPED = {"pytest", "pluggy", "iniconfig", "reportlab", "xlwt", "pip", "wheel"}  # pruebas y utilidades de desarrollo
LICENSE_FILE = re.compile(r"^(LICEN[CS]E|COPYING|NOTICE|UNLICENSE|COPYRIGHT)([-_.].*)?$", re.IGNORECASE)
# Copyleft con excepción conocida y revisada (ver THIRD_PARTY_NOTICES.md): PyInstaller permite distribuir lo empaquetado
# con cualquier licencia; r-efi solo se compila para UEFI y ofrece MIT/Apache.
KNOWN_COPYLEFT_OK = {"pyinstaller", "pyinstaller-hooks-contrib", "r-efi"}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").strip()


def license_files(directory: Path) -> list[Path]:
    found = [p for p in directory.iterdir() if p.is_file() and LICENSE_FILE.match(p.name)] if directory.is_dir() else []
    for sub in ("licenses", "LICENSES", "license"):
        if (directory / sub).is_dir():
            found += [p for p in (directory / sub).rglob("*") if p.is_file()]
    return sorted(found)


def python_packages():
    for d in metadata.distributions():
        name = d.metadata["Name"]
        if not name or name.lower() in NOT_SHIPPED:
            continue
        lic = (d.metadata.get("License-Expression") or d.metadata.get("License") or "").strip().replace("\n", " ")
        if len(lic) > 120:
            lic = ""  # el campo trae el texto entero: se verá en el archivo de licencia
        classifiers = [c.split("::")[-1].strip() for c in d.metadata.get_all("Classifier", []) if c.startswith("License")]
        texts = []
        for f in d.files or []:
            parts = f.parts
            if LICENSE_FILE.match(f.name) or any(p.lower() in ("licenses", "license") for p in parts[:-1]):
                located = f.locate()
                if located.is_file():
                    texts.append((str(f), read(located)))
        yield "python", name, d.version, lic or ", ".join(classifiers), texts


def npm_packages():
    lock = ROOT / "package-lock.json"
    if not lock.exists():
        print("aviso: sin package-lock.json, se omite npm", file=sys.stderr)
        return
    for path, info in json.loads(lock.read_text()).get("packages", {}).items():
        if not path or info.get("dev") or "node_modules" not in path:
            continue
        directory = ROOT / path
        if not directory.is_dir():
            continue
        pkg = json.loads((directory / "package.json").read_text())
        lic = pkg.get("license") or (pkg.get("licenses") or [{}])[0].get("type") or ""
        yield "npm", pkg["name"], pkg.get("version", "?"), lic if isinstance(lic, str) else str(lic), \
            [(p.name, read(p)) for p in license_files(directory)]


def rust_packages():
    try:
        out = subprocess.run(["cargo", "metadata", "--format-version", "1", "--manifest-path", str(ROOT / "src-tauri" / "Cargo.toml")],
                             capture_output=True, text=True, check=True).stdout
    except Exception as e:  # sin cargo no se puede enumerar: se avisa y se sigue
        print(f"aviso: no se pudo ejecutar cargo metadata ({type(e).__name__}), se omite Rust", file=sys.stderr)
        return
    for p in json.loads(out)["packages"]:
        if p["name"] == "markify":
            continue
        yield "rust", p["name"], p["version"], p.get("license") or "", \
            [(f.name, read(f)) for f in license_files(Path(p["manifest_path"]).parent)]


def main() -> int:
    packages = [*python_packages(), *npm_packages(), *rust_packages()]
    by_text: dict[str, list] = defaultdict(list)
    no_text = []
    for eco, name, version, lic, texts in packages:
        if not texts:
            no_text.append((eco, name, version, lic))
        for _, body in texts:
            if body:
                by_text[hashlib.sha1(body.encode()).hexdigest()].append((body, f"{eco}:{name} {version}"))

    counts = Counter(f"{eco}" for eco, *_ in packages)
    copyleft = [(eco, n, v, lic) for eco, n, v, lic, _ in packages
                if re.search(r"gpl|affero", lic, re.IGNORECASE) and n.lower() not in KNOWN_COPYLEFT_OK]
    lines = [
        "Third-party licenses of the components shipped with Markify",
        "=" * 60,
        "Generated by scripts/gen_licenses.py. Scope: Python packages of the sidecar bundle, production npm packages",
        "of the frontend and the Rust crates of the Tauri shell (an upper bound: it includes the crates of every",
        "platform). Build/test-only tools are not listed. Identical license texts are grouped.",
        "",
        f"Packages: {dict(counts)}",
        "",
        "Notes",
        "-----",
        "* PyInstaller (its bootloader is part of the sidecar executable) is GPL-2.0-or-later WITH an exception that",
        "  allows distributing the bundled application under any license; see its COPYING text below.",
        "* certifi and tqdm (MPL-2.0) and a few Rust crates (MPL-2.0) are used unmodified; their license texts are included.",
        "* r-efi offers MIT OR Apache-2.0 OR LGPL-2.1-or-later and only compiles for UEFI targets.",
        "* The PP-OCRv5 models (PaddleOCR) are Apache-2.0, the same license as RapidOCR below.",
        "* FFmpeg (needed for audio/video transcription) is NOT bundled; it is installed separately by the user.",
        "",
    ]
    if no_text:
        lines += ["Packages without a license file (license declared in their metadata)", "-" * 68]
        lines += [f"  {eco}:{name} {version}: {lic or 'not declared'}" for eco, name, version, lic in sorted(no_text)]
        lines.append("")
    for n, (digest, group) in enumerate(sorted(by_text.items(), key=lambda kv: kv[1][0][1].lower()), 1):
        who = sorted({label for _, label in group})
        lines += ["", "=" * 78, f"[{n}] applies to: " + ", ".join(who), "=" * 78, group[0][0]]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{OUT.name}: {len(packages)} packages {dict(counts)}, {len(by_text)} distinct texts, {OUT.stat().st_size // 1024} KB, "
          f"{len(no_text)} without a license file")
    if copyleft:
        print("COPYLEFT sin excepción revisada:", *[f"{e}:{n} {v} ({l})" for e, n, v, l in copyleft], sep="\n  ", file=sys.stderr)
        return 1 if "--check" in sys.argv else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
