#!/usr/bin/env python3
"""Apply Tier 1 feature updates to all 5 dog-restaurant templates."""
import os, re, sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dog-restaurants")
FILES = ["index.html", "t4-memphis/index.html", "t7-zakka/index.html", "t8-forest/index.html", "t9-meadow/index.html"]

SHARED_JS = """let toastTimer;function toast(msg){let el=document.getElementById('toast');if(!el){el=document.createElement('div');el.id='toast';document.body.appendChild(el);}el.textContent=msg;el.className='toast show';clearTimeout(toastTimer);toastTimer=setTimeout(()=>{el.className='toast';},2000);}
function surpriseMe(){const pool=computeFiltered().length?computeFiltered():RESTAURANTS;const r=pool[Math.floor(Math.random()*pool.length)];state.limit=Math.max(state.limit,r.idx+1);renderCards();selectCard(r.idx);toast(t('surpriseMe')+' \U0001f3b2');}
async function shareCard(idx){const r=RESTAURANTS[idx];const name=getLocale()==='en'?r.en:r.zh;const url=location.origin+location.pathname+'?r='+r.idx;if(navigator.share){try{await navigator.share({title:name,text:rDistrict(r)+' \u00b7 '+rAddress(r),url});}catch(e){}}else{try{await navigator.clipboard.writeText(url);toast(t('share')+' \u2705');}catch(e){}}}
const FAV_KEY='dog-favs';
function getFavs(){try{return JSON.parse(localStorage.getItem(FAV_KEY))||[];}catch(e){return[];}}
function isFav(idx){return getFavs().includes(idx);}
function toggleFav(idx){let favs=getFavs();if(favs.includes(idx)){favs=favs.filter(f=>f!==idx);toast(t('removed'));}else{favs.push(idx);toast(t('saved'));}localStorage.setItem(FAV_KEY,JSON.stringify(favs));renderChips();renderCards();}
function copyAddress(idx){const r=RESTAURANTS[idx];if(navigator.clipboard){navigator.clipboard.writeText(rAddress(r)).then(()=>toast(t('copied'))).catch(()=>{});}else{const ta=document.createElement('textarea');ta.value=rAddress(r);document.body.appendChild(ta);ta.select();try{document.execCommand('copy');toast(t('copied'));}catch(e){}document.body.removeChild(ta);}}
function rDistrict(r){return getLocale()==='en'?(r.districtEn||DISTRICT_ZH_TO_EN[r.districtZh]||r.districtZh||r.district||''):(r.districtZh||r.district||'');}
function rAddress(r){return getLocale()==='en'?(r.addressEn||r.addressZh||r.address||''):(r.addressZh||r.address||'');}
function haversine(lat1,lng1,lat2,lng2){const R=6371,toRad=d=>d*Math.PI/180;const dLat=toRad(lat2-lat1),dLng=toRad(lng2-lng1);const a=Math.sin(dLat/2)**2+Math.cos(toRad(lat1))*Math.cos(toRad(lat2))*Math.sin(dLng/2)**2;return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));}
let userLoc=null;
function nearMe(){if(!navigator.geolocation){toast(t('nearMe')+' \u274c');return;}toast(t('nearMe')+' \u2026');navigator.geolocation.getCurrentPosition(pos=>{userLoc={lat:pos.coords.latitude,lng:pos.coords.longitude};state.sort='distance';document.getElementById('sortSelect').value='distance';state.limit=60;renderCards();},()=>{toast(t('nearMe')+' \u274c');});}
"""

CARD_FOOTER = '<div class="card-footer"><span class="card-licence">${t(\'cardLicence\')}: ${escapeHtml(r.licence)}</span><div class="card-actions"><button class="card-icon-btn ${fav?\'fav-active\':\'\'}" title="${t(\'saved\')}" onclick="event.stopPropagation();toggleFav(${r.idx})">${fav?\'\u2764\ufe0f\':\'\U0001f90d\'}</button><button class="card-icon-btn" title="${t(\'share\')}" onclick="event.stopPropagation();shareCard(${r.idx})">\U0001f4e4</button><button class="card-icon-btn" title="${t(\'copyAddress\')}" onclick="event.stopPropagation();copyAddress(${r.idx})">\U0001f4cb</button><a class="card-map-btn" href="${mapExternalUrl(r)}" target="_blank" rel="noopener" onclick="event.stopPropagation()">${t(\'openInMaps\')} \u2192</a></div></div>'

# i18n additions
I18N_ZH = "copyAddress:'\u8907\u88fd\u5730\u5740',copied:'\u5df2\u8907\u88fd\uff01',surpriseMe:'\u9a5a\u559c\u96a8\u6a5f',saved:'\u5df2\u6536\u85cf',removed:'\u5df2\u79fb\u9664',share:'\u5206\u4eab',nearMe:'\u9644\u8fd1',sortByDistance:'\u6309\u8ddd\u96e2',filterSaved:'\u5df2\u6536\u85cf',"
I18N_EN = "copyAddress:'Copy address',copied:'Copied!',surpriseMe:'Surprise me',saved:'Saved',removed:'Removed',share:'Share',nearMe:'Near me',sortByDistance:'By distance',filterSaved:'Saved',"

# RESTAURANTS defensive mapping
RESTAURANTS_NEW = "const RESTAURANTS=DOG_DATA.r.map((row,i)=>{let en,zh,districtZh,districtEn,addressZh,addressEn,licence,lat,lng;if(row.length>=7){[en,zh,districtZh,districtEn,addressZh,addressEn,licence,lat,lng]=row;lat=lat||null;lng=lng||null;}else{[en,zh,districtZh,addressZh,licence]=row;districtEn=DISTRICT_ZH_TO_EN[districtZh]||'';addressEn='';lat=null;lng=null;}return{idx:i,en,zh,districtZh,districtEn,addressZh,addressEn,licence,lat,lng,district:districtZh,address:addressZh,haystack:`${LOWER(en)} ${LOWER(zh)} ${LOWER(districtZh)} ${LOWER(districtEn)} ${LOWER(addressZh)} ${LOWER(addressEn)} ${LOWER(licence)}`};});"

# Old RESTAURANTS pattern (varies slightly per template but the core is the same)
RESTAURANTS_OLD_PATTERNS = [
    "const RESTAURANTS=DOG_DATA.r.map(([en,zh,district,address,licence],i)=>({idx:i,en,zh,district,address,licence,haystack:`${LOWER(en)} ${LOWER(zh)} ${LOWER(district)} ${LOWER(DISTRICT_ZH_TO_EN[district]||'')} ${LOWER(address)} ${LOWER(licence)}`}));",
    "const RESTAURANTS = DOG_DATA.r.map(([en,zh,district,address,licence], i) => ({\n  idx:i, en, zh, district, address, licence,\n  haystack: `${LOWER(en)} ${LOWER(zh)} ${LOWER(district)} ${LOWER(DISTRICT_ZH_TO_EN[district]||'')} ${LOWER(address)} ${LOWER(licence)}`\n}));",
]

# computeFiltered old -> new (minified)
CF_OLD_MIN = "function computeFiltered(){const q=LOWER(state.q.trim());let out=RESTAURANTS;if(state.district!=='all')out=out.filter(r=>r.district===state.district);if(q){const terms=q.split(/\\s+/).filter(Boolean);out=out.filter(r=>terms.every(t=>r.haystack.includes(t)));}if(state.sort==='name'){out=[...out].sort((a,b)=>(getLocale()==='en'?a.en:a.zh).localeCompare(getLocale()==='en'?b.en:b.zh,getLocale()));}else{out=[...out].sort((a,b)=>a.district===b.district?a.zh.localeCompare(b.zh,'zh-HK'):a.district.localeCompare(b.district,'zh-HK'));}return out;}"
CF_NEW_MIN = "function computeFiltered(){const q=LOWER(state.q.trim());let out=RESTAURANTS;if(state.district!=='all')out=out.filter(r=>r.district===state.district);if(state.filterFav)out=out.filter(r=>isFav(r.idx));if(q){const terms=q.split(/\\s+/).filter(Boolean);out=out.filter(r=>terms.every(t=>r.haystack.includes(t)));}if(state.sort==='distance'&&userLoc){out=[...out].sort((a,b)=>{const da=a.lat!=null?haversine(userLoc.lat,userLoc.lng,a.lat,a.lng):Infinity;const db=b.lat!=null?haversine(userLoc.lat,userLoc.lng,b.lat,b.lng):Infinity;return da-db;});}else if(state.sort==='name'){out=[...out].sort((a,b)=>(getLocale()==='en'?a.en:a.zh).localeCompare(getLocale()==='en'?b.en:b.zh,getLocale()));}else{out=[...out].sort((a,b)=>a.district===b.district?a.zh.localeCompare(b.zh,'zh-HK'):a.district.localeCompare(b.district,'zh-HK'));}return out;}"

# state old -> new (add filterFav)
STATE_OLD_MIN = "let state={q:'',district:'all',sort:'district',limit:60};let selectedIdx=-1;"
STATE_NEW_MIN = "let state={q:'',district:'all',sort:'district',limit:60,filterFav:false};let selectedIdx=-1;"

# Map URL functions old -> new
MAP_OLD = "function mapEmbedUrl(idx){const r=RESTAURANTS[idx];return `https://www.google.com/maps?q=${encodeURIComponent(r.address+' '+r.zh+' Hong Kong')}&hl=${getLocale()==='en'?'en':'zh-TW'}&output=embed`;}"
MAP_NEW = "function mapEmbedUrl(idx){const r=RESTAURANTS[idx];let q;if(r.lat!=null&&r.lng!=null){q=r.lat+','+r.lng;}else{q=rAddress(r)+' '+r.zh+' Hong Kong';}return `https://www.google.com/maps?q=${encodeURIComponent(q)}&hl=${getLocale()==='en'?'en':'zh-TW'}&output=embed`;}"

MAP_EXT_OLD = "function mapExternalUrl(r){return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(r.address+' '+r.zh+' Hong Kong')}&hl=${getLocale()==='en'?'en':'zh-TW'}`;}"
MAP_EXT_NEW = "function mapExternalUrl(r){let q;if(r.lat!=null&&r.lng!=null){q=r.lat+','+r.lng;}else{q=rAddress(r)+' '+r.zh+' Hong Kong';}return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}&hl=${getLocale()==='en'?'en':'zh-TW'}`;}"

DIR_OLD = "function directionsUrl(idx){const r=RESTAURANTS[idx];return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(r.address+' '+r.zh+' Hong Kong')}&travelmode=walking`;}"
DIR_NEW = "function directionsUrl(idx){const r=RESTAURANTS[idx];let q;if(r.lat!=null&&r.lng!=null){q=r.lat+','+r.lng;}else{q=rAddress(r)+' '+r.zh+' Hong Kong';}return `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(q)}&travelmode=walking`;}"

MAPSUB_OLD = "document.getElementById('mapSub').textContent=districtName(r.district)+' \u00b7 '+r.address.substring(0,40);"
MAPSUB_NEW = "document.getElementById('mapSub').textContent=rDistrict(r)+' \u00b7 '+rAddress(r).substring(0,40);"

# checkUrlParams old -> new (add ?r= handling)
CHECK_OLD_MIN = "function checkUrlParams(){const params=new URLSearchParams(location.search);const d=params.get('district');const q=params.get('q');if(d&&DOG_DATA.d.includes(d))state.district=d;if(q){state.q=q;document.getElementById('search').value=q;document.getElementById('searchClear').hidden=false;}const lang=params.get('lang');if(lang==='en'||lang==='zh-HK')currentLocale=lang;}"
CHECK_NEW_MIN = SHARED_JS + "\nfunction checkUrlParams(){const params=new URLSearchParams(location.search);const d=params.get('district');const q=params.get('q');if(d&&DOG_DATA.d.includes(d))state.district=d;if(q){state.q=q;document.getElementById('search').value=q;document.getElementById('searchClear').hidden=false;}const lang=params.get('lang');if(lang==='en'||lang==='zh-HK')currentLocale=lang;const rIdx=params.get('r');if(rIdx!==null){const ri=parseInt(rIdx);if(ri>=0&&ri<RESTAURANTS.length)selectedIdx=ri;}}"

# DOMContentLoaded old -> new (add deep-link)
DCL_OLD_SIMPLE = "window.addEventListener('DOMContentLoaded',()=>{checkUrlParams();applyLocale();});"
DCL_NEW_SIMPLE = "window.addEventListener('DOMContentLoaded',()=>{checkUrlParams();applyLocale();if(selectedIdx>=0)showMap(selectedIdx);});"

DCL_OLD_FOREST = "window.addEventListener('DOMContentLoaded',()=>{buildBgDogs();buildLeaves(reduceMotion?0:14);checkUrlParams();applyLocale();onScroll();window.addEventListener('resize',onScroll,{passive:true});});"
DCL_NEW_FOREST = "window.addEventListener('DOMContentLoaded',()=>{buildBgDogs();buildLeaves(reduceMotion?0:14);checkUrlParams();applyLocale();if(selectedIdx>=0)showMap(selectedIdx);onScroll();window.addEventListener('resize',onScroll,{passive:true});});"

def patch_file(fpath):
    full = os.path.join(BASE, fpath)
    with open(full, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    changes = []

    # i18n: add new keys after cardLicence in zh-HK
    if "surpriseMe:" not in content:
        # zh-HK
        content = content.replace(
            "cardLicence:'\u726c\u724c',",
            "cardLicence:'\u726c\u724c'," + I18N_ZH,
            1
        )
        # en
        content = content.replace(
            "cardLicence:'Licence',",
            "cardLicence:'Licence'," + I18N_EN,
            1
        )
        changes.append("i18n keys")

    # V1 has readable cardLicence - handle differently
    if "cardLicence:'\u726c\u724c'" not in content and "surpriseMe:" not in content:
        # Try V1 format
        content = content.replace(
            "copied:'\u5df2\u8907\u88fd\uff01',",
            "copied:'\u5df2\u8907\u88fd\uff01',surpriseMe:'\u9a5a\u559c\u96a8\u6a5f',saved:'\u5df2\u6536\u85cf',removed:'\u5df2\u79fb\u9664',share:'\u5206\u4eab',nearMe:'\u9644\u8fd1',sortByDistance:'\u6309\u8ddd\u96e2',filterSaved:'\u5df2\u6536\u85cf',",
            1
        )
        content = content.replace(
            "copied:'Copied!',",
            "copied:'Copied!',surpriseMe:'Surprise me',saved:'Saved',removed:'Removed',share:'Share',nearMe:'Near me',sortByDistance:'By distance',filterSaved:'Saved',",
            1
        )
        changes.append("i18n keys (V1 format)")

    # RESTAURANTS mapping
    if "districtZh" not in content:
        for pat in RESTAURANTS_OLD_PATTERNS:
            if pat in content:
                content = content.replace(pat, RESTAURANTS_NEW, 1)
                changes.append("RESTAURANTS mapping")
                break

    # state
    if "filterFav" not in content:
        if STATE_OLD_MIN in content:
            content = content.replace(STATE_OLD_MIN, STATE_NEW_MIN, 1)
            changes.append("state.filterFav")

    # computeFiltered
    if "state.filterFav" not in content or "haversine(userLoc" not in content:
        if CF_OLD_MIN in content:
            content = content.replace(CF_OLD_MIN, CF_NEW_MIN, 1)
            changes.append("computeFiltered")

    # Map URL functions
    content = content.replace(MAP_OLD, MAP_NEW)
    content = content.replace(MAP_EXT_OLD, MAP_EXT_NEW)
    content = content.replace(DIR_OLD, DIR_NEW)
    if "rAddress" in content:
        changes.append("map URLs")

    # updateMapInfo
    content = content.replace(MAPSUB_OLD, MAPSUB_NEW)

    # checkUrlParams + shared JS
    if "function nearMe()" not in content:
        if CHECK_OLD_MIN in content:
            content = content.replace(CHECK_OLD_MIN, CHECK_NEW_MIN, 1)
            changes.append("checkUrlParams + shared JS")
        else:
            # V1 readable format
            v1_check = """// check URL params for initial filter
function checkUrlParams() {
  const params = new URLSearchParams(location.search);
  const d = params.get('district');
  const q = params.get('q');
  if (d && DOG_DATA.d.includes(d)) state.district = d;
  if (q) { state.q = q; document.getElementById('search').value = q; document.getElementById('searchClear').hidden = false; }
  const lang = params.get('lang');
  if (lang === 'en' || lang === 'zh-HK') currentLocale = lang;
}"""
            v1_new = SHARED_JS + "\n// check URL params for initial filter\nfunction checkUrlParams() {\n  const params = new URLSearchParams(location.search);\n  const d = params.get('district');\n  const q = params.get('q');\n  if (d && DOG_DATA.d.includes(d)) state.district = d;\n  if (q) { state.q = q; document.getElementById('search').value = q; document.getElementById('searchClear').hidden = false; }\n  const lang = params.get('lang');\n  if (lang === 'en' || lang === 'zh-HK') currentLocale = lang;\n  const r = params.get('r');\n  if (r !== null) { const idx = parseInt(r); if (idx >= 0 && idx < RESTAURANTS.length) selectedIdx = idx; }\n}"
            if v1_check in content:
                content = content.replace(v1_check, v1_new, 1)
                changes.append("checkUrlParams V1 + shared JS")

    # DOMContentLoaded - add deep-link
    if "if(selectedIdx>=0)showMap(selectedIdx)" not in content:
        content = content.replace(DCL_OLD_SIMPLE, DCL_NEW_SIMPLE)
        content = content.replace(DCL_OLD_FOREST, DCL_NEW_FOREST)
        changes.append("DOMContentLoaded deep-link")

    # renderChips - add saved chip
    if "filterSaved" not in content or "getFavs()" not in content:
        # Minified templates
        old_chips = "const chips=[`<button class=\"chip ${state.district==='all'?'active':''}\" onclick=\"setDistrict('all')\">"
        new_chips_prefix = "const favs=getFavs();const chips=[`<button class=\"chip ${state.district==='all'?'active':''}\" onclick=\"setDistrict('all')\">"
        if old_chips in content and "getFavs()" not in content:
            # Find the closing of the first chip and add saved chip after it
            # Pattern: </button>`;
            content = content.replace(
                "</button>`];",
                "</button>`,`<button class=\"chip ${state.filterFav?'active':''}\" onclick=\"state.filterFav=!state.filterFav;renderChips();renderCards()\">\u2764\ufe0f ${t('filterSaved')} <span class=\"chip-count\">${favs.length}</span></button>`];",
                1
            )
            content = content.replace(old_chips, new_chips_prefix, 1)
            changes.append("renderChips saved chip")

    # cardHTML - update to new format with actions
    if "card-actions" not in content:
        # This is complex - each template has different cardHTML
        # Find the old card footer and replace with new one
        old_footer = "<div class=\"card-footer\"><span class=\"card-licence\">${t('cardLicence')}: ${escapeHtml(r.licence)}</span><a class=\"card-map-btn\" href=\"${mapExternalUrl(r)}\" target=\"_blank\" rel=\"noopener\" onclick=\"event.stopPropagation()\">${t('openInMaps')} \u2192</a></div>"
        if old_footer in content:
            content = content.replace(old_footer, CARD_FOOTER)
            changes.append("card footer")
        
        # Update district and address references in cardHTML
        content = content.replace("escapeHtml(districtName(r.district))", "escapeHtml(rDistrict(r))")
        content = content.replace("escapeHtml(r.address)", "escapeHtml(rAddress(r))")

    # Hero buttons
    if "surpriseMe()" not in content or "nearMe()" not in content:
        hero_btns = '<div class="hero-actions"><button class="hero-btn" onclick="surpriseMe()">\U0001f3b2 <span data-i18n="surpriseMe">\u9a5a\u559c\u96a8\u6a5f</span></button><button class="hero-btn" onclick="nearMe()">\U0001f4cd <span data-i18n="nearMe">\u9644\u8fd1</span></button></div>'
        # Find </section> after search bar
        if "hero-actions" not in content:
            # Try to find the end of the search-wrap div and insert before </section>
            content = content.replace(
                '</div></div></div></section>',
                '</div></div>' + hero_btns + '</div></section>',
                1
            )
            changes.append("hero buttons")

    if content != orig:
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  {fpath}: APPLIED ({', '.join(changes)})")
    else:
        print(f"  {fpath}: NO CHANGES NEEDED")

if __name__ == "__main__":
    print("Applying Tier 1 feature updates to all 5 templates...")
    for f in FILES:
        patch_file(f)
    print("Done!")
