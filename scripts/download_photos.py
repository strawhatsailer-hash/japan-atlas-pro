#!/usr/bin/env python3
"""Incremental photo bundler for Japan Atlas Pro.

Existing valid local assets are reused. Only destinations without a usable local
bundle are searched. Failed/empty searches have a 7-day cooldown to avoid repeated
Wikimedia requests on every ordinary site update. Set FORCE_MISSING_PHOTO_REFRESH=1
or run the workflow manually with retry_missing_photos=true to retry those gaps.
"""
from __future__ import annotations
import json, os, re, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
PHOTO_DIR = DIST / 'assets' / 'photos'
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
PLACES = json.loads((ROOT / 'places.json').read_text(encoding='utf-8'))
UA = 'JapanAtlasProPhotoBundler/2.0 (personal travel planner; Wikimedia Commons API; contact via GitHub repository)'
COOLDOWN_SECONDS = 7 * 24 * 60 * 60
FORCE_MISSING_REFRESH = os.environ.get('FORCE_MISSING_PHOTO_REFRESH', '').lower() in ('1','true','yes','on')
MANIFEST_PATH = PHOTO_DIR / 'manifest.json'

# Manually verified Wikimedia Commons file pages for destinations where broad search
# previously selected unrelated results or returned empty results. Exact file titles
# are resolved through the Commons API and their attribution/licence metadata is kept.
CURATED_FILE_TITLES = {
 't7': ['File:Tokyo Tower close up 1.jpg', 'File:Tokyo Tower close up 2.jpg', 'File:Tokyo tower.jpg'],
 't8': ['File:The iconic Godzilla in Shinjuku area, Tokyo, Japan.jpg', 'File:Godzilla in Shinjuku (53416845058).jpg', 'File:The iconic Godzilla in Shinjuku area, Tokyo, Japan1.jpg'],
 't9': ['File:Magnet by Shibuya 109 in Shibuya Crossing in Tokyo, 2019 - 784.jpg', 'File:MAGNET by SHIBUYA109 Shibuya Crossing (49997446076).jpg', 'File:MAGNET by SHIBUYA109 (49997450386).jpg'],
 't10': ['File:Suga Shrine staircase, 9 December 2024.jpg', 'File:Suga Shrine stairs low-angle 20161113-071158.jpg', 'File:Suga Shrine stairs high-angle 20161113-070754.jpg'],
}
# Do not use the Taiwan store photo for the Tokyo destination. We instead use verified,
# openly licensed photographs of the correct MAGNET by SHIBUYA109 building/exterior context.
# These are explicitly location-reference photos, not claimed to be store-interior images.
KNOWN_NO_VERIFIED_MATCH = {}

QUERY_VARIANTS = {
 't1':['Sensō-ji temple Asakusa Tokyo'], 't2':['Kaminarimon Thunder Gate Asakusa Tokyo'],
 't3':['Nakamise shopping street Asakusa Tokyo'], 't4':['Meiji Jingu shrine Tokyo'],
 't5':['Shibuya Scramble Crossing Tokyo'], 't6':['Hachiko statue Shibuya Tokyo'],
 't7':['Tokyo Tower Japan'], 't8':['Godzilla Head Hotel Gracery Shinjuku Tokyo','新宿 ゴジラヘッド ホテルグレイスリー'],
 't9':['麦わらストア 渋谷パルコ ワンピース','ONE PIECE Mugiwara Store Shibuya PARCO','ワンピース 麦わらストア 東京'],
 't10':['Suga Shrine stairs Yotsuya Tokyo Your Name','須賀神社 男坂 君の名は 四谷'],
 't11':['Warner Bros Studio Tour Tokyo Making Harry Potter'], 'f1':['Lake Kawaguchiko Mount Fuji Japan'],
 'f2':['Lake Ashi Motohakone Hakone Japan'], 'f3':['Hakone Shrine lake torii Japan'],
 'k1':['Fushimi Inari Taisha red torii Kyoto'], 'k2':['Kiyomizu dera temple Kyoto'],
 'k3':['Ninenzaka street Kyoto'], 'k4':['Sannenzaka street Kyoto'], 'k5':['Yasaka Pagoda Hokanji Kyoto'],
 'k6':['Gion district Kyoto traditional street'], 'k7':['Yasaka Shrine Kyoto'],
 'k8':['Arashiyama Bamboo Grove Kyoto'], 'k9':['Togetsukyo Bridge Arashiyama Kyoto'],
 'k10':['Kinkakuji Golden Pavilion Kyoto'], 'k11':['Nishiki Market Kyoto'],
 'o1':['Osaka Castle park exterior'], 'o2':['Hokoku Shrine Osaka Castle Park','大阪城公園 豊國神社'],
 'o3':['Dotonbori canal Glico sign Osaka'], 'x1':['Shibuya Sky observation deck Tokyo'],
 'x2':['Maruyama Park Kyoto'], 'x3':['Shinsaibashi shopping street Osaka'],
 'x4':['Takeshita Street Harajuku Tokyo'], 'x5':['Namba Yasaka Shrine Osaka lion head'],
 'x6':['Nijo Castle Kyoto'], 'x7':['Pontocho Alley Kyoto']
}

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def clean_html(value: str) -> str:
    value = re.sub(r'<[^>]+>', '', value or '')
    return re.sub(r'\s+', ' ', value).strip()

def get_json(url: str) -> dict:
    for attempt in range(6):
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code != 429 and e.code not in (500, 502, 503, 504):
                raise
            retry_after = e.headers.get('Retry-After')
            delay = int(retry_after) if retry_after and retry_after.isdigit() else min(12 * (2 ** attempt), 120)
            if attempt == 5:
                raise
            print(f'WARN HTTP {e.code}; retrying Commons search in {delay}s (attempt {attempt + 1}/6)')
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 5:
                raise
            delay = min(4 * (2 ** attempt), 45)
            print(f'WARN network error; retrying in {delay}s (attempt {attempt + 1}/6): {e}')
            time.sleep(delay)
    return {}

def queries_for(place: dict) -> list[str]:
    return QUERY_VARIANTS.get(place['id'], [f"{place['name']} {place['area']} Japan"])

def local_asset_exists(item: dict) -> bool:
    thumb = str(item.get('thumb') or '')
    if not thumb.startswith('./assets/photos/'):
        return False
    rel = thumb[2:]
    path = (DIST / rel).resolve()
    try:
        path.relative_to((DIST / 'assets' / 'photos').resolve())
    except ValueError:
        return False
    return path.is_file() and path.stat().st_size > 1000

def load_previous() -> tuple[dict, dict]:
    try:
        raw = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
        if not isinstance(raw, dict):
            raw = {}
    except (OSError, json.JSONDecodeError):
        raw = {}
    meta = raw.get('_meta') if isinstance(raw.get('_meta'), dict) else {}
    return raw, meta

def search_curated_images(place: dict) -> list[dict]:
    titles = CURATED_FILE_TITLES.get(place['id'], [])
    if not titles:
        return []
    params = {'action':'query', 'titles':'|'.join(titles), 'prop':'imageinfo',
              'iiprop':'url|extmetadata', 'iiurlwidth':1000, 'format':'json'}
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    data = get_json(url)
    pages = data.get('query', {}).get('pages', {})
    by_title = {str(v.get('title','')).casefold(): v for v in pages.values()}
    picked = []
    for requested in titles:
        page = by_title.get(requested.casefold())
        if not page or 'missing' in page:
            print(f"WARN curated Commons file not found for {place['id']}: {requested}")
            continue
        ii = (page.get('imageinfo') or [{}])[0]
        thumb, source = ii.get('thumburl'), ii.get('descriptionurl')
        if not thumb or not source or not thumb.lower().split('?')[0].endswith(('.jpg','.jpeg','.png','.webp')):
            print(f"WARN curated Commons file has no usable image URL for {place['id']}: {requested}")
            continue
        ext = ii.get('extmetadata') or {}
        title = str(page.get('title', requested)).replace('File:','').replace('_',' ')
        description = clean_html((ext.get('ImageDescription') or {}).get('value',''))
        picked.append({'title':title, 'url':thumb, 'source':source,
            'author':clean_html((ext.get('Artist') or {}).get('value','Unknown author')),
            'license':clean_html((ext.get('LicenseShortName') or {}).get('value','See source page')),
            'licenseUrl':(ext.get('LicenseUrl') or {}).get('value',''), 'description':description})
    return picked

def search_images(place: dict) -> list[dict]:
    for query in queries_for(place):
        params = {'action':'query','generator':'search','gsrsearch':'filetype:bitmap ' + query,
                  'gsrnamespace':6,'gsrlimit':16,'prop':'imageinfo','iiprop':'url|extmetadata',
                  'iiurlwidth':1000,'format':'json'}
        url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
        time.sleep(1.5)
        try:
            data = get_json(url)
        except Exception as e:
            print(f"WARN Commons search failed for {place['id']} ({query}): {e}")
            continue
        pages = list((data.get('query', {}).get('pages') or {}).values())
        wanted = [w.lower() for w in re.findall(r'[a-z0-9]+', query) if len(w) > 3]
        results = []
        for page in pages:
            ii = (page.get('imageinfo') or [{}])[0]
            url_thumb, source = ii.get('thumburl'), ii.get('descriptionurl')
            if not url_thumb or not source or not url_thumb.lower().split('?')[0].endswith(('.jpg','.jpeg','.png','.webp')):
                continue
            title = page.get('title','Photo').replace('File:','').replace('_',' ')
            ext = ii.get('extmetadata') or {}
            description = clean_html((ext.get('ImageDescription') or {}).get('value',''))
            text = (title + ' ' + description).lower()
            score = sum(1 for word in wanted if word in text)
            if score < 1:
                continue
            results.append((score, {'title':title,'url':url_thumb,'source':source,
                'author':clean_html((ext.get('Artist') or {}).get('value','Unknown author')),
                'license':clean_html((ext.get('LicenseShortName') or {}).get('value','See source page')),
                'licenseUrl':(ext.get('LicenseUrl') or {}).get('value',''), 'description':description}))
        results.sort(key=lambda x:x[0], reverse=True)
        picked, seen = [], set()
        for _, item in results:
            norm = re.sub(r'[^a-z0-9]','',item['title'].lower())
            if norm in seen:
                continue
            seen.add(norm); picked.append(item)
            if len(picked) >= 3:
                break
        if picked:
            return picked
    return []

def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={'User-Agent':UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = r.read()
    if len(data) < 4000:
        raise ValueError('download unexpectedly small')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

def write_manifest(manifest: dict, meta: dict) -> None:
    manifest['_meta'] = meta
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')

def build() -> int:
    print(f'FORCE_MISSING_PHOTO_REFRESH={FORCE_MISSING_REFRESH}')
    previous, old_meta = load_previous()
    meta = dict(old_meta)
    version_file = ROOT / 'scripts' / 'photo-cache-version.txt'
    curation_version = version_file.read_text(encoding='utf-8').strip() if version_file.exists() else '1'
    previous_curation_version = str(meta.get('curationVersion') or '')
    last_attempt = dict(meta.get('lastAttempt') or {})
    manifest = {}
    forced_ids = []
    skipped_cached = 0
    queried = 0
    for place in PLACES:
        pid = place['id']
        old_items = previous.get(pid, [])
        valid = [item for item in old_items if isinstance(item, dict) and local_asset_exists(item)] if isinstance(old_items, list) else []
        # For curated destinations, invalidate any previous bundle whose filenames do not
        # match the reviewed allowlist; this corrects the earlier Tokyo Tower mismatches.
        allowed = {x.removeprefix('File:').casefold() for x in CURATED_FILE_TITLES.get(pid, [])}
        needs_recuration = bool(allowed and valid and (previous_curation_version != curation_version or any(str(item.get('title','')).casefold() not in allowed for item in valid)))
        if needs_recuration:
            reason = 'curation version changed' if previous_curation_version != curation_version else 'cached titles are outside the reviewed allowlist'
            print(f'RECURATE {pid}: {reason}; replacing cached selection')
            valid = []
        if pid in KNOWN_NO_VERIFIED_MATCH:
            manifest[pid] = []
            print(f"SKIP {pid}: {KNOWN_NO_VERIFIED_MATCH[pid]}")
            last_attempt[pid] = now_iso()
            meta['lastAttempt'] = last_attempt
            write_manifest(manifest | {k:v for k,v in previous.items() if k not in manifest and k != '_meta'}, meta)
            continue
        if valid:
            manifest[pid] = valid
            skipped_cached += len(valid)
            print(f'SKIP {pid}: reused {len(valid)} bundled photo(s); no download needed')
            continue
        attempted = last_attempt.get(pid)
        recent = False
        if attempted and not FORCE_MISSING_REFRESH and pid not in CURATED_FILE_TITLES:
            try:
                dt = datetime.fromisoformat(attempted.replace('Z','+00:00'))
                recent = (datetime.now(timezone.utc)-dt).total_seconds() < COOLDOWN_SECONDS
            except (ValueError, TypeError):
                recent = False
        if recent:
            manifest[pid] = []
            print(f'SKIP {pid}: no saved photos; recent failed/empty search is in 7-day cooldown')
            continue
        queried += 1
        if FORCE_MISSING_REFRESH:
            forced_ids.append(pid)
        print(f'SEARCH {pid}: looking for missing bundled photos')
        if pid in CURATED_FILE_TITLES:
            try:
                picked = search_curated_images(place)
            except Exception as e:
                print(f"WARN curated Commons lookup failed for {pid}: {e}")
                picked = []
        else:
            picked = search_images(place)
        saved = []
        for j, item in enumerate(picked, 1):
            ext = '.webp' if '.webp' in item['url'].lower() else '.png' if '.png' in item['url'].lower() else '.jpg'
            rel = f'assets/photos/{pid}-{j}{ext}'
            try:
                download(item['url'], DIST / rel)
                saved.append({'title':item['title'],'thumb':'./'+rel,'page':item['source'],
                    'author':item['author'] or 'Unknown author','license':item['license'],
                    'licenseUrl':item['licenseUrl'],'description':item['description']})
                print(f"OK {pid}: {item['title']}")
            except Exception as e:
                print(f'WARN image download failed for {pid}: {e}')
            time.sleep(0.5)
        manifest[pid] = saved
        last_attempt[pid] = now_iso()
        if not saved:
            print(f'WARN no bundled photos for {pid}; online archive fallback remains available')
        # Persist progress during the build so a later failure doesn't lose all work.
        meta['lastAttempt'] = last_attempt
        write_manifest(manifest | {k:v for k,v in previous.items() if k not in manifest and k != '_meta'}, meta)
    meta['lastAttempt'] = last_attempt
    meta['curationVersion'] = curation_version
    write_manifest(manifest, meta)
    total = sum(len(v) for k,v in manifest.items() if k != '_meta' and isinstance(v,list))
    missing = [p['id'] for p in PLACES if not manifest.get(p['id'])]
    print(f'Bundled photos: {total} across {len(PLACES)} places')
    print(f'Reused cached photos: {skipped_cached}; destination searches this run: {queried}; missing bundles: {len(missing)}')
    if missing:
        print('Missing bundle IDs:', ', '.join(missing))
        retryable = [pid for pid in missing if pid not in KNOWN_NO_VERIFIED_MATCH]
        if retryable:
            print('Retryable missing IDs:', ', '.join(retryable))
            print('To retry these only, run the workflow manually with retry_missing_photos enabled.')
        for pid in missing:
            if pid in KNOWN_NO_VERIFIED_MATCH:
                print(f'No automatic retry scheduled for {pid}: {KNOWN_NO_VERIFIED_MATCH[pid]}')
    return 0

if __name__ == '__main__':
    raise SystemExit(build())
