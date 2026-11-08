create table public.app_status (
  id smallint primary key check (id = 1),
  message text not null check (char_length(message) > 0),
  updated_at timestamp with time zone not null default timezone('utc'::text, now())
);

alter table public.app_status enable row level security;

grant select on table public.app_status to anon, authenticated;

create policy "アプリケーション状態を読み取れる"
on public.app_status
for select
to anon, authenticated
using (true);

insert into public.app_status (id, message)
values (1, 'Supabaseとの接続を確認できました。');
