# HANDOFF: Dog Restaurants Auto-Update & Deployment

**Project:** Parklan ClawHub — Dog-Friendly Restaurants HK
**Repo:** https://github.com/Parklan2046/ClawProject
**Live site:** on9claw.com/dog-restaurants/
**Commit:** `0514ac1` — pushed to `main`
**Date:** July 2026

---

## What This Project Does

A static website showing 944 licensed dog-friendly restaurants in Hong Kong, with bilingual search (Traditional Chinese + English), 19-district filter, Google Maps embed, and 5 design templates. Data is sourced from FEHD's official public API.

## What's Already Done (no action needed)

| Item | Status |
|---|---|
| 5 HTML templates (V1, V5, V8, V9, V10) | Built, tested, deployed |
| `data.js` with 944 restaurants | Generated from live API |
| Template gallery (`templates.html`) | Links to all 5 versions |
| Update script (`scripts/update-dog-data.py`) | Fetches API, compares hash, regenerates data.js |
| GitHub Actions cron workflow (`.github/workflows/update-dog-data.yml`) | Committed and pushed |
| All bug fixes (JS syntax, mobile map tab) | Applied to all 5 templates |
| QA verified by 5 subagents | 189/189 checks passed |

---

## What You Need To Do

### Step 1: Verify GitHub Secrets Exist

The cron workflow uses 3 secrets that should already exist for the main deploy workflow. Verify them at:

```
GitHub repo → Settings → Secrets and variables → Actions
```

Required secrets:

| Secret Name | What It Is | Used By |
|---|---|---|
| `DROPLET_HOST` | DigitalOcean droplet IP address | Both workflows |
| `DROPLET_USERNAME` | SSH username (likely `root`) | Both workflows |
| `DROPLET_PASSWORD` | SSH password | Both workflows |

If any are missing, add them. These are the SAME secrets used by `.github/workflows/deploy.yml` (the push-to-deploy workflow), so if deploys already work, these secrets are already configured.

### Step 2: Trigger the First Manual Run

Test the workflow immediately (don't wait for the daily cron):

```
GitHub repo → Actions tab → "Update Dog Restaurant Data" → Run workflow
```

Or via CLI:
```bash
gh workflow run update-dog-data.yml --repo Parklan2046/ClawProject
```

**Expected behavior:**
1. Workflow starts → checks out code → runs Python script
2. Script fetches `https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php`
3. Since data.js was just regenerated, hash should match → "No data changes detected"
4. Workflow exits cleanly with `changed=false`

If the workflow fails, check the Actions logs for the specific step.

### Step 3: Verify Nginx Serves the Site

The dog-restaurants directory needs to be accessible at `on9claw.com/dog-restaurants/`. On the droplet:

```bash
ssh root@<DROPLET_HOST>
ls -la /var/www/clawproject/dog-restaurants/
```

You should see:
```
data.js
index.html
templates.html
t4-memphis/
t7-zakka/
t8-forest/
t9-meadow/
```

Check Nginx config serves it:
```bash
cat /etc/nginx/sites-enabled/default | grep -A5 "location /"
```

The Nginx config should serve `/var/www/clawproject/` as the root, so `/dog-restaurants/` resolves automatically. If not, add:

```nginx
location /dog-restaurants/ {
    alias /var/www/clawproject/dog-restaurants/;
    try_files $uri $uri/ /dog-restaurants/index.html;
}
```

Then reload: `sudo nginx -t && sudo systemctl reload nginx`

### Step 4: Confirm the Daily Cron Schedule

The cron runs at **00:00 UTC daily** (= 08:00 HKT). To confirm it's registered:

```
GitHub repo → Actions tab → "Update Dog Restaurant Data" → check for the schedule icon
```

The schedule is defined in the workflow file. It cannot be changed from the UI — edit `.github/workflows/update-dog-data.yml` if you want a different time:

```yaml
schedule:
  - cron: "0 0 * * *"   # currently 08:00 HKT / 00:00 UTC
```

---

## How the Auto-Update Flow Works

```
Every day at 08:00 HKT
         │
         ▼
GitHub Actions triggers "Update Dog Restaurant Data"
         │
         ▼
scripts/update-dog-data.py runs
  ├── Fetches FEHD getData.php API (944+ restaurants)
  ├── Transforms to compact format
  ├── Hashes the data
  └── Compares with .data-hash file
         │
     ┌───┴───┐
     │       │
   SAME    CHANGED
     │       │
     ▼       ▼
   Done    Overwrites data.js + .data-hash
           │
           ▼
         git commit + push to main
           │
           ▼
         SSH to droplet → git pull origin main
           │
           ▼
         on9claw.com/dog-restaurants/ is now live with fresh data
```

**Key detail:** The script only commits when data actually changes. If FEHD doesn't update, no commit happens, no deploy happens. This keeps git history clean.

---

## Data Source Reference

**Old source (DEAD):** `https://www.fehd.gov.hk/tc_chi/licensing/dog_restaurants/fulllist.pdf` — returns 404. FEHD removed it.

**Current source (LIVE):**
```
GET https://www.fehd.gov.hk/english/licensing/dog_restaurants/getData.php
```

Returns a JSON array of objects with these fields:

| Field | Type | Example |
|---|---|---|
| `shop_sign_en` | string | `%ARABICA` |
| `shop_sign_tc` | string | `%ARABICA` |
| `shop_sign_sc` | string | `%ARABICA` |
| `district_en` | string | `Central/Western` |
| `district_tc` | string | `中西區` |
| `district_sc` | string | `中西区` |
| `address_en` | string | `SHOP G17, LEVEL G OF THE PEAK TOWER...` |
| `address_tc` | string | `香港山頂道128號 山頂凌霄閣G層G17鋪` |
| `address_sc` | string | `香港山顶道128号 山顶凌霄阁G层G17铺` |
| `licence` | string | `3118811827` |
| `house_rule` | string | (currently empty for all) |

No API key required. No rate limiting observed. The JS file on FEHD's site is versioned with `?v=20260626`.

---

## Files Modified/Created in This Commit

| File | Action | Purpose |
|---|---|---|
| `scripts/update-dog-data.py` | **NEW** | Data fetcher + transformer (stdlib only, zero deps) |
| `.github/workflows/update-dog-data.yml` | **NEW** | Daily cron workflow |
| `dog-restaurants/data.js` | **MODIFIED** | Updated from 946 (old PDF) to 944 (live API) |
| `dog-restaurants/.data-hash` | **NEW** | Hash file for change detection |

---

## Manual Operations (if needed)

### Force a data refresh right now
```bash
gh workflow run update-dog-data.yml
```

### Run the script locally
```bash
cd /var/www/clawproject
python3 scripts/update-dog-data.py
```

### Check current record count
```bash
python3 -c "
import json
with open('/var/www/clawproject/dog-restaurants/data.js') as f:
    s = f.read().replace('const DOG_DATA=','').rstrip(';\\n')
    print(len(json.loads(s)['r']), 'restaurants')
"
```

### Change cron frequency
Edit `.github/workflows/update-dog-data.yml`:
```yaml
schedule:
  - cron: "0 0 * * *"    # daily at 08:00 HKT
  # - cron: "0 0 * * 1"  # weekly on Monday only
  # - cron: "0 */6 * * *" # every 6 hours
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Workflow shows "No data changes" every day | This is correct — FEHD hasn't updated their list. The data IS fresh. |
| Workflow fails on API fetch | FEHD server may be down or blocked. Retry manually from Actions tab. |
| Data.js is stale on the website | SSH to droplet, run `cd /var/www/clawproject && git pull origin main` |
| Nginx returns 404 for /dog-restaurants/ | Check Nginx root path serves `/var/www/clawproject/` — see Step 3 |
| GitHub Actions cron not triggering | GitHub may delay scheduled runs up to 15 min on high-load days. Also: scheduled workflows only run on the default branch. |
| Workflow can't push commit | Ensure `permissions: contents: write` is in the workflow (it is). Repo settings must allow Actions to create commits. |

---

## Contact / Context

- **Repo owner:** Parklan (github.com/Parklan2046)
- **Live domain:** on9claw.com (DigitalOcean droplet)
- **Deploy mechanism:** SSH git pull on push to main (already working for all other projects)
- **Cron schedule:** Daily at 08:00 HKT
