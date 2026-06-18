create table if not exists assets (
  id text primary key,
  label text not null,
  hostname text,
  location text,
  asset_tag text,
  manufacturer text,
  model text,
  serial_number text,
  equipment_type_guess text,
  status text not null default 'active',
  source text not null default 'manual',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists notes (
  id text primary key,
  asset_id text not null references assets(id) on delete cascade,
  body text not null,
  created_at timestamptz not null default now()
);

create table if not exists photos (
  id text primary key,
  asset_id text not null references assets(id) on delete cascade,
  object_key text not null unique,
  filename text not null,
  content_type text not null,
  size_bytes integer not null,
  caption text,
  created_at timestamptz not null default now()
);

create table if not exists ai_analysis_jobs (
  id text primary key,
  asset_id text not null references assets(id) on delete cascade,
  photo_id text references photos(id) on delete set null,
  object_key text,
  status text not null default 'queued',
  model text,
  prompt_version text,
  result jsonb,
  error text,
  attempts integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table ai_analysis_jobs add column if not exists photo_id text references photos(id) on delete set null;
alter table ai_analysis_jobs add column if not exists object_key text;
alter table ai_analysis_jobs add column if not exists attempts integer not null default 0;

create index if not exists idx_assets_created_at on assets(created_at desc);
create index if not exists idx_photos_asset_id on photos(asset_id);
create index if not exists idx_notes_asset_id on notes(asset_id);
create index if not exists idx_ai_analysis_jobs_asset_id on ai_analysis_jobs(asset_id);
create index if not exists idx_ai_analysis_jobs_photo_id on ai_analysis_jobs(photo_id);
create index if not exists idx_ai_analysis_jobs_status_created_at on ai_analysis_jobs(status, created_at);
