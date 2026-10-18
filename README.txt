JAPAN ATLAS PRO — PHOTO REPAIR UPDATE (v3)

WHY THIS UPDATE
The prior bundle had a curated list for Suga Shrine stairs, but cache reuse did not always invalidate a previously published photo manifest when the curation version changed. This update bumps the photo cache version and makes the downloader re-curate allowlisted destinations when the manifest curation version is stale. It refreshes only curated Tokyo destinations (Tokyo Tower, Godzilla Head, MAGNET location references, and Suga Shrine stairs); the other saved destination bundles are retained. The service worker cache is also bumped so the new UI can load.

MUGIWARA STORE
The official Shibuya main store listing currently places the shop inside MAGNET by SHIBUYA109 on the 6th floor, not Shibuya PARCO. The bundled photos are openly licensed photos of the building/location, not claimed to show the store interior. The UI says this explicitly. No Taiwan-store image is used.

FILES TO REPLACE IN YOUR EXISTING GITHUB REPOSITORY
- index.html
- sw.js
- scripts/download_photos.py
- scripts/photo-cache-version.txt
- tests/test_download_photos.py (recommended)

Keep places.json, .github/workflows/pages.yml, manifest.webmanifest, and icon.svg unchanged. Do not upload this folder as a new nested folder; replace the matching files at their existing paths. Commit the changes to main. The changed cache version makes Actions restore the previous bundle and re-curate only the allowlisted destination photo sets.

VALIDATION
- Python unit tests: 9 passed.
- Python compile: passed.
- Inline JavaScript syntax: passed (4 blocks).
- ZIP integrity: checked after creation.
- This environment cannot run the GitHub Actions network downloader against Wikimedia or visually verify the live iPhone browser. After commit, inspect the build log for RECURATE/SEARCH on t7, t8, t9, and t10 and confirm a non-empty manifest for t10. A green build alone does not prove that every image loaded.
