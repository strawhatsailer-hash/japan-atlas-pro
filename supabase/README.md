# Japan Atlas Pro — Supabase publishing setup

This folder contains the database setup for published itinerary snapshots. Never place a Supabase secret/service-role key in the public GitHub Pages site.

## One-time setup
1. Create a Supabase project.
2. Open SQL Editor → New query, paste `schema.sql`, and run it.
3. Keep email/password sign-in enabled. After creating your own account, disable public sign-ups.
4. In Authentication → Users, create a publisher account using an email address you control.
5. In Project Settings → API Keys, copy the Project URL and the Publishable key (starts with `sb_publishable_`). Do not use the secret key.
6. Configure the front end with only the Project URL and publishable key. Publishing must require a signed-in user.

## Security model
- Published snapshots are publicly readable so visitors can open them without signing in.
- Direct browser inserts, updates, and deletes are revoked.
- Publishing uses `publish_japan_itinerary`, which requires an authenticated user and creates an immutable snapshot marked as latest.
- Old share slugs remain valid and retain their original snapshots.
- Never put database passwords or secret/service-role keys in `index.html`, GitHub, a public issue, or this chat.

## Planned URL behavior
- The normal site URL loads the latest published snapshot when one exists.
- A short URL such as `?trip=abc123xyz` opens that immutable snapshot.
- Publishing requires the owner to sign in. The browser never receives elevated database credentials.

Do not treat this as complete until the front end is configured with your project URL/publishable key and the full publish/read flow has been tested.
