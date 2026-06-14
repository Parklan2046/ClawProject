/* Pulse — Live Football x Markets
   Connects to /ws, renders match cards, sparklines, pulse bars,
   "markets moved" feed, hot markets panel. */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const state = {
  matches: [],
  marketsUnmatched: [],
  lastUpdate: {},
  movedLog: [],          // {ts, title, pct, marketId, dir}
  filter: 'all',
};

let ws = null;
let reconnectTimer = null;
const FLASH_DURATION = 1800;

/* ------------------------------------------------------------------ */
/* Connection                                                          */
/* ------------------------------------------------------------------ */
function setConn(status) {
  const el = $('#conn');
  el.classList.remove('live', 'stale', 'down');
  el.classList.add(status);
  const txt = el.querySelector('.conn-text');
  txt.textContent = t(status) || status;
}

function connect() {
  setConn('connecting');
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}${location.pathname.replace(/\/$/,"")}/ws`);
  ws.onopen = () => { setConn('live'); };
  ws.onclose = () => {
    setConn('down');
    if (!reconnectTimer) reconnectTimer = setTimeout(() => { reconnectTimer = null; connect(); }, 2000);
  };
  ws.onerror = () => { /* onclose handles it */ };
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === 'snapshot') applySnapshot(msg);
    } catch (e) {
      console.error('bad ws msg', e);
    }
  };
}

function applySnapshot(msg) {
  const before = new Map(state.matches.map(m => [m.id, m]));
  state.matches = msg.matches || [];
  state.marketsUnmatched = msg.markets_unmatched || [];
  state.lastUpdate = msg.last_update || {};

  // detect market moves (compare attached markets)
  for (const m of state.matches) {
    if (!m.market) continue;
    const prev = before.get(m.id);
    if (!prev || !prev.market) continue;
    const prevPrice = topOutcomePrice(prev.market);
    const curPrice = topOutcomePrice(m.market);
    if (prevPrice && curPrice && Math.abs(curPrice - prevPrice) > 0.01) {
      const pct = (curPrice - prevPrice) * 100;
      pushMoved(m, pct);
    }
  }

  renderAll();
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */
function topOutcomePrice(market) {
  const pm = market?.primary_market;
  if (!pm || !pm.outcomes) return null;
  return Math.max(...pm.outcomes.map(o => o.price || 0));
}

function fmtTime(unix) {
  if (!unix) return '—';
  const d = new Date(unix * 1000);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function fmtRelTime(unix) {
  if (!unix) return '—';
  const s = Math.floor(Date.now() / 1000 - unix);
  if (s < 5) return t('justNow');
  if (s < 60) return `${s}${t('secAgo')}`;
  if (s < 3600) return `${Math.floor(s / 60)}${t('minAgo')}`;
  return `${Math.floor(s / 3600)}${t('hrAgo')}`;
}

function teamInitial(name) {
  return countryFlag(name) || (tname(name) || '?').trim().charAt(0);
}

function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    e.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  }
  return e;
}

function svgSparkline(values, opts = {}) {
  const w = opts.w || 220, h = opts.h || 28;
  if (!values || values.length < 2) return '';
  const min = Math.min(...values), max = Math.max(...values);
  const range = max - min || 1;
  const step = w / (values.length - 1);
  const points = values.map((v, i) => {
    const x = i * step;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });
  const lineD = `M ${points.join(' L ')}`;
  const areaD = `${lineD} L ${w},${h} L 0,${h} Z`;
  return `
    <svg class="sparkline" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
      <defs>
        <linearGradient id="spark-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#66e3ff" stop-opacity="0.6"/>
          <stop offset="100%" stop-color="#66e3ff" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <path class="area" d="${areaD}" />
      <path d="${lineD}" />
    </svg>`;
}

/* ------------------------------------------------------------------ */
/* Render: match card                                                  */
/* ------------------------------------------------------------------ */
function renderMatchCard(m) {
  const card = el('article', { class: `match-card ${m.state}` });
  const state = m.state;
  const stateLabel = state === 'in' ? t('stateLive') : (state === 'pre' ? t('stateSoon') : t('stateFT'));
  const statePill = el('span', { class: `state-pill ${state === 'in' ? 'live' : (state === 'pre' ? 'pre' : 'post')}` });
  if (state === 'in') statePill.appendChild(el('span', { class: 'blink' }));
  statePill.appendChild(document.createTextNode(stateLabel + (m.clock ? ` · ${m.clock}` : '')));

  const leagueTag = el('div', { class: 'league-tag' },
    el('span', { class: 'code' }, '🏆'),
    el('span', {}, tname(m.league) || m.league || ''),
  );

  const head = el('div', { class: 'match-head' }, leagueTag, statePill);
  card.appendChild(head);

  // teams
  const mkTeam = (side) => {
    const t = m[side];
    const isWinner = m.state === 'post' && t.winner === true;
    const logo = t.logo
      ? el('img', { class: 'team-logo', src: t.logo, alt: t.name, loading: 'lazy' })
      : el('div', { class: 'team-logo fallback' }, teamInitial(t.name));
    return el('div', { class: `team-row ${isWinner ? 'winner' : ''}` },
      logo,
      el('div', { class: 'team-name' }, tname(t.short || t.name) || '—'),
      el('div', { class: 'team-score' }, String(t.score)),
    );
  };
  const body = el('div', { class: 'match-body' }, mkTeam('home'), mkTeam('away'));
  card.appendChild(body);

  // meta (venue / kickoff)
  const meta = el('div', { class: 'match-meta' },
    el('span', {}, tname(m.venue) || (m.state === 'pre' ? fmtTime(Date.parse(m.date) / 1000) : '')),
    m.state === 'pre' ? el('span', { class: 'clock' }, t('kickoff')) : null,
  );
  card.appendChild(meta);

  // market row
  if (m.market) {
    const pm = m.market.primary_market;
    const outcomes = (pm.outcomes || []).slice(0, 3);
    const favIdx = outcomes.reduce((best, o, i) => (o.price > (outcomes[best]?.price || 0) ? i : best), 0);
    const pricePills = outcomes.map((o, i) => {
      const pct = o.price != null ? `${Math.round(o.price * 100)}¢` : '—';
      return el('span', { class: `outcome-pill ${i === favIdx ? 'fav' : ''}` },
        el('span', { class: 'name' }, tname(o.name).slice(0, 8)),
        el('span', {}, pct),
      );
    });
    const marketQ = el('div', { class: 'market-q' }, pm.question || m.market.title);
    const marketPrices = el('div', { class: 'market-prices' }, ...pricePills);
    const marketRow = el('div', { class: 'market-row' }, marketQ, marketPrices);
    card.appendChild(marketRow);

    // edge badge + sparkline
    const edge = m.edge || {};
    if (edge.has_history) {
      const badge = el('div', { class: `edge-badge ${edge.direction}` });
      const sign = edge.edge_pct > 0 ? '+' : '';
      badge.appendChild(document.createTextNode(`${sign}${edge.edge_pct.toFixed(1)}¢ ${t('edgeLabel')}`));
      if (Math.abs(edge.edge_pct) > 3) badge.classList.add('hot');
      const sparkWrap = el('div', { class: 'sparkline-wrap', html: svgSparkline(edge.sparkline) });
      card.appendChild(badge);
      card.appendChild(sparkWrap);
    }
  } else {
    // no market matched — show a subtle line
    card.appendChild(el('div', { class: 'match-meta' },
      el('span', { style: 'opacity:0.5' }, t('noMarket')),
    ));
  }

  // pulse bar — speed driven by edge volatility
  const speed = 1.5 + Math.max(0, 4 - (m.edge?.volatility || 0) * 80);
  const opacity = m.market ? Math.min(1, 0.3 + (m.edge?.volatility || 0) * 2) : 0.2;
  const bar = el('div', { class: 'pulse-bar' });
  bar.style.setProperty('--pulse-speed', `${Math.max(0.8, speed).toFixed(2)}s`);
  bar.style.setProperty('--pulse-opacity', String(opacity));
  card.appendChild(bar);

  return card;
}

/* ------------------------------------------------------------------ */
/* Render: moved feed                                                  */
/* ------------------------------------------------------------------ */
function pushMoved(match, pct) {
  const id = match.market?.id;
  if (!id) return;
  // de-dupe within 30s
  const last = state.movedLog.find(x => x.id === id);
  if (last && (Date.now() / 1000 - last.ts) < 30) return;
  state.movedLog.unshift({
    ts: Date.now() / 1000,
    id,
    title: match.market.title,
    pct,
    dir: pct > 0 ? 'up' : 'down',
  });
  state.movedLog = state.movedLog.slice(0, 20);
  renderMoved();
}

function renderMoved() {
  const feed = $('#moved-feed');
  feed.innerHTML = '';
  if (state.movedLog.length === 0) {
    feed.appendChild(el('div', { class: 'empty' }, t('noMoves')));
    return;
  }
  for (const item of state.movedLog.slice(0, 12)) {
    const sign = item.pct > 0 ? '+' : '';
    const dirClass = item.pct > 0 ? 'up' : 'down';
    const node = el('div', { class: 'moved-item' },
      el('div', { class: 'moved-title' }, item.title),
      el('div', { class: 'moved-meta' },
        el('span', { class: `moved-pct ${dirClass}` }, `${sign}${item.pct.toFixed(1)}¢`),
        el('span', {}, fmtRelTime(item.ts)),
      ),
    );
    feed.appendChild(node);
    setTimeout(() => node.classList.add('flash'), 50);
    setTimeout(() => node.classList.remove('flash'), FLASH_DURATION);
  }
}

/* ------------------------------------------------------------------ */
/* Render: championship / futures markets                              */
/* ------------------------------------------------------------------ */
const CHAMPION_PATTERNS = [
  /win the \d{4}.*(world cup|fifa world cup)/i,
  /fifa world cup winner/i,
  /world cup \d{4} winner/i,
  /golden boot/i,
  /top scorer/i,
  /to lift the (world cup|trophy)/i,
  /to win the world cup/i,
  /most goals/i,
  /group .* winner/i,
  /to qualify.*world cup/i,
  /to reach the (final|semi|quarter)/i,
];

function isChampionMarket(market) {
  const text = (market.title || '') + ' ' + (market.primary_market?.question || '');
  return CHAMPION_PATTERNS.some(rx => rx.test(text));
}

function championCategory(market) {
  const text = (market.title || '') + ' ' + (market.primary_market?.question || '');
  if (/golden boot|top scorer|most goals/i.test(text)) return 'topScorer';
  if (/group .* winner/i.test(text)) return 'groupWinner';
  if (/reach the (final|semi|quarter)|qualif/i.test(text)) return 'knockout';
  return 'winner';
}

function renderChampion() {
  const wrap = $('#champ-markets');
  if (!wrap) return;
  wrap.innerHTML = '';
  // Pull from both attached + unmatched, de-dupe
  const seen = new Set();
  const champs = [];
  for (const m of state.matches) {
    if (m.market && isChampionMarket(m.market) && !seen.has(m.market.id)) {
      seen.add(m.market.id);
      champs.push(m.market);
    }
  }
  for (const m of (state.marketsUnmatched || [])) {
    if (isChampionMarket(m) && !seen.has(m.id)) {
      seen.add(m.id);
      champs.push(m);
    }
  }
  if (champs.length === 0) {
    wrap.appendChild(el('div', { class: 'empty' }, t('noChampions')));
    return;
  }
  // Sort by 24h volume desc
  champs.sort((a, b) => (b.primary_market?.volume_24h || 0) - (a.primary_market?.volume_24h || 0));
  for (const m of champs.slice(0, 8)) {
    const pm = m.primary_market || {};
    const cat = championCategory(m);
    const vol = pm.volume_24h || 0;
    const volStr = vol >= 1e6 ? `$${(vol / 1e6).toFixed(2)}M` :
                   vol >= 1e3 ? `$${(vol / 1e3).toFixed(1)}k` :
                   `$${vol.toFixed(0)}`;
    // Outcome pills: show the favourite(s) — first 2 outcomes with prices
    const outcomes = (pm.outcomes || []).slice(0, 2);
    const pills = outcomes.map(o => {
      const pct = o.price != null ? `${Math.round(o.price * 100)}¢` : '—';
      return el('span', { class: 'champ-outcome' },
        el('span', { class: 'champ-outcome-name' }, (o.name || '').slice(0, 10)),
        el('span', { class: 'champ-outcome-price' }, pct),
      );
    });
    const node = el('div', { class: 'hot-item champ-item' },
      el('div', { class: 'hot-q' }, pm.question || m.title),
      el('div', { class: 'champ-pills' }, ...pills),
      el('div', { class: 'hot-meta' },
        el('span', { class: `champ-tag champ-${cat}` }, t('champ_' + cat)),
        el('span', { class: 'hot-vol' }, volStr),
      ),
    );
    wrap.appendChild(node);
  }
}

/* ------------------------------------------------------------------ */
/* Render: hot markets                                                 */
/* ------------------------------------------------------------------ */
function renderHot() {
  const wrap = $('#hot-markets');
  wrap.innerHTML = '';
  const list = (state.marketsUnmatched || []).slice(0, 8);
  if (list.length === 0) {
    wrap.appendChild(el('div', { class: 'empty' }, t('noMarkets')));
    return;
  }
  for (const m of list) {
    const pm = m.primary_market || {};
    const vol = pm.volume_24h || 0;
    const volStr = vol >= 1e6 ? `$${(vol / 1e6).toFixed(2)}M` :
                   vol >= 1e3 ? `$${(vol / 1e3).toFixed(1)}k` :
                   `$${vol.toFixed(0)}`;
    const node = el('div', { class: 'hot-item' },
      el('div', { class: 'hot-q' }, pm.question || m.title),
      el('div', { class: 'hot-meta' },
        el('span', {}, t('vol24h')),
        el('span', { class: 'hot-vol' }, volStr),
      ),
    );
    wrap.appendChild(node);
  }
}

/* ------------------------------------------------------------------ */
/* Render: stats + grid                                                */
/* ------------------------------------------------------------------ */
function renderStats() {
  const live = state.matches.filter(m => m.state === 'in').length;
  $('#stat-live').textContent = String(live);
  $('#stat-markets').textContent = String(state.matches.filter(m => m.market).length + (state.marketsUnmatched?.length || 0));

  const edges = state.matches.map(m => m.edge?.edge_pct || 0).filter(e => e);
  const maxEdge = edges.length ? Math.max(...edges.map(Math.abs)) : 0;
  $('#stat-edge').textContent = maxEdge > 0 ? `${maxEdge.toFixed(1)}¢` : '—';

  const last = Math.max(state.lastUpdate.espn || 0, state.lastUpdate.polymarket || 0);
  $('#stat-update').textContent = fmtRelTime(last);
}

function isToday(unixMs) {
  if (!unixMs) return false;
  const d = new Date(unixMs);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() &&
         d.getMonth() === now.getMonth() &&
         d.getDate() === now.getDate();
}

function renderGrid() {
  const grid = $('#match-grid');
  grid.innerHTML = '';
  // Show all WC matches — no today gate. Live + finished always shown;
  // upcoming sorted soonest-first by date.
  const list = state.matches.filter(m => {
    if (state.filter === 'all') return true;
    if (state.filter === 'live') return m.state === 'in';
    if (state.filter === 'upcoming') return m.state === 'pre';
    if (state.filter === 'final') return m.state === 'post';
    return true;
  });
  // sort: live first, then upcoming by date, then final
  list.sort((a, b) => {
    const order = { in: 0, pre: 1, post: 2 };
    if (order[a.state] !== order[b.state]) return order[a.state] - order[b.state];
    if (a.state === 'pre') return new Date(a.date) - new Date(b.date);
    return 0;
  });

  if (list.length === 0) {
    grid.appendChild(el('div', { class: 'empty big' }, t('noMatchFilter')));
    return;
  }

  for (const m of list) grid.appendChild(renderMatchCard(m));
}

function renderAll() {
  renderStats();
  renderGrid();
  renderChampion();
  renderHot();
}

/* ------------------------------------------------------------------ */
/* Filter chips                                                        */
/* ------------------------------------------------------------------ */
$$('.chip').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.chip').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.filter = btn.dataset.filter;
    renderGrid();
  });
});

/* ------------------------------------------------------------------ */
/* Re-render "rel time" every 10s                                      */
/* ------------------------------------------------------------------ */
setInterval(() => {
  renderStats();
  if (state.movedLog.length) renderMoved();
}, 10000);

/* ------------------------------------------------------------------ */
/* Boot                                                                */
/* ------------------------------------------------------------------ */
connect();
// fetch initial snapshot via REST in case WS is slow
fetch('api/snapshot').then(r => r.json()).then(applySnapshot).catch(() => {});
