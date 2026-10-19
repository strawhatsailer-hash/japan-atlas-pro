-- Japan Atlas Pro: secure published itinerary snapshots
-- Run this file in Supabase Dashboard > SQL Editor.
create table if not exists public.itinerary_publications (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9-]{6,40}$'),
  title text not null default 'Japan Atlas itinerary',
  snapshot jsonb not null,
  is_latest boolean not null default false,
  owner_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  created_at timestamptz not null default now()
);
create index if not exists itinerary_publications_latest_idx on public.itinerary_publications (is_latest) where is_latest = true;
create index if not exists itinerary_publications_owner_idx on public.itinerary_publications (owner_id);
alter table public.itinerary_publications enable row level security;
drop policy if exists "Anyone can read published itinerary snapshots" on public.itinerary_publications;
create policy "Anyone can read published itinerary snapshots" on public.itinerary_publications for select to anon, authenticated using (true);
revoke insert, update, delete on public.itinerary_publications from anon, authenticated;
grant select on public.itinerary_publications to anon, authenticated;
create or replace function public.publish_japan_itinerary(p_snapshot jsonb, p_slug text, p_title text default 'Japan Atlas itinerary')
returns table (published_slug text, published_at timestamptz) language plpgsql security definer set search_path = '' as $$
declare v_user_id uuid := auth.uid(); v_now timestamptz := now();
begin
  if v_user_id is null then raise exception 'Sign in to publish an itinerary.'; end if;
  if p_snapshot is null or jsonb_typeof(p_snapshot) <> 'object' then raise exception 'A valid itinerary snapshot is required.'; end if;
  if p_slug !~ '^[a-z0-9-]{6,40}$' then raise exception 'Invalid share slug.'; end if;
  if length(coalesce(p_title,'')) < 1 or length(p_title) > 120 then raise exception 'Title must be between 1 and 120 characters.'; end if;
  update public.itinerary_publications set is_latest = false where owner_id = v_user_id and is_latest = true;
  insert into public.itinerary_publications(slug,title,snapshot,is_latest,owner_id,created_at) values (p_slug,p_title,p_snapshot,true,v_user_id,v_now);
  return query select p_slug, v_now;
exception when unique_violation then raise exception 'This share slug already exists. Please publish again to create a new link.';
end; $$;
revoke all on function public.publish_japan_itinerary(jsonb,text,text) from public;
grant execute on function public.publish_japan_itinerary(jsonb,text,text) to authenticated;
