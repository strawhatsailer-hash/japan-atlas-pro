#!/usr/bin/env python3
"""Build-time photo bundler for Japan Atlas Pro using Wikimedia Commons.
Downloads up to three relevant, reusable thumbnail images per destination,
with source, author and licence metadata recorded in the generated manifest.
"""
import json, os, re, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
PHOTO_DIR = DIST / 'assets' / 'photos'
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
PLACES = json.loads((ROOT / 'places.json').read_text(encoding='utf-8'))
UA = 'JapanAtlasProPhotoBundler/1.0 (personal travel planner; Wikimedia Commons API)'

def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def clean_html(value):
    value = re.sub(r'<[^>]+>', '', value or '')
    return re.sub(r'\s+', ' ', value).strip()

def query_for(p):
    overrides = {
      't1':'Sensō-ji temple Asakusa Tokyo', 't2':'Kaminarimon Thunder Gate Asakusa Tokyo',
      't3':'Nakamise shopping street Asakusa Tokyo', 't4':'Meiji Jingu shrine Tokyo',
      't5':'Shibuya Scramble Crossing Tokyo', 't6':'Hachiko statue Shibuya Tokyo',
      't7':'Tokyo Tower Japan', 't8':'Godzilla head Hotel Gracery Shinjuku',
      't9':'ONE PIECE Mugiwara Store Shibuya PARCO', 't10':'Suga Shrine stairs Yotsuya Tokyo Your Name',
      't11':'Warner Bros Studio Tour Tokyo Making Harry Potter', 'f1':'Lake Kawaguchiko Mount Fuji Japan',
      'f2':'Lake Ashi Motohakone Hakone Japan', 'f3':'Hakone Shrine lake torii Japan',
      'k1':'Fushimi Inari Taisha red torii Kyoto', 'k2':'Kiyomizu dera temple Kyoto',
      'k3':'Ninenzaka street Kyoto', 'k4':'Sannenzaka street Kyoto', 'k5':'Yasaka Pagoda Hokanji Kyoto',
      'k6':'Gion district Kyoto traditional street', 'k7':'Yasaka Shrine Kyoto',
      'k8':'Arashiyama Bamboo Grove Kyoto', 'k9':'Togetsukyo Bridge Arashiyama Kyoto',
      'k10':'Kinkakuji Golden Pavilion Kyoto', 'k11':'Nishiki Market Kyoto',
      'o1':'Osaka Castle park exterior', 'o2':'Hokoku Shrine Osaka Castle Park', 'o3':'Dotonbori canal Glico sign Osaka',
      'x1':'Shibuya Sky observation deck Tokyo', 'x2':'Maruyama Park Kyoto',
      'x3':'Shinsaibashi shopping street Osaka', 'x4':'Takeshita Street Harajuku Tokyo',
      'x5':'Namba Yasaka Shrine Osaka lion head', 'x6':'Nijo Castle Kyoto', 'x7':'Pontocho Alley Kyoto'
    }
    return overrides.get(p['id'], p['name'] + ' ' + p['area'] + ' Japan')

def search_images(p):
    query = query_for(p)
    params = {'action':'query','generator':'search','gsrsearch':'filetype:bitmap ' + query,
              'gsrnamespace':6,'gsrlimit':16,'prop':'imageinfo','iiprop':'url|extmetadata',
              'iiurlwidth':1000,'format':'json'}
    url = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)
    try:
        data = get_json(url)
    except Exception as e:
        print(f"WARN Commons search failed for {p['id']}: {e}")
        return []
    pages = list((data.get('query',{}).get('pages') or {}).values())
    wanted = [w.lower() for w in re.findall(r'[a-z0-9]+', query) if len(w)>3]
    results=[]
    for page in pages:
        ii=(page.get('imageinfo') or [{}])[0]
        url=ii.get('thumburl'); source=ii.get('descriptionurl')
        if not url or not source or not url.lower().split('?')[0].endswith(('.jpg','.jpeg','.png','.webp')): continue
        title=page.get('title','Photo').replace('File:','').replace('_',' ')
        ext=ii.get('extmetadata') or {}
        description=clean_html((ext.get('ImageDescription') or {}).get('value',''))
        text=(title+' '+description).lower()
        score=sum(1 for w in wanted if w in text)
        # Prioritise names matching the place; query search itself is relevance-ranked.
        results.append((score, {'title':title,'url':url,'source':source,
          'author':clean_html((ext.get('Artist') or {}).get('value','Unknown author')),
          'license':clean_html((ext.get('LicenseShortName') or {}).get('value','See source page')),
          'licenseUrl':(ext.get('LicenseUrl') or {}).get('value',''),
          'description':description}))
    results.sort(key=lambda x:x[0], reverse=True)
    # avoid near-identical titles; use three to keep total download reasonable
    picked=[]; seen=set()
    for _, item in results:
        norm=re.sub(r'[^a-z0-9]','',item['title'].lower())
        if norm in seen: continue
        seen.add(norm); picked.append(item)
        if len(picked)>=3: break
    return picked

def download(url, path):
    req=urllib.request.Request(url, headers={'User-Agent':UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        data=r.read()
    if len(data)<4000: raise ValueError('download unexpectedly small')
    path.write_bytes(data)

manifest={}
for index,p in enumerate(PLACES):
    pid=p['id']; picked=search_images(p); saved=[]
    for j,item in enumerate(picked,1):
        ext='.webp' if '.webp' in item['url'].lower() else '.jpg'
        rel=f"assets/photos/{pid}-{j}{ext}"
        try:
            download(item['url'], DIST/rel)
            saved.append({'title':item['title'],'thumb':'./'+rel,'page':item['source'],
                          'author':item['author'] or 'Unknown author','license':item['license'],
                          'licenseUrl':item['licenseUrl'],'description':item['description']})
            print(f"OK {pid}: {item['title']}")
        except Exception as e:
            print(f"WARN image download failed for {pid}: {e}")
        time.sleep(0.15)
    manifest[pid]=saved
    if not saved: print(f"WARN no bundled photos for {pid}; runtime online search remains as fallback")
(DIST/'assets'/'photos'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Bundled photos:',sum(len(v) for v in manifest.values()),'across',len(manifest),'places')
