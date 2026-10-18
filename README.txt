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
