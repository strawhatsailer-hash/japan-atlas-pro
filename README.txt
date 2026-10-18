JAPAN ATLAS PRO — GITHUB PAGES DEPLOYMENT

Files
- index.html: main planner app
- manifest.webmanifest + icon.svg: installable PWA metadata
- sw.js: caches the app shell after the first successful visit (cache version v2; updates older cached copies)

Deploy all four files at the ROOT of your GitHub Pages repository. Commit changes to main. Wait for GitHub Pages to publish, then open https://YOUR-USERNAME.github.io/REPOSITORY-NAME/ and refresh.

On iPhone: open the HTTPS website in Safari/Edge. In Safari, Share → Add to Home Screen may install it as an app-like shortcut.

Offline limits: the planner shell and data saved in this browser may be available after the first successful visit. Live MapLibre style files, map tiles, Google Maps directions and any online routing remain online-dependent and are intentionally not cached. This is not a full offline street-map package.

Data privacy: this is a static public website. Avoid storing private personal data in the source repository. Place edits are saved to browser localStorage; export a JSON backup periodically.

Recent UX update: the primary map style is OpenFreeMap Liberty (more colourful than Positron). The Atlas has a Map style toggle to switch between Colour and Soft styles. Destination markers use city colours and category emoji. The route builder defaults to two different places when both selectors were initially identical.

Important: live vector tiles require internet. This package does not include offline street-map tiles.


UX refresh: selected-place inspector now loads a horizontal gallery of multiple reference photos from Wikimedia Commons when online. Each photo links to its Commons source page for attribution/licence details. Image results depend on Commons search availability and should be visually checked before relying on a specific image. The nearby places list shows a thumbnail when photos have loaded. The app remains usable if photo search is unavailable.


Latest update: place navigation now searches using the human-readable place name and address rather than only raw coordinates. The route builder also sends readable place names/addresses to Google Maps. Place inspector photo galleries use staged Wikimedia Commons searches and show image source/licence links; photo loading requires internet.

Latest update: navigation searches by human-readable place name/address rather than raw coordinates. Route builder uses readable place labels. Photo galleries use staged Wikimedia Commons searches and link to source/licence details; photo loading requires internet.
