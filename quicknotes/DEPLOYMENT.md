# QuickNotes Deployment Guide

## Current Status

✅ **QuickNotes is deployed and running!**

### Local Dashboard (Working Now)
**URL:** `http://172.17.0.2:5678` (from inside container)  
**SSH Tunnel:** `ssh -L 5678:localhost:5678 ubuntu@134.122.8.186` then open `http://localhost:5678`

### Landing Page
**Files:** `/var/www/on9claw/quicknotes/`

---

## Quick Access Now

**SSH into VPS:** `ssh root@134.122.8.186` (password: hMjvskBEhPtxnN8Z)

Then visit: `http://134.122.8.186:5678`

---

## Make it Public at on9claw.com/quicknotes

Reload Caddy on the VPS host:
```bash
caddy reload --config /tmp/on9claw-layout/Caddyfile
```

---

## QuickNotes Agent

✅ Active in Signal - just send notes to Laura!
