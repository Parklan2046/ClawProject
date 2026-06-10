/* ============================================
   PixelStrike 1.6 — App Logic
   ============================================ */

'use strict';

/* ---------- DATA ---------- */

const SIDES = {
  ct: {
    label: 'Counter-Terrorist',
    short: 'Counter-Terrorist operative',
    clothing: 'classic blue helmet, tactical vest and camo uniform',
  },
  t: {
    label: 'Terrorist',
    short: 'Terrorist operative',
    clothing: 'classic brown jacket, balaclava and cap',
  },
};

const MAPS = {
  de_dust2: {
    label: 'de_dust2',
    locations: ['A Bombsite', 'Long A', 'Long Doors', 'Mid', 'T Spawn', 'CT Spawn', 'B Tunnels', 'B Site'],
    features: 'iconic sandstone walls, wooden crates, double doors and sandbags',
  },
  de_inferno: {
    label: 'de_inferno',
    locations: ['A Site', 'Banana', 'Apartments', 'Library', 'Mid', 'T Spawn', 'CT Spawn', 'Pit'],
    features: 'iconic terracotta walls, cobblestone ground, arched windows and market stalls',
  },
  de_train: {
    label: 'de_train',
    locations: ['A Site', 'B Site', 'Ivy', 'Upper Tunnels', 'T Connector', 'CT Spawn', 'Alley', 'Pop Dog'],
    features: 'iconic industrial trainyard, shipping containers, green steel walls and graffiti',
  },
  de_nuke: {
    label: 'de_nuke',
    locations: ['A Site', 'B Site', 'Outside', 'Roof', 'Lobby', 'Ramp', 'Silo', 'Hut'],
    features: 'iconic nuclear power plant, concrete walls, radioactive glow and chain-link fences',
  },
  de_mirage: {
    label: 'de_mirage',
    locations: ['A Site', 'B Site', 'Mid', 'Palace', 'A Ramp', 'T Apartments', 'CT Spawn', 'Jungle'],
    features: 'iconic Moroccan walls, ornate archways, sun-baked plaster and palm trees',
  },
  de_cbble: {
    label: 'de_cbble',
    locations: ['A Site', 'B Site', 'Drop', 'Mid', 'T Spawn', 'CT Spawn', 'Long A', 'Hut'],
    features: 'iconic stone castle ruins, green courtyard, medieval archways and grass',
  },
};

const GUNS = [
  // Pistols
  { id: 'glock', name: 'Glock-18', cat: 'pistol', side: 't', icon: 'gun-pistol', action: 'held at the hip ready to fire' },
  { id: 'usp', name: 'USP-S', cat: 'pistol', side: 'ct', icon: 'gun-pistol', action: 'held at the hip with silencer' },
  { id: 'deagle', name: 'Desert Eagle', cat: 'pistol', side: 'both', icon: 'gun-pistol', action: 'raised in one hand cocked back' },
  { id: 'p250', name: 'P250', cat: 'pistol', side: 'both', icon: 'gun-pistol', action: 'held in two hands low ready' },

  // Rifles
  { id: 'ak47', name: 'AK-47', cat: 'rifle', side: 't', icon: 'gun-ak', action: 'gripping the wooden stock and foregrip, right index finger on trigger' },
  { id: 'm4a1', name: 'M4A1', cat: 'rifle', side: 'ct', icon: 'gun-m4', action: 'gripping the collapsible stock and foregrip, right index finger on trigger' },
  { id: 'galil', name: 'Galil', cat: 'rifle', side: 't', icon: 'gun-ak', action: 'held in both hands low ready' },
  { id: 'famas', name: 'FAMAS', cat: 'rifle', side: 'ct', icon: 'gun-m4', action: 'held in both hands low ready' },
  { id: 'aug', name: 'AUG', cat: 'rifle', side: 'ct', icon: 'gun-m4', action: 'with scope raised, both hands on grip' },
  { id: 'sg553', name: 'SG 553', cat: 'rifle', side: 't', icon: 'gun-ak', action: 'with scope raised, both hands on grip' },

  // Sniper
  { id: 'awp', name: 'AWP', cat: 'sniper', side: 'both', icon: 'gun-awp', action: 'scoped in, both hands on stock and grip' },
  { id: 'scout', name: 'SSG 08', cat: 'sniper', side: 'both', icon: 'gun-awp', action: 'scoped in, both hands on stock' },

  // SMG
  { id: 'mac10', name: 'MAC-10', cat: 'smg', side: 't', icon: 'gun-smg', action: 'held in one hand racked back' },
  { id: 'mp9', name: 'MP9', cat: 'smg', side: 'ct', icon: 'gun-smg', action: 'held in two hands low ready' },
  { id: 'ump45', name: 'UMP-45', cat: 'smg', side: 'both', icon: 'gun-smg', action: 'held in two hands low ready' },
  { id: 'p90', name: 'P90', cat: 'smg', side: 'both', icon: 'gun-smg', action: 'held in two hands, bullpup grip' },

  // Other
  { id: 'knife', name: 'Knife', cat: 'other', side: 'both', icon: 'gun-knife', action: 'flipped mid-spin in one hand' },
  { id: 'c4', name: 'C4', cat: 'other', side: 't', icon: 'gun-c4', action: 'held in one hand, keypad glowing' },
  { id: 'zeus', name: 'Zeus x27', cat: 'other', side: 'both', icon: 'gun-zeus', action: 'crackling with electricity in one hand' },
];

const POSES = {
  ready: 'in a ready aiming stance with feet shoulder-width apart',
  aim: 'aiming down sights with both eyes open',
  relaxed: 'in a relaxed hold, gun at low ready',
  win: 'in a victorious celebratory pose with one arm raised',
};

const ATMOSPHERES = {
  day: { desc: 'bright daylight with strong dramatic shadows' },
  golden: { desc: 'warm dusty golden hour lighting with long orange shadows' },
  night: { desc: 'dark night scene with cool blue moonlight and rim lighting' },
  fog: { desc: 'thick dusty fog with low visibility and god rays' },
};

const EFFECTS = {
  muzzle: 'muzzle flash bursting from the barrel',
  smoke: 'wisps of light smoke drifting around the figure',
  dust: 'dust particles floating in the air, backlit by the sun',
  tracers: 'subtle bullet tracers streaking past in the background',
};

const GRADES = {
  classic: 'classic clean pixel art color grade',
  warm: 'warm dusty orange tinted color grade',
  cool: 'cool blue cinematic color grade',
  contrast: 'high contrast bold color grade with deep blacks',
};

/* ---------- STATE ---------- */

const state = {
  side: 'ct',
  map: 'de_dust2',
  location: 'A Bombsite',
  gun: 'ak47',
  gunCat: 'all',
  pose: 'ready',
  atmo: 'day',
  fx: [],
  grade: 'classic',
  overlay: '',
  lastResult: null,
};

/* ---------- STYLE PREFIX ---------- */

const STYLE_PREFIX =
  'Create a high-quality vertical smartphone wallpaper in authentic retro pixel art style inspired by Counter-Strike 1.6 (2000). Crisp visible pixels, dithering, limited vibrant color palette, blocky yet detailed character models like classic CS 1.6 low-poly translated into pixel art, dramatic cinematic lighting with strong shadows, atmospheric particles and dust. Vertical 9:16 composition, epic and nostalgic, perfect as phone lockscreen or wallpaper. Sharp pixel edges, professional composition. No text, no logos, no watermarks, no HUD, no modern UI elements.';

const NEGATIVE =
  'blurry, lowres, deformed hands, extra fingers, bad anatomy, photorealistic, 3D render, smooth shading, modern graphics, text, logo, watermark, UI, HUD, cartoon, anime, cute, oversaturated, washed out, duplicate elements, artifacts';

/* ---------- DOM HELPERS ---------- */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

/* ---------- INIT ---------- */

document.addEventListener('DOMContentLoaded', () => {
  populateLocations();
  renderGuns('all');
  bindEvents();
  updatePrompt();
  registerSW();
  bindInstall();
});

function populateLocations() {
  const sel = $('#mapLocation');
  sel.innerHTML = MAPS[state.map].locations
    .map((loc) => `<option value="${loc}">${loc.toUpperCase()}</option>`)
    .join('');
  sel.value = state.location;
}

function renderGuns(cat) {
  const grid = $('#gunGrid');
  const list = cat === 'all' ? GUNS : GUNS.filter((g) => g.cat === cat);
  grid.innerHTML = list
    .map(
      (g) => `
      <button class="gun-card ${g.id === state.gun ? 'selected' : ''}" data-gun="${g.id}">
        <div class="gun-icon"><div class="${g.icon}"></div></div>
        <span class="gun-name">${g.name.toUpperCase()}</span>
        <span class="gun-side ${g.side}">${g.side.toUpperCase()}</span>
      </button>`
    )
    .join('');
}

function bindEvents() {
  // Side
  $$('#sideGrid .side-card').forEach((card) => {
    card.addEventListener('click', () => {
      $$('#sideGrid .side-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');
      state.side = card.dataset.side;
      updatePrompt();
    });
  });

  // Map
  $$('#mapScroll .map-card').forEach((card) => {
    card.addEventListener('click', () => {
      $$('#mapScroll .map-card').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');
      state.map = card.dataset.map;
      state.location = MAPS[state.map].locations[0];
      populateLocations();
      updatePrompt();
    });
  });

  // Location
  $('#mapLocation').addEventListener('change', (e) => {
    state.location = e.target.value;
    updatePrompt();
  });

  // Gun tabs
  $$('#gunTabs .gun-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      $$('#gunTabs .gun-tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      state.gunCat = tab.dataset.cat;
      renderGuns(state.gunCat);
    });
  });

  // Gun cards (delegated)
  $('#gunGrid').addEventListener('click', (e) => {
    const card = e.target.closest('.gun-card');
    if (!card) return;
    $$('#gunGrid .gun-card').forEach((c) => c.classList.remove('selected'));
    card.classList.add('selected');
    state.gun = card.dataset.gun;
    updatePrompt();
  });

  // Pose
  $('#poseRow').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    $$('#poseRow .chip').forEach((c) => c.classList.remove('selected'));
    chip.classList.add('selected');
    state.pose = chip.dataset.pose;
    updatePrompt();
  });

  // Atmosphere
  $('#atmoRow').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    $$('#atmoRow .chip').forEach((c) => c.classList.remove('selected'));
    chip.classList.add('selected');
    state.atmo = chip.dataset.atmo;
    updatePrompt();
  });

  // Effects (multi-select)
  $('#fxRow').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    const fx = chip.dataset.fx;
    if (state.fx.includes(fx)) {
      state.fx = state.fx.filter((f) => f !== fx);
      chip.classList.remove('selected');
    } else {
      state.fx.push(fx);
      chip.classList.add('selected');
    }
    updatePrompt();
  });

  // Grade
  $('#gradeRow').addEventListener('click', (e) => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    $$('#gradeRow .chip').forEach((c) => c.classList.remove('selected'));
    chip.classList.add('selected');
    state.grade = chip.dataset.grade;
    updatePrompt();
  });

  // Overlay text
  $('#overlayText').addEventListener('input', (e) => {
    state.overlay = e.target.value.trim();
    updatePrompt();
  });

  // Copy prompt
  $('#copyPrompt').addEventListener('click', copyPrompt);

  // Generate
  $('#generateBtn').addEventListener('click', generate);
  $('#regenBtn').addEventListener('click', generate);
  $('#surpriseBtn').addEventListener('click', surprise);
  $('#editBtn').addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  // Collapsible fine tune
  $('#advToggle').addEventListener('click', () => {
    const step = $('#advToggle').closest('.step');
    step.classList.toggle('collapsed');
  });

  // Download
  $$('.dl-btn').forEach((btn) => {
    btn.addEventListener('click', () => download(btn.dataset.size));
  });
}

/* ---------- PROMPT BUILDER ---------- */

function buildPrompt() {
  const side = SIDES[state.side];
  const map = MAPS[state.map];
  const gun = GUNS.find((g) => g.id === state.gun);
  const pose = POSES[state.pose];
  const atmo = ATMOSPHERES[state.atmo].desc;
  const grade = GRADES[state.grade];
  const fx = state.fx.length
    ? state.fx.map((f) => EFFECTS[f]).join(', ')
    : '';

  const mainScene =
    `A ${side.short} from Counter-Strike 1.6 standing ${pose} on the ${state.location} of ${map.label} map, ` +
    `holding a ${gun.name} in both hands ${gun.action}, wearing ${side.clothing}, ${atmo}. ` +
    `Background shows ${map.features}. ` +
    (fx ? `${fx}. ` : '') +
    `${grade}. ` +
    `Highly detailed pixel art, sharp pixels, subtle film grain and CRT scanline feel, rule of thirds composition.` +
    (state.overlay ? ` Include the text "${state.overlay}" rendered in a retro pixel font in the corner.` : '');

  return { positive: `${STYLE_PREFIX}\n\n${mainScene}`, negative: NEGATIVE };
}

function updatePrompt() {
  const p = buildPrompt();
  $('#promptPreview').textContent = p.positive;
}

/* ---------- ACTIONS ---------- */

async function copyPrompt() {
  const text = $('#promptPreview').textContent;
  try {
    await navigator.clipboard.writeText(text);
    toast('PROMPT COPIED');
  } catch (e) {
    // Fallback
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    toast('PROMPT COPIED');
  }
}

function surprise() {
  // Randomize all selections
  const sides = Object.keys(SIDES);
  const maps = Object.keys(MAPS);
  const cats = ['pistol', 'rifle', 'sniper', 'smg', 'other'];
  const poses = Object.keys(POSES);
  const atmos = Object.keys(ATMOSPHERES);
  const grades = Object.keys(GRADES);
  const allFx = Object.keys(EFFECTS);

  state.side = sides[Math.floor(Math.random() * sides.length)];
  state.map = maps[Math.floor(Math.random() * maps.length)];
  state.location = MAPS[state.map].locations[Math.floor(Math.random() * MAPS[state.map].locations.length)];
  const cat = cats[Math.floor(Math.random() * cats.length)];
  const pool = GUNS.filter((g) => g.cat === cat);
  state.gun = pool[Math.floor(Math.random() * pool.length)].id;
  state.gunCat = cat;
  state.pose = poses[Math.floor(Math.random() * poses.length)];
  state.atmo = atmos[Math.floor(Math.random() * atmos.length)];
  state.grade = grades[Math.floor(Math.random() * grades.length)];
  // 0-2 random effects
  const fxCount = Math.floor(Math.random() * 3);
  state.fx = [];
  for (let i = 0; i < fxCount; i++) {
    const f = allFx[Math.floor(Math.random() * allFx.length)];
    if (!state.fx.includes(f)) state.fx.push(f);
  }
  state.overlay = Math.random() > 0.7 ? (Math.random() > 0.5 ? 'GL HF' : '16-14') : '';

  // Reflect into UI
  $$('#sideGrid .side-card').forEach((c) => c.classList.toggle('selected', c.dataset.side === state.side));
  $$('#mapScroll .map-card').forEach((c) => c.classList.toggle('selected', c.dataset.map === state.map));
  populateLocations();
  $$('#gunTabs .gun-tab').forEach((t) => t.classList.toggle('active', t.dataset.cat === state.gunCat));
  renderGuns(state.gunCat);
  $$('#poseRow .chip').forEach((c) => c.classList.toggle('selected', c.dataset.pose === state.pose));
  $$('#atmoRow .chip').forEach((c) => c.classList.toggle('selected', c.dataset.atmo === state.atmo));
  $$('#fxRow .chip').forEach((c) => c.classList.toggle('selected', state.fx.includes(c.dataset.fx)));
  $$('#gradeRow .chip').forEach((c) => c.classList.toggle('selected', c.dataset.grade === state.grade));
  $('#overlayText').value = state.overlay;
  updatePrompt();
  toast('SURPRISE LOADED');
}

/* ---------- IMAGE GENERATION ---------- */

async function generate() {
  const area = $('#resultArea');
  const ph = $('#resultPlaceholder');
  const img = $('#resultImg');
  area.classList.remove('hidden');
  img.classList.add('hidden');
  ph.classList.remove('hidden');

  // Scroll into view
  area.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const p = buildPrompt();

  // Try the OpenClaw image generation endpoint (relative path, no auth, PWA-friendly)
  // Falls back to a placeholder grid if backend is unavailable.
  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        positive: p.positive,
        negative: p.negative,
        width: 1080,
        height: 1920,
        seed: Math.floor(Math.random() * 1e9),
      }),
    });
    if (!res.ok) throw new Error('API ' + res.status);
    const data = await res.json();
    if (data.image) {
      img.src = data.image;
      img.onload = () => {
        ph.classList.add('hidden');
        img.classList.remove('hidden');
        state.lastResult = data.image;
        toast('WALLPAPER READY');
      };
      return;
    }
    throw new Error('no image in response');
  } catch (err) {
    // Fallback: render a procedural pixel-art placeholder preview
    renderPlaceholder();
  }
}

function renderPlaceholder() {
  const ph = $('#resultPlaceholder');
  const img = $('#resultImg');
  ph.classList.add('hidden');
  img.classList.remove('hidden');

  // Build a small canvas with the selections, then upscale for the retro look
  const c = document.createElement('canvas');
  c.width = 1080; c.height = 1920;
  const ctx = c.getContext('2d');
  ctx.imageSmoothingEnabled = false;

  // Background gradient by map
  const mapColors = {
    de_dust2: ['#c8945a', '#8a5a30'],
    de_inferno: ['#b04030', '#4a1810'],
    de_train: ['#4a504a', '#1a201a'],
    de_nuke: ['#5a6a3a', '#1a2010'],
    de_mirage: ['#d8b878', '#6a5028'],
    de_cbble: ['#608050', '#284018'],
  };
  const grad = ctx.createLinearGradient(0, 0, 0, 1920);
  const colors = mapColors[state.map] || ['#888', '#222'];
  grad.addColorStop(0, colors[0]);
  grad.addColorStop(1, colors[1]);
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 1080, 1920);

  // Vignette
  const vg = ctx.createRadialGradient(540, 960, 200, 540, 960, 1400);
  vg.addColorStop(0, 'rgba(0,0,0,0)');
  vg.addColorStop(1, 'rgba(0,0,0,0.7)');
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, 1080, 1920);

  // Floor line
  ctx.fillStyle = 'rgba(0,0,0,0.4)';
  ctx.fillRect(0, 1300, 1080, 4);
  ctx.fillRect(0, 1310, 1080, 2);

  // Character (big pixel)
  const charColor = state.side === 'ct' ? '#4a8fd6' : '#c97a3a';
  const cx = 540, cy = 900;

  // Body
  ctx.fillStyle = charColor;
  ctx.fillRect(cx - 120, cy - 80, 240, 280);
  ctx.fillStyle = 'rgba(0,0,0,0.3)';
  ctx.fillRect(cx + 60, cy - 80, 60, 280);

  // Helmet/head
  ctx.fillStyle = state.side === 'ct' ? '#2a5a8a' : '#1a1a1a';
  ctx.fillRect(cx - 80, cy - 200, 160, 120);
  // Eyes
  ctx.fillStyle = '#fff';
  ctx.fillRect(cx - 50, cy - 160, 24, 18);
  ctx.fillRect(cx + 26, cy - 160, 24, 18);
  ctx.fillStyle = '#000';
  ctx.fillRect(cx - 40, cy - 156, 8, 8);
  ctx.fillRect(cx + 36, cy - 156, 8, 8);

  // Gun
  const gunColors = {
    ak47: ['#5a4028', '#3a2810'],
    m4a1: ['#4a4a4a', '#1a1a1a'],
    awp: ['#5a5a5a', '#1a1a1a'],
    glock: ['#2a2a2a', '#1a1a1a'],
    usp: ['#2a2a2a', '#1a1a1a'],
    deagle: ['#2a2a2a', '#1a1a1a'],
    p250: ['#2a2a2a', '#1a1a1a'],
    galil: ['#5a4028', '#3a2810'],
    famas: ['#4a4a4a', '#1a1a1a'],
    aug: ['#4a4a4a', '#1a1a1a'],
    sg553: ['#5a4028', '#3a2810'],
    scout: ['#5a5a5a', '#1a1a1a'],
    mac10: ['#2a2a2a', '#1a1a1a'],
    mp9: ['#2a2a2a', '#1a1a1a'],
    ump45: ['#2a2a2a', '#1a1a1a'],
    p90: ['#2a2a2a', '#1a1a1a'],
    knife: ['#c0c0c0', '#4a3018'],
    c4: ['#4a4030', '#1a1208'],
    zeus: ['#1a1a1a', '#c0c0c0'],
  };
  const gc = gunColors[state.gun] || ['#888', '#444'];
  ctx.fillStyle = gc[0];
  ctx.fillRect(cx - 100, cy + 40, 220, 32);
  ctx.fillStyle = gc[1];
  ctx.fillRect(cx - 100, cy + 60, 220, 12);
  // Muzzle flash
  if (state.fx.includes('muzzle')) {
    ctx.fillStyle = '#f0d250';
    ctx.fillRect(cx + 120, cy + 44, 60, 24);
    ctx.fillStyle = '#fff';
    ctx.fillRect(cx + 140, cy + 48, 30, 16);
  }

  // Dust particles
  if (state.fx.includes('dust') || state.atmo === 'fog' || state.atmo === 'golden') {
    ctx.fillStyle = 'rgba(255,220,160,0.4)';
    for (let i = 0; i < 60; i++) {
      const x = Math.random() * 1080;
      const y = Math.random() * 1920;
      const s = Math.random() * 8 + 2;
      ctx.fillRect(x, y, s, s);
    }
  }

  // Smoke
  if (state.fx.includes('smoke')) {
    ctx.fillStyle = 'rgba(200,200,200,0.25)';
    for (let i = 0; i < 30; i++) {
      const x = Math.random() * 1080;
      const y = 200 + Math.random() * 1500;
      const s = Math.random() * 60 + 20;
      ctx.fillRect(x, y, s, s);
    }
  }

  // Tracers
  if (state.fx.includes('tracers')) {
    ctx.fillStyle = '#f0d250';
    for (let i = 0; i < 5; i++) {
      const y = 200 + Math.random() * 1500;
      ctx.fillRect(0, y, 1080, 2);
    }
  }

  // Title plate
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(60, 60, 960, 100);
  ctx.strokeStyle = '#f0d250';
  ctx.lineWidth = 2;
  ctx.strokeRect(60, 60, 960, 100);
  ctx.fillStyle = '#f0d250';
  ctx.font = 'bold 56px monospace';
  ctx.textAlign = 'center';
  ctx.fillText('PIXELSTRIKE 1.6', 540, 128);

  // Bottom plate
  ctx.fillStyle = 'rgba(0,0,0,0.7)';
  ctx.fillRect(60, 1760, 960, 100);
  ctx.strokeStyle = '#4a8fd6';
  ctx.strokeRect(60, 1760, 960, 100);
  ctx.fillStyle = '#fff';
  ctx.font = 'bold 28px monospace';
  ctx.fillText(
    `${state.side.toUpperCase()} • ${MAPS[state.map].label} • ${GUNS.find((g) => g.id === state.gun).name.toUpperCase()}`,
    540,
    1810
  );

  // Overlay text
  if (state.overlay) {
    ctx.fillStyle = '#f0d250';
    ctx.font = 'bold 64px monospace';
    ctx.fillText(state.overlay.toUpperCase(), 540, 1640);
  }

  // Scanlines
  ctx.fillStyle = 'rgba(0,0,0,0.15)';
  for (let y = 0; y < 1920; y += 4) {
    ctx.fillRect(0, y, 1080, 1);
  }

  img.src = c.toDataURL('image/png');
  img.onload = () => {
    state.lastResult = img.src;
    toast('PLACEHOLDER RENDERED');
  };
}

/* ---------- DOWNLOAD ---------- */

function download(size) {
  if (!state.lastResult) {
    toast('NOTHING TO DOWNLOAD');
    return;
  }
  const targetW = size === '1440' ? 1440 : 1080;
  const targetH = size === '1440' ? 2560 : 1920;

  const src = new Image();
  src.onload = () => {
    const c = document.createElement('canvas');
    c.width = targetW;
    c.height = targetH;
    const ctx = c.getContext('2d');
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, 0, 0, targetW, targetH);
    // Re-add scanlines for retro feel
    ctx.fillStyle = 'rgba(0,0,0,0.12)';
    const step = targetH / 480;
    for (let y = 0; y < targetH; y += step) {
      ctx.fillRect(0, y, targetW, 1);
    }
    c.toBlob((blob) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `pixelstrike-${state.side}-${state.gun}-${state.map}-${targetW}x${targetH}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast('DOWNLOADED');
    }, 'image/png');
  };
  src.src = state.lastResult;
}

/* ---------- PWA ---------- */

function registerSW() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {
      /* fail silently in dev */
    });
  }
}

let deferredPrompt = null;
function bindInstall() {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    $('#installBtn').classList.remove('hidden');
  });
  $('#installBtn').addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    $('#installBtn').classList.add('hidden');
  });
}

/* ---------- TOAST ---------- */

let toastTimer = null;
function toast(msg) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 1800);
}
