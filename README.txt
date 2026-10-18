JAPAN ATLAS PRO — PHOTO-BUNDLED GITHUB PAGES DEPLOYMENT

What this build does
- Keeps the interactive MapLibre / OpenFreeMap map (online map tiles still require internet).
- Adds a GitHub Actions build that downloads up to three reusable, attribution-bearing Wikimedia Commons photos per destination before publishing.
- The published site serves bundled photos from its own assets folder, so galleries no longer depend on a live Commons search for the normal case.
- Records source page, author and licence metadata for each downloaded photo. Review attribution/licence terms before republishing beyond this personal planner.
- If Commons has no suitable result or a download fails, the app can still use its existing online-search fallback.

IMPORTANT DEPLOYMENT CHANGE
This package uses GitHub Actions to build the site and bundle images. In your repository, upload/commit the package files including:
  .github/workflows/pages.yml
  scripts/download_photos.py
  places.json
  index.html
  sw.js
  manifest.webmanifest
  icon.svg

Then open repository Settings > Pages and set Build and deployment > Source to "GitHub Actions" (not "Deploy from a branch"). The workflow runs on pushes to main and can be started manually from Actions.

On iPhone, GitHub mobile may make hidden files/folders awkward to upload. The easiest reliable option is GitHub's web interface in desktop-site mode or uploading the ZIP from a computer. Make sure .github/workflows/pages.yml is actually present in the repository at that exact path; without it, photo bundling will not run.

Image bundle size depends on Commons results. The build downloads up to three 1000px-wide thumbnails per place (35 places), so expect a larger published site than the previous HTML-only version. Images are selected automatically from Commons search, not individually hand-curated; inspect them and their licences if exact visual matching matters.

Privacy and limits
- This is a public static site. Do not commit private information or API secrets.
- Planner edits are local to each visitor's browser; they are not synced between people.
- The photo gallery is bundled by the GitHub-hosted build, but map tiles and Google Maps navigation still need internet. This is not a complete offline street-map package.
