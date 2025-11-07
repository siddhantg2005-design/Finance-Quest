-- Finance Quest — Supabase/Postgres Schema
-- UUID PKs, jsonb badges, timestamps, soft-delete flags, FKs, indexes, and seed data.
-- Paste into Supabase SQL Editor.

-- Ensure UUID generation is available (Supabase includes pgcrypto by default)
create extension if not exists pgcrypto;

-- Utility trigger to maintain updated_at on row updates
create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

--------------------------------------------------------------------------------
-- USERS: Mirror of Supabase auth.users (1:1 by id). Keep minimal columns.
--------------------------------------------------------------------------------
create table if not exists public.users (
  -- PK mirrors auth.users.id
  id uuid primary key
    references auth.users(id) on delete cascade,
  -- Record creation timestamp
  created_at timestamptz not null default now(),
  -- Record last update timestamp
  updated_at timestamptz not null default now(),
  -- Soft delete flag (do not hard-delete for auditability)
  is_deleted boolean not null default false
);

comment on table public.users is 'Application users mapping 1:1 to auth.users (by id).';
comment on column public.users.id is 'UUID primary key mirroring auth.users.id.';
comment on column public.users.created_at is 'Row creation timestamp.';
comment on column public.users.updated_at is 'Row last update timestamp.';
comment on column public.users.is_deleted is 'Soft delete flag; when true, row is considered deleted.';

create trigger trg_users_updated_at
before update on public.users
for each row execute function set_updated_at();

--------------------------------------------------------------------------------
-- PROFILES: User profile + progression (xp, level, badges)
--------------------------------------------------------------------------------
create table if not exists public.profiles (
  -- Surrogate PK for profiles
  id uuid primary key default gen_random_uuid(),
  -- FK to users (unique: one profile per user)
  user_id uuid not null unique
    references public.users(id) on delete cascade,
  -- Total experience points
  xp integer not null default 0,
  -- Gamified level
  level integer not null default 1,
  -- Badges as JSONB (array or object per product needs)
  badges jsonb not null default '[]'::jsonb,
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Soft delete
  is_deleted boolean not null default false
);

comment on table public.profiles is 'Per-user profile: XP, level, badges.';
comment on column public.profiles.id is 'UUID primary key for profile.';
comment on column public.profiles.user_id is 'FK to users.id; unique to enforce 1:1.';
comment on column public.profiles.xp is 'Accumulated experience points.';
comment on column public.profiles.level is 'Computed/assigned level based on XP.';
comment on column public.profiles.badges is 'jsonb list/object of awarded badges.';
comment on column public.profiles.created_at is 'Row creation timestamp.';
comment on column public.profiles.updated_at is 'Row last update timestamp.';
comment on column public.profiles.is_deleted is 'Soft delete flag.';

create index if not exists idx_profiles_user_id on public.profiles (user_id);
create index if not exists idx_profiles_badges_gin on public.profiles using gin (badges);

create trigger trg_profiles_updated_at
before update on public.profiles
for each row execute function set_updated_at();

--------------------------------------------------------------------------------
-- TRANSACTIONS: Financial transactions per user
--------------------------------------------------------------------------------
create table if not exists public.transactions (
  -- PK
  id uuid primary key default gen_random_uuid(),
  -- Owner
  user_id uuid not null
    references public.users(id) on delete cascade,
  -- Monetary amount (expenses negative or positive? convention: positive outflow by default)
  amount numeric(12,2) not null,
  -- ISO 4217 currency code (e.g., USD, INR)
  currency char(3) not null default 'USD',
  -- Category label (simple text; can be normalized later)
  category text,
  -- Optional freeform description/merchant
  description text,
  -- When the transaction occurred
  occurred_at timestamptz not null,
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Soft delete
  is_deleted boolean not null default false
);

comment on table public.transactions is 'User financial transactions.';
comment on column public.transactions.id is 'UUID primary key for transaction.';
comment on column public.transactions.user_id is 'FK to users.id (owner).';
comment on column public.transactions.amount is 'Amount (numeric(12,2)).';
comment on column public.transactions.currency is 'ISO 4217 currency code.';
comment on column public.transactions.category is 'Transaction category label.';
comment on column public.transactions.description is 'Transaction description/merchant.';
comment on column public.transactions.occurred_at is 'Timestamp when transaction occurred.';
comment on column public.transactions.created_at is 'Row creation timestamp.';
comment on column public.transactions.updated_at is 'Row last update timestamp.';
comment on column public.transactions.is_deleted is 'Soft delete flag.';

create index if not exists idx_transactions_user_occurred_at
  on public.transactions (user_id, occurred_at desc);

create index if not exists idx_transactions_user_category
  on public.transactions (user_id, category);

create index if not exists idx_transactions_created_at
  on public.transactions (created_at desc);

create trigger trg_transactions_updated_at
before update on public.transactions
for each row execute function set_updated_at();

--------------------------------------------------------------------------------
-- GOALS: Savings/budget goals per user
--------------------------------------------------------------------------------
create table if not exists public.goals (
  -- PK
  id uuid primary key default gen_random_uuid(),
  -- Owner
  user_id uuid not null
    references public.users(id) on delete cascade,
  -- Goal name/title
  name text not null,
  -- Target amount for the goal
  target_amount numeric(12,2) not null,
  -- Current accumulated amount toward the goal
  current_amount numeric(12,2) not null default 0,
  -- Optional deadline date for the goal
  deadline date,
  -- Status lifecycle
  status text not null default 'active' check (status in ('active','paused','completed','archived')),
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Soft delete
  is_deleted boolean not null default false
);

comment on table public.goals is 'User goals (savings/budget) with target amounts and status.';
comment on column public.goals.id is 'UUID primary key for goal.';
comment on column public.goals.user_id is 'FK to users.id (owner).';
comment on column public.goals.name is 'Goal display name.';
comment on column public.goals.target_amount is 'Target amount to reach.';
comment on column public.goals.current_amount is 'Current progress toward target.';
comment on column public.goals.deadline is 'Optional due date.';
comment on column public.goals.status is 'State: active|paused|completed|archived.';
comment on column public.goals.created_at is 'Row creation timestamp.';
comment on column public.goals.updated_at is 'Row last update timestamp.';
comment on column public.goals.is_deleted is 'Soft delete flag.';

create index if not exists idx_goals_user_status
  on public.goals (user_id, status);

create index if not exists idx_goals_deadline
  on public.goals (deadline);

create trigger trg_goals_updated_at
before update on public.goals
for each row execute function set_updated_at();

--------------------------------------------------------------------------------
-- XP LOG: Audit trail of XP changes (e.g., completing quests, streaks)
--------------------------------------------------------------------------------
create table if not exists public.xp_log (
  -- PK
  id uuid primary key default gen_random_uuid(),
  -- Owner
  user_id uuid not null
    references public.users(id) on delete cascade,
  -- Increment/decrement of XP (can be negative on penalty)
  xp_delta integer not null,
  -- Human-readable reason/category (e.g., 'add_transaction', 'streak_bonus')
  reason text not null,
  -- Optional linkage to a related entity type (e.g., 'transaction', 'goal')
  related_entity_type text,
  -- Optional related entity id (UUID from the related table)
  related_entity_id uuid,
  -- Timestamps
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  -- Soft delete
  is_deleted boolean not null default false
);

comment on table public.xp_log is 'Immutable/auditable log of XP adjustments per user.';
comment on column public.xp_log.id is 'UUID primary key for xp log row.';
comment on column public.xp_log.user_id is 'FK to users.id (owner).';
comment on column public.xp_log.xp_delta is 'XP change (positive or negative).';
comment on column public.xp_log.reason is 'Reason code/text for the XP change.';
comment on column public.xp_log.related_entity_type is 'Optional type of related entity.';
comment on column public.xp_log.related_entity_id is 'Optional UUID of related entity.';
comment on column public.xp_log.created_at is 'Row creation timestamp.';
comment on column public.xp_log.updated_at is 'Row last update timestamp.';
comment on column public.xp_log.is_deleted is 'Soft delete flag.';

create index if not exists idx_xp_log_user_created_at
  on public.xp_log (user_id, created_at desc);

create index if not exists idx_xp_log_reason
  on public.xp_log (reason);

create trigger trg_xp_log_updated_at
before update on public.xp_log
for each row execute function set_updated_at();

--------------------------------------------------------------------------------
-- Example Seed Data
-- NOTE: Replace the two UUIDs below with real IDs from auth.users to satisfy the FK.
--------------------------------------------------------------------------------

-- Example auth-linked user IDs (replace with real auth.users IDs)
-- User A and User B
with seed as (
  select
    '11111111-1111-1111-1111-111111111111'::uuid as user_a,
    '22222222-2222-2222-2222-222222222222'::uuid as user_b
)
insert into public.users (id)
select user_a from seed
on conflict (id) do nothing;

with seed as (
  select
    '11111111-1111-1111-1111-111111111111'::uuid as user_a,
    '22222222-2222-2222-2222-222222222222'::uuid as user_b
)
insert into public.users (id)
select user_b from seed
on conflict (id) do nothing;

-- Profiles for the two users
insert into public.profiles (user_id, xp, level, badges)
values
  ('11111111-1111-1111-1111-111111111111', 120, 3, '[{"code":"first_tx","awarded_at":"2025-01-01"}]'::jsonb),
  ('22222222-2222-2222-2222-222222222222', 40, 1,  '[]'::jsonb)
on conflict (user_id) do nothing;

-- Six transactions (3 per user)
insert into public.transactions (user_id, amount, currency, category, description, occurred_at)
values
  -- User A
  ('11111111-1111-1111-1111-111111111111',  -45.50, 'USD', 'Food',       'Groceries',               now() - interval '10 days'),
  ('11111111-1111-1111-1111-111111111111',  -12.99, 'USD', 'Transport',  'Bus pass',               now() - interval '7 days'),
  ('11111111-1111-1111-1111-111111111111', -150.00, 'USD', 'Utilities',  'Electricity bill',       now() - interval '3 days'),
  -- User B
  ('22222222-2222-2222-2222-222222222222', -200.00, 'USD', 'Rent',       'Monthly rent partial',   now() - interval '15 days'),
  ('22222222-2222-2222-2222-222222222222',  -18.75, 'USD', 'Food',       'Lunch',                  now() - interval '5 days'),
  ('22222222-2222-2222-2222-222222222222',  -30.00, 'USD', 'Health',     'Pharmacy',               now() - interval '2 days');

-- Two goals (one per user)
insert into public.goals (user_id, name, target_amount, current_amount, deadline, status)
values
  ('11111111-1111-1111-1111-111111111111', 'Emergency Fund', 1000.00, 200.00, (current_date + interval '90 days')::date, 'active'),
  ('22222222-2222-2222-2222-222222222222', 'New Laptop',      800.00, 100.00, (current_date + interval '120 days')::date, 'active');

-- Four XP log entries (various reasons)
insert into public.xp_log (user_id, xp_delta, reason, related_entity_type, related_entity_id)
values
  ('11111111-1111-1111-1111-111111111111', 10,  'add_transaction', 'transaction', null),
  ('11111111-1111-1111-1111-111111111111', 20,  'streak_bonus',    null,          null),
  ('22222222-2222-2222-2222-222222222222', 10,  'add_transaction', 'transaction', null),
  ('22222222-2222-2222-2222-222222222222', 50,  'goal_created',    'goal',        null);