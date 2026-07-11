#!/usr/bin/env python3
"""Fix V1 index.html remaining gaps."""
import os

fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dog-restaurants", "index.html")
with open(fpath, "r", encoding="utf-8") as f:
    c = f.read()

# Fix 1: state filterFav
c = c.replace(
    "let state = { q:'', district:'all', sort:'district', limit:60 };",
    "let state = { q:'', district:'all', sort:'district', limit:60, filterFav:false };"
)

# Fix 2: computeFiltered - add filterFav + distance sort
old_cf_start = "function computeFiltered() {"
old_cf_end = "  return out;\n}"
cf_idx_start = c.find(old_cf_start)
cf_idx_end = c.find(old_cf_end, cf_idx_start) + len(old_cf_end)
if cf_idx_start >= 0 and cf_idx_end > cf_idx_start:
    new_cf = """function computeFiltered() {
  const q = LOWER(state.q.trim());
  let out = RESTAURANTS;
  if (state.district !== 'all') out = out.filter(r => r.district === state.district);
  if (state.filterFav) out = out.filter(r => isFav(r.idx));
  if (q) {
    const terms = q.split(/\\s+/).filter(Boolean);
    out = out.filter(r => terms.every(t => r.haystack.includes(t)));
  }
  if (state.sort === 'distance' && userLoc) {
    out = [...out].sort((a,b) => {
      const da = a.lat != null ? haversine(userLoc.lat, userLoc.lng, a.lat, a.lng) : Infinity;
      const db = b.lat != null ? haversine(userLoc.lat, userLoc.lng, b.lat, b.lng) : Infinity;
      return da - db;
    });
  } else if (state.sort === 'name') {
    out = [...out].sort((a,b) =>
      (getLocale()==='en'?a.en:a.zh).localeCompare(getLocale()==='en'?b.en:b.zh, getLocale()));
  } else {
    out = [...out].sort((a,b) =>
      a.district === b.district
        ? a.zh.localeCompare(b.zh,'zh-HK')
        : a.district.localeCompare(b.district,'zh-HK'));
  }
  return out;
}"""
    c = c[:cf_idx_start] + new_cf + c[cf_idx_end:]

# Fix 3: cardHTML - add fav variable, update district/address, add card-actions
if "card-actions" not in c:
    # Add fav variable
    c = c.replace(
        "const isActive = r.idx === selectedIdx;\n  return",
        "const isActive = r.idx === selectedIdx;\n  const fav = isFav(r.idx);\n  return"
    )
    # Update district/address references
    c = c.replace("escapeHtml(districtName(r.district))", "escapeHtml(rDistrict(r))")
    c = c.replace("escapeHtml(r.address)", "escapeHtml(rAddress(r))")
    
    # Replace old footer with new card-actions footer
    old_footer = """    <div class="card-footer">
      <span class="card-licence">${t('cardLicence')}: ${escapeHtml(r.licence)}</span>
      <a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">
        ${t('openInMaps')} \u2192
      </a>
    </div>"""
    new_footer = """    <div class="card-footer">
      <span class="card-licence">${t('cardLicence')}: ${escapeHtml(r.licence)}</span>
      <div class="card-actions">
        <button class="card-icon-btn ${fav?'fav-active':''}" title="${t('saved')}" onclick="event.stopPropagation();toggleFav(${r.idx})">${fav?'\u2764\ufe0f':'\U0001f90d'}</button>
        <button class="card-icon-btn" title="${t('share')}" onclick="event.stopPropagation();shareCard(${r.idx})">\U0001f4e4</button>
        <button class="card-icon-btn" title="${t('copyAddress')}" onclick="event.stopPropagation();copyAddress(${r.idx})">\U0001f4cb</button>
        <a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t('openInMaps')} \u2192</a>
      </div>
    </div>"""
    c = c.replace(old_footer, new_footer)

with open(fpath, "w", encoding="utf-8") as f:
    f.write(c)
print("V1 index.html: all fixes applied")
