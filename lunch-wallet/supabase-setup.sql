-- Lunch Wallet Supabase setup
-- Run this once in Supabase SQL Editor for project: Parklan2046's Project

create extension if not exists pgcrypto;

create table if not exists public.lunch_wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  type text not null check (type in ('deposit', 'lunch', 'taxi')),
  by_name text not null,
  amount numeric(12,2) not null check (amount > 0),
  date date not null,
  place text,
  note text,
  participants jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.lunch_wallet_meta (
  key text primary key,
  value jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.lunch_wallet_transactions enable row level security;
alter table public.lunch_wallet_meta enable row level security;

drop policy if exists "public full access lunch wallet transactions" on public.lunch_wallet_transactions;
create policy "public full access lunch wallet transactions"
  on public.lunch_wallet_transactions
  for all
  to anon
  using (true)
  with check (true);

drop policy if exists "public full access lunch wallet meta" on public.lunch_wallet_meta;
create policy "public full access lunch wallet meta"
  on public.lunch_wallet_meta
  for all
  to anon
  using (true)
  with check (true);

insert into public.lunch_wallet_meta (key, value)
values ('saved_places', '{"lunch": [], "taxi": []}'::jsonb)
on conflict (key) do nothing;
