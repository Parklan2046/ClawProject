#!/usr/bin/env python3
"""
Fix all bugs found by 3 QA agents across 5 templates:

BUG 1 (QA1): 4 templates (V5/V8/V9/V10) missing 9 zh-HK i18n keys
BUG 2 (QA2): No distance display on cards (all 5 templates)
BUG 3 (QA2): Sort dropdown "distance" doesn't trigger geolocation (all 5)
BUG 4 (QA2): V1 map URLs don't use coordinates (V1 only)
BUG 5 (QA2): V1 map URLs use r.address instead of rAddress(r) (V1 only)
"""
import os, re

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dog-restaurants")
FILES = ["index.html", "t4-memphis/index.html", "t7-zakka/index.html", "t8-forest/index.html", "t9-meadow/index.html"]

# The 9 missing zh-HK keys (as a string to insert before the closing } of zh-HK section)
ZH_KEYS = "surpriseMe:'驚喜隨機',nearMe:'附近',sortByDistance:'按距離',copyAddress:'複製地址',copied:'已複製！',saved:'已收藏',removed:'已取消收藏',share:'分享',filterSaved:'已收藏',"

# New card footer with SVG icons (replaces emoji-based footer)
NEW_FOOTER = """<div class="card-footer"><button class="card-heart ${fav?'fav-active':''}" type="button" aria-label="${t('saved')}" aria-pressed="${fav}" title="${t('saved')}" onclick="event.stopPropagation();toggleFav(${r.idx})"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg></button><span class="card-licence" title="${t('cardLicence')}: ${escapeHtml(r.licence)}">${t('cardLicence')}: ${escapeHtml(r.licence)}</span><div class="card-actions"><button class="card-icon-btn" type="button" aria-label="${t('share')}" title="${t('share')}" onclick="event.stopPropagation();shareCard(${r.idx})"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg></button><button class="card-icon-btn" type="button" aria-label="${t('copyAddress')}" title="${t('copyAddress')}" onclick="event.stopPropagation();copyAddress(${r.idx})"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button><a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>${t('openInMaps')}</a></div></div>"""

# CSS for new card footer
FOOTER_CSS = """.card-footer{display:flex;align-items:center;gap:8px;margin-top:auto;padding-top:12px;border-top:1px solid var(--border)}
.card-licence{font-size:11.5px;color:var(--text-faint);font-weight:600;flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-heart{position:relative;flex-shrink:0;width:38px;height:38px;display:inline-flex;align-items:center;justify-content:center;border:none;cursor:pointer;background:var(--bg-muted);border-radius:var(--radius-pill);color:var(--text-faint);transition:background var(--dur) var(--ease-soft),color var(--dur) var(--ease-soft),transform var(--dur-fast) var(--ease-bounce)}
.card-heart:hover{background:var(--accent-coral-soft,#FFE0E0);color:var(--accent-coral-deep,#E8807A)}
.card-heart:active{transform:scale(0.88)}
.card-heart.fav-active{background:#FFE0E0;color:#E8807A}
.card-heart svg{width:18px;height:18px;transition:fill var(--dur) var(--ease-soft)}
.card-heart.fav-active svg{fill:currentColor;animation:heartPop 380ms var(--ease-bounce)}
@keyframes heartPop{0%{transform:scale(1)}25%{transform:scale(1.45)}50%{transform:scale(0.82)}75%{transform:scale(1.15)}100%{transform:scale(1)}}
.card-actions{display:flex;align-items:center;gap:4px;flex-shrink:0}
.card-icon-btn{flex-shrink:0;width:36px;height:36px;display:inline-flex;align-items:center;justify-content:center;border:none;cursor:pointer;background:transparent;border-radius:var(--radius-pill);color:var(--text-faint);transition:background var(--dur) var(--ease-soft),color var(--dur) var(--ease-soft),transform var(--dur-fast) var(--ease-bounce)}
.card-icon-btn:hover{background:var(--bg-muted);color:var(--text-muted)}
.card-icon-btn:active{transform:scale(0.9)}
.card-icon-btn svg{width:17px;height:17px}
.card-map-btn{flex-shrink:0;margin-left:4px;display:inline-flex;align-items:center;gap:5px;font:700 13px var(--font-body);color:#fff;text-decoration:none;white-space:nowrap;background:var(--primary);padding:8px 14px;border-radius:var(--radius-pill);box-shadow:var(--shadow-sage,var(--shadow-sm));transition:background var(--dur) var(--ease-soft),transform var(--dur-fast) var(--ease-bounce)}
.card-map-btn:hover{background:var(--primary-deep);transform:translateY(-1px)}
.card-map-btn:active{transform:translateY(0) scale(0.96)}
.card-map-btn svg{width:14px;height:14px;flex-shrink:0}
.card-heart:focus-visible,.card-icon-btn:focus-visible,.card-map-btn:focus-visible{outline:none;box-shadow:var(--focus-ring)}
.card-dist{display:inline-flex;align-items:center;gap:4px;font:700 12px/1 var(--font-body);padding:4px 10px;border-radius:var(--radius-pill);background:var(--primary-tint,#E8F1EA);color:var(--primary-deep,#5B8E6C);width:fit-content;margin-top:4px}"""

# Distance display JS to add to cardHTML
DIST_JS = "if(state.sort==='distance'&&userLoc&&r.lat!=null){const d=haversine(userLoc.lat,userLoc.lng,r.lat,r.lng);const dt=d<1?Math.round(d*1000)+' m':d.toFixed(1)+' km';distHTML=`<span class=\"card-dist\">\U0001f4cf ${dt}</span>`;}"

def fix_file(fpath):
    full = os.path.join(BASE, fpath)
    with open(full, "r", encoding="utf-8") as f:
        c = f.read()
    orig = c
    changes = []
    
    # === BUG 1: Add missing zh-HK keys ===
    en_pos = c.find("en:{")
    if en_pos < 0:
        en_pos = c.find("'en': {")
    if en_pos > 0:
        zh_section = c[:en_pos]
        if "surpriseMe:" not in zh_section:
            # Find the last } before en:{ — that's the end of zh-HK
            # Insert keys before it
            zh_end = c.rfind("},", 0, en_pos)
            if zh_end > 0:
                c = c[:zh_end] + "," + ZH_KEYS.rstrip(",") + c[zh_end+1:]
                # Fix potential double comma
                c = c.replace(",,", ",")
                changes.append("zh-HK i18n keys")
    
    # === BUG 2: Add distance display CSS ===
    if ".card-dist{" not in c:
        # Insert before </style>
        c = c.replace("</style>", FOOTER_CSS + "\n</style>", 1)
        # Remove old card-footer/card-actions CSS if present (avoid duplicates)
        # The old CSS was added by the batch script — replace it
        changes.append("footer CSS")
    
    # === BUG 2: Add distance display to cardHTML ===
    if "card-dist" not in c or "haversine(userLoc" not in c.split("cardHTML")[1] if "cardHTML" in c else True:
        # Add distHTML variable to cardHTML
        # Find "const fav=isFav" or "const fav = isFav" and add distHTML after it
        if "let distHTML" not in c:
            c = c.replace(
                "const fav=isFav(r.idx);",
                "const fav=isFav(r.idx);let distHTML='';" + DIST_JS,
                1
            )
            c = c.replace(
                "const fav = isFav(r.idx);",
                "const fav = isFav(r.idx);let distHTML='';" + DIST_JS.replace("\\", "\\\\"),
                1
            )
            changes.append("distance display JS")
        
        # Add ${distHTML} to the card template (after district, before address)
        if "${distHTML}" not in c:
            # Insert after card-district span, before card-address
            c = c.replace(
                '<div class="card-address">',
                '${distHTML}<div class="card-address">',
                1
            )
            changes.append("distance display HTML")
    
    # === BUG 3: Sort dropdown triggers nearMe when distance selected without geolocation ===
    if "if(this.value==='distance'&&!userLoc)" not in c:
        old_onchange = "onchange=\"state.sort=this.value;state.limit=60;renderCards()\""
        new_onchange = "onchange=\"if(this.value==='distance'&&!userLoc){nearMe();}else{state.sort=this.value;state.limit=60;renderCards();}\""
        if old_onchange in c:
            c = c.replace(old_onchange, new_onchange, 1)
            changes.append("sort dropdown geolocation trigger")
    
    # === BUG 4 & 5: V1 map URLs — use coordinates and rAddress ===
    if fpath == "index.html":
        # Check if V1 still uses r.address in map functions
        if "r.address" in c and "rAddress(r)" not in c.split("function mapEmbedUrl")[1].split("function")[0] if "function mapEmbedUrl" in c else False:
            # Replace V1 map functions
            old_map = """function mapEmbedUrl(idx) {
  const r = RESTAURANTS[idx];
  const query = `${r.address} ${r.zh} Hong Kong`;
  return `https://www.google.com/maps?q=${encodeURIComponent(query)}&hl=${getLocale()==='en'?'en':'zh-TW'}&output=embed`;
}
function mapExternalUrl(r) {
  const query = `${r.address} ${r.zh} Hong Kong`;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}&hl=${getLocale()==='en'?'en':'zh-TW'}`;
}
function directionsUrl(idx) {
  const r = RESTAURANTS[idx];
  const dest = encodeURIComponent(`${r.address} ${r.zh} Hong Kong`);
  return `https://www.google.com/maps/dir/?api=1&destination=${dest}&travelmode=walking`;
}"""
            new_map = """function mapEmbedUrl(idx) {
  const r = RESTAURANTS[idx];
  let q;
  if (r.lat != null && r.lng != null) { q = r.lat + ',' + r.lng; }
  else { q = rAddress(r) + ' ' + r.zh + ' Hong Kong'; }
  return `https://www.google.com/maps?q=${encodeURIComponent(q)}&hl=${getLocale()==='en'?'en':'zh-TW'}&output=embed`;
}
function mapExternalUrl(r) {
  let q;
  if (r.lat != null && r.lng != null) { q = r.lat + ',' + r.lng; }
  else { q = rAddress(r) + ' ' + r.zh + ' Hong Kong'; }
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}&hl=${getLocale()==='en'?'en':'zh-TW'}`;
}
function directionsUrl(idx) {
  const r = RESTAURANTS[idx];
  let q;
  if (r.lat != null && r.lng != null) { q = r.lat + ',' + r.lng; }
  else { q = rAddress(r) + ' ' + r.zh + ' Hong Kong'; }
  return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(q)}&travelmode=walking`;
}"""
            if old_map in c:
                c = c.replace(old_map, new_map, 1)
                changes.append("V1 map URLs (coords + rAddress)")
    
    # === Replace emoji-based card footer with SVG-based footer ===
    # Old footer pattern (emoji-based)
    old_emojis = [
        # Minified pattern with emojis
        '<div class="card-footer"><span class="card-licence">${t(\'cardLicence\')}: ${escapeHtml(r.licence)}</span><div class="card-actions"><button class="card-icon-btn ${fav?\'fav-active\':\'\'}" title="${t(\'saved\')}" onclick="event.stopPropagation();toggleFav(${r.idx})">${fav?\'❤️\':\'🤍\'}</button><button class="card-icon-btn" title="${t(\'share\')}" onclick="event.stopPropagation();shareCard(${r.idx})">📤</button><button class="card-icon-btn" title="${t(\'copyAddress\')}" onclick="event.stopPropagation();copyAddress(${r.idx})">📋</button><a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t(\'openInMaps\')} →</a></div></div>',
        # V1 readable pattern with emojis
        """    <div class="card-footer">
      <span class="card-licence">${t('cardLicence')}: ${escapeHtml(r.licence)}</span>
      <div class="card-actions">
        <button class="card-icon-btn ${fav?'fav-active':''}" title="${t('saved')}" onclick="event.stopPropagation();toggleFav(${r.idx})">${fav?'❤️':'🤍'}</button>
        <button class="card-icon-btn" title="${t('share')}" onclick="event.stopPropagation();shareCard(${r.idx})">📤</button>
        <button class="card-icon-btn" title="${t('copyAddress')}" onclick="event.stopPropagation();copyAddress(${r.idx})">📋</button>
        <a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t('openInMaps')} →</a>
      </div>
    </div>""",
    ]
    for old in old_emojis:
        if old in c:
            c = c.replace(old, NEW_FOOTER, 1)
            changes.append("SVG footer (replaced emojis)")
            break
    
    # Fix toggleFav to not re-render all cards (only update clicked heart)
    if "if(state.filterFav){" not in c:
        old_toggle = "function toggleFav(idx){let favs=getFavs();if(favs.includes(idx)){favs=favs.filter(f=>f!==idx);toast(t('removed'));}else{favs.push(idx);toast(t('saved'));}localStorage.setItem(FAV_KEY,JSON.stringify(favs));renderChips();renderCards();}"
        new_toggle = "function toggleFav(idx){let favs=getFavs();const wasFav=favs.includes(idx);if(wasFav){favs=favs.filter(f=>f!==idx);toast(t('removed'));}else{favs.push(idx);toast(t('saved'));}localStorage.setItem(FAV_KEY,JSON.stringify(favs));renderChips();if(state.filterFav){renderCards();}else{document.querySelectorAll('.card[data-idx=\"'+idx+'\"] .card-heart').forEach(btn=>{btn.classList.toggle('fav-active',!wasFav);btn.setAttribute('aria-pressed',!wasFav);});}}"
        if old_toggle in c:
            c = c.replace(old_toggle, new_toggle, 1)
            changes.append("toggleFav isolated update")
    
    if c != orig:
        with open(full, "w", encoding="utf-8") as f:
            f.write(c)
        print(f"  {fpath}: APPLIED ({', '.join(changes)})")
    else:
        print(f"  {fpath}: NO CHANGES NEEDED")

if __name__ == "__main__":
    print("Applying bug fixes to all 5 templates...")
    for f in FILES:
        fix_file(f)
    print("Done!")
