#!/usr/bin/env python3
"""Seed a cold Actions cache from the currently published photo bundle.

This runs only when the GitHub Actions photo cache is not an exact hit. It lets
an upgrade reuse already-published assets instead of querying Commons/download
all photos again. If the published bundle is unavailable, it exits successfully
and the incremental downloader handles missing assets.
"""
import json, os, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
PHOTO_DIR = DIST / 'assets' / 'photos'
MANIFEST = PHOTO_DIR / 'manifest.json'
BASE = os.environ.get('PUBLISHED_PHOTO_BASE', 'https://strawhatsailer-hash.github.io/japan-atlas-pro').rstrip('/')
UA = 'JapanAtlasProPhotoSeed/1.0 (reuse published public photo assets)'

def fetch(url: str, timeout: int = 25) -> bytes:
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()

def safe_rel(thumb: str) -> str | None:
    prefix = './assets/photos/'
    if not isinstance(thumb, str) or not thumb.startswith(prefix):
        return None
    rel = thumb[2:]
    path = Path(rel)
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] != 'assets' or len(path.parts) != 3:
        return None
    return rel

def main() -> int:
    if MANIFEST.is_file():
        try:
            current = json.loads(MANIFEST.read_text(encoding='utf-8'))
            if isinstance(current, dict) and any(isinstance(v, list) and v for k, v in current.items() if k != '_meta'):
                print('Published bundle seed skipped: a restored/local photo manifest already exists.')
                return 0
        except (OSError, json.JSONDecodeError):
            pass
    try:
        raw = fetch(BASE + '/assets/photos/manifest.json')
        manifest = json.loads(raw.decode('utf-8'))
        if not isinstance(manifest, dict):
            raise ValueError('published manifest is not a JSON object')
    except Exception as exc:
        print(f'WARN could not seed from the current published site: {exc}')
        print('The incremental Commons downloader will fill missing photos if possible.')
        return 0
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)
    reused = 0
    for place_id, items in manifest.items():
        if place_id == '_meta' or not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            rel = safe_rel(item.get('thumb', ''))
            if not rel:
                continue
            dest = (DIST / rel).resolve()
            try:
                dest.relative_to(PHOTO_DIR.resolve())
            except ValueError:
                continue
            if dest.is_file() and dest.stat().st_size > 1000:
                reused += 1
                continue
            url = BASE + '/' + rel
            try:
                data = fetch(url, timeout=40)
                if len(data) < 1000:
                    raise ValueError('published image was unexpectedly small')
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                reused += 1
                print(f'REUSE published asset: {rel}')
            except Exception as exc:
                print(f'WARN published asset unavailable ({rel}): {exc}')
    # Preserve the manifest metadata and paths for the downloader to validate locally.
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Seeded {reused} photo asset(s) from the existing published site.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
