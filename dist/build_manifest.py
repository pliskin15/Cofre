# build_manifest.py — Cofre
import hashlib, json, os, sys, shutil
from pathlib import Path
from datetime import datetime, timezone

# ══════════════════════════════════════════
#  ATUALIZE AQUI A CADA NOVA VERSAO
NEW_VERSION = "1.0.2"
# ══════════════════════════════════════════

BUILD_DIR       = Path("dist/Cofre")
OUTPUT_MANIFEST = Path("updates/latest/version.json")
OUTPUT_FILES    = Path("updates/files")
GITHUB_USER     = "pliskin15"
GITHUB_REPO     = "Cofre"
GIT_BRANCH      = "updates"
BASE_URL        = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GIT_BRANCH}/updates/files"

EXCLUDE_NAMES = {"launcher.exe", "updater_config.json", "version.txt"}

def should_exclude(fp: Path, rel: str) -> bool:
    if fp.name in EXCLUDE_NAMES:
        return True
    if any(part.endswith(".dist-info") for part in Path(rel).parts):
        return True
    return False

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b: break
            h.update(b)
    return h.hexdigest()

def main():
    if not BUILD_DIR.exists():
        print(f"[ERRO] Pasta nao encontrada: {BUILD_DIR}")
        sys.exit(1)

    print(f"Varrendo {BUILD_DIR} ...")
    files = {}
    for root, _, filenames in os.walk(BUILD_DIR):
        for name in filenames:
            fp  = Path(root) / name
            rel = fp.relative_to(BUILD_DIR).as_posix()
            if should_exclude(fp, rel):
                continue
            files[rel] = {
                "size":   fp.stat().st_size,
                "sha256": sha256_file(fp),
            }

    manifest = {
        "version":      NEW_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url":     BASE_URL,
        "files":        files,
    }

    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    if OUTPUT_FILES.exists():
        shutil.rmtree(OUTPUT_FILES)
    shutil.copytree(BUILD_DIR, OUTPUT_FILES)

    print(f"[OK] Manifesto gerado: {OUTPUT_MANIFEST}")
    print(f"     Versao:   {NEW_VERSION}")
    print(f"     Arquivos: {len(files)}")
    print()
    print("Proximo passo:")
    print("  git add updates/")
    print(f'  git commit -m "release v{NEW_VERSION}"')
    print("  git push origin updates")

if __name__ == "__main__":
    main()