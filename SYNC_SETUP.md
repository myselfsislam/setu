# Turning on "Sync across devices" (Supabase, free tier)

Setu encrypts each user's data on their device before upload, so the server only ever stores unreadable blobs.

## 1. Create the project (about 5 minutes)
1. Sign up at **supabase.com** → **New project**. Pick a region in the **EU (e.g. London / Frankfurt)**. Any database password is fine (Setu doesn't use it).
2. **Project Settings → API**: copy the **Project URL** and the **anon public** key. (Never share the `service_role` key.)

## 2. Create the table (SQL Editor → New query → paste → Run)
```sql
create table public.vaults (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  salt       text not null,
  data       text not null,
  updated_at timestamptz not null default now()
);
alter table public.vaults enable row level security;
create policy "read own vault"   on public.vaults for select using (auth.uid() = user_id);
create policy "create own vault" on public.vaults for insert with check (auth.uid() = user_id);
create policy "update own vault" on public.vaults for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "delete own vault" on public.vaults for delete using (auth.uid() = user_id);
```

## 3. Email sign-in with a 6-digit code
1. **Authentication → Sign In / Providers → Email**: enabled. Leave "Confirm email" on.
2. **Authentication → Email Templates → Magic Link**: replace the body with:
   ```html
   <h2>Your Setu sign-in code</h2>
   <p>Enter this code in Setu: <strong style="font-size:24px">{{ .Token }}</strong></p>
   <p>It expires in 1 hour. If you didn't ask for it, ignore this email.</p>
   ```
   Do the same for **Confirm signup** (first-time users get this one).
3. **Authentication → URL Configuration**: Site URL `https://myselfsislam.github.io/setu/`.
4. Optional but recommended for launch: **Project Settings → Authentication → SMTP** with your own email provider (Supabase's built-in email is limited to a few emails an hour).

## 4. Switch it on in Setu
Send the Project URL and anon key to be added to `SYNC_CFG` in `index.html`:
```js
var SYNC_CFG={url:'https://YOUR-PROJECT.supabase.co',anon:'YOUR-ANON-KEY'};
```
The anon key is safe to publish: row-level security means each signed-in user can only read and write their own encrypted row.
