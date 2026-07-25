/* 逆命大郎 登入 — boot, 2D fallback, form logic */
(function () {
  'use strict';

  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fxState = { running: true };

  /* ============================================================
     2D FALLBACK PARTICLES (no WebGL)
     ============================================================ */
  function startFallback2D() {
    document.body.classList.add('fallback-2d');
    if (reduceMotion) return;

    const dustCanvas = document.getElementById('dust-canvas');
    const dustCtx = dustCanvas.getContext('2d');
    const emberCanvas = document.getElementById('ember-canvas');
    const emberCtx = emberCanvas.getContext('2d');

    let dust = [];
    let embers = [];
    let raf = 0;

    function resize() {
      dustCanvas.width = emberCanvas.width = innerWidth * devicePixelRatio;
      dustCanvas.height = emberCanvas.height = innerHeight * devicePixelRatio;
      dustCanvas.style.width = emberCanvas.style.width = innerWidth + 'px';
      dustCanvas.style.height = emberCanvas.style.height = innerHeight + 'px';
      dustCtx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
      emberCtx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
    }

    function resetEmber(e) {
      e.x = Math.random() * innerWidth;
      e.y = innerHeight + 10 + Math.random() * 80;
      e.r = 0.8 + Math.random() * 2.2;
      e.vx = -0.2 + Math.random() * 0.4;
      e.vy = -(0.35 + Math.random() * 0.9);
      e.a = 0.25 + Math.random() * 0.55;
      e.life = 0;
      e.max = 220 + Math.random() * 320;
      e.wobble = Math.random() * Math.PI * 2;
      return e;
    }

    function spawn() {
      const dn = innerWidth < 600 ? 55 : 110;
      dust = [];
      for (let i = 0; i < dn; i++) {
        dust.push({
          x: Math.random() * innerWidth,
          y: Math.random() * innerHeight,
          r: 0.4 + Math.random() * 1.8,
          vx: 0.15 + Math.random() * 0.55,
          vy: -0.05 + Math.random() * 0.2,
          a: 0.12 + Math.random() * 0.35,
          phase: Math.random() * Math.PI * 2,
          spin: 0.004 + Math.random() * 0.01,
          warm: Math.random() > 0.65
        });
      }
      const en = innerWidth < 600 ? 14 : 28;
      embers = [];
      for (let i = 0; i < en; i++) embers.push(resetEmber({}));
    }

    function tick() {
      if (!fxState.running || document.hidden) return;

      dustCtx.clearRect(0, 0, innerWidth, innerHeight);
      for (const p of dust) {
        p.phase += p.spin;
        p.x += p.vx + Math.sin(p.phase) * 0.15;
        p.y += p.vy + Math.cos(p.phase * 0.7) * 0.08;
        if (p.x > innerWidth + 10) p.x = -10;
        if (p.x < -10) p.x = innerWidth + 10;
        if (p.y < -10) p.y = innerHeight + 10;
        if (p.y > innerHeight + 10) p.y = -10;

        const g = dustCtx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 3);
        if (p.warm) {
          g.addColorStop(0, 'rgba(232, 200, 140, ' + p.a + ')');
          g.addColorStop(1, 'rgba(180, 140, 80, 0)');
        } else {
          g.addColorStop(0, 'rgba(220, 225, 230, ' + p.a + ')');
          g.addColorStop(1, 'rgba(180, 190, 200, 0)');
        }
        dustCtx.beginPath();
        dustCtx.fillStyle = g;
        dustCtx.arc(p.x, p.y, p.r * 3, 0, Math.PI * 2);
        dustCtx.fill();
      }

      emberCtx.clearRect(0, 0, innerWidth, innerHeight);
      for (const e of embers) {
        e.life++;
        e.wobble += 0.03;
        e.x += e.vx + Math.sin(e.wobble) * 0.35;
        e.y += e.vy;
        const fade = 1 - e.life / e.max;
        const alpha = e.a * fade;

        if (e.life > e.max || e.y < -20) {
          resetEmber(e);
          continue;
        }

        const g = emberCtx.createRadialGradient(e.x, e.y, 0, e.x, e.y, e.r * 4);
        g.addColorStop(0, 'rgba(255, 200, 120, ' + alpha + ')');
        g.addColorStop(0.4, 'rgba(220, 120, 60, ' + alpha * 0.55 + ')');
        g.addColorStop(1, 'rgba(80, 30, 10, 0)');
        emberCtx.beginPath();
        emberCtx.fillStyle = g;
        emberCtx.arc(e.x, e.y, e.r * 4, 0, Math.PI * 2);
        emberCtx.fill();

        emberCtx.strokeStyle = 'rgba(255, 180, 100, ' + alpha * 0.25 + ')';
        emberCtx.lineWidth = 0.6;
        emberCtx.beginPath();
        emberCtx.moveTo(e.x, e.y);
        emberCtx.lineTo(e.x - e.vx * 6, e.y - e.vy * 8);
        emberCtx.stroke();
      }

      raf = requestAnimationFrame(tick);
    }

    resize();
    spawn();
    tick();

    addEventListener('resize', () => { resize(); spawn(); });
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) tick();
    });

    window.__stopFallback = () => { cancelAnimationFrame(raf); };
  }

  /* ============================================================
     BOOT FX
     ============================================================ */
  let use3D = false;
  if (!reduceMotion && typeof window.initLoginScene === 'function') {
    try {
      use3D = window.initLoginScene(fxState);
    } catch (e) {
      use3D = false;
    }
  }
  if (!use3D) startFallback2D();

  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && window.__loginThree && fxState.running) window.__loginThree.resume();
  });

  /* ============================================================
     FORM (visual prototype only)
     ============================================================ */
  const panel = document.getElementById('login-panel');
  const form = document.getElementById('login-form');
  const err = document.getElementById('error-msg');
  const veil = document.getElementById('enter-veil');

  function showError(msg) {
    err.textContent = msg;
    err.classList.add('show');
    panel.classList.remove('shake');
    void panel.offsetWidth;
    panel.classList.add('shake');
  }

  function clearError() {
    err.classList.remove('show');
    err.textContent = '';
  }

  function playEnter(label) {
    clearError();
    veil.classList.add('active');
    fxState.running = false;
    if (window.__stopFallback) window.__stopFallback();
    setTimeout(() => {
      const note = document.createElement('div');
      note.style.cssText = 'position:fixed;inset:0;z-index:101;display:grid;place-items:center;color:#e8e4d9;font-family:inherit;text-align:center;padding:24px;background:#030508;';
      note.innerHTML =
        '<div>' +
        '<div style="font-size:1.6rem;letter-spacing:0.4em;margin-bottom:16px;color:#e8c96a;">已進入門扉</div>' +
        '<div style="font-size:0.9rem;letter-spacing:0.18em;color:#a8a494;line-height:1.9;">' +
        label + '<br>' +
        '此頁為登入視覺原型 · 尚未接入《逆命大郎》本體<br>' +
        '<button id="back-btn" style="margin-top:28px;padding:12px 28px;background:transparent;border:1px solid rgba(201,168,76,0.45);color:#e8e4d9;letter-spacing:0.28em;cursor:pointer;font-family:inherit;">返回登入</button>' +
        '</div></div>';
      document.body.appendChild(note);
      document.getElementById('back-btn').onclick = () => {
        note.remove();
        veil.classList.remove('active');
        fxState.running = true;
        if (window.__loginThree) window.__loginThree.resume();
      };
    }, 950);
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('account').value.trim();
    const pass = document.getElementById('secret').value;
    if (!name) {
      showError('請留下少俠名號');
      return;
    }
    if (!pass) {
      showError('請輸入江湖密語');
      return;
    }
    playEnter('少俠「' + name + '」· 帳號登入（示範）');
  });

  document.getElementById('btn-guest').addEventListener('click', () => {
    playEnter('遊客模式（示範）');
  });

  document.getElementById('link-demo').addEventListener('click', () => {
    document.getElementById('account').value = '青石少年';
    document.getElementById('secret').value = '江湖';
    clearError();
  });

  document.getElementById('link-clear').addEventListener('click', () => {
    document.getElementById('account').value = '';
    document.getElementById('secret').value = '';
    clearError();
  });
})();
