JAPAN ATLAS PRO — MOUNT FUJI PIN + PHOTO UPDATE (v5)

WHAT THIS ADDS
- A dedicated map pin named “Mount Fuji (landmark pin)” at Mount Fuji itself.
- Three curated Wikimedia Commons photo candidates for the Mount Fuji gallery, with creator/licence metadata kept in the generated manifest.
- A local-storage migration that merges newly added default destinations into an existing saved planner without deleting the user's saved edits.
- Photo cache version 5 and service-worker cache v16 to prompt a fresh bundle and client shell.

PRIOR TRIP DECISIONS RESTORED FROM THE EARLIER PLANNING LOG
- Mount Fuji is a confirmed trip goal.
- Day 5 remains a route decision: Lake Kawaguchiko OR Hakone/Lake Ashi, not both.
- Hakone Cedar Avenue and Owakudani stay removed.
- Nara Park/Todai-ji and Kamogawa River stay removed.
- Maruyama Park and Shinsaibashi-suji remain optional only.
- Shibuya Sky remains optional; Tokyo Tower is the selected main tower.
- The Fuji pin is a landmark reference, not a claim that the summit is a winter-accessible visit. The photos show Mount Fuji from viewpoints and do not guarantee visibility in January.

FILES TO REPLACE IN YOUR EXISTING GITHUB REPOSITORY
- index.html
- places.json
- sw.js
- scripts/download_photos.py
- scripts/photo-cache-version.txt
- tests/test_download_photos.py

Keep .github/workflows/pages.yml, manifest.webmanifest, icon.svg, and scripts/seed_published_photos.py unchanged.
Replace each file at the same path in the existing repository; do not upload this folder as a nested folder. Commit to main and wait for GitHub Actions.

WHAT TO CHECK IN THE ACTIONS LOG
- It should show RECURATE/SEARCH for f0 and SEARCH/RECURATE for curated photo sets where cache version changed.
- It should report at least one successfully downloaded image for f0 and include f0 in dist/assets/photos/manifest.json.
- A green deployment alone is not enough: open the site in Incognito, open the Fuji landmark pin/place, and confirm the gallery renders. The build needs network access to Wikimedia Commons to fetch the curated images.

VALIDATION PERFORMED HERE
- 11 Python unit tests passed.
- Python compilation passed.
- Inline JavaScript syntax checks passed.
- ZIP integrity check passed.
- Live GitHub Actions download and live iPhone rendering cannot be executed from this local workspace, so those remain deployment checks.
