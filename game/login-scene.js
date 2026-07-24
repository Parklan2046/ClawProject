/* ============================================================
   俠客行 登入 — 3D Anime Night Town (Path A: A1-A5)
   Exposes window.initLoginScene() -> true if WebGL scene started
   ============================================================ */
(function () {
  'use strict';

  window.initLoginScene = function (fxState) {
    if (typeof THREE === 'undefined') return false;
    const canvas = document.getElementById('three-canvas');
    if (!canvas || !window.WebGLRenderingContext) return false;

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        powerPreference: 'high-performance'
      });
    } catch (e) {
      return false;
    }

    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    renderer.setSize(innerWidth, innerHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x131a28, 0.020);

    const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 400);
    camera.position.set(0, 3.1, 13.5);

    /* ========================================================
       A3 — toon shading foundation
       ======================================================== */
    const gradData = new Uint8Array([70, 130, 200, 255]);
    const gradientMap = new THREE.DataTexture(gradData, 4, 1, THREE.RedFormat);
    gradientMap.minFilter = THREE.NearestFilter;
    gradientMap.magFilter = THREE.NearestFilter;
    gradientMap.needsUpdate = true;

    function toon(color) {
      return new THREE.MeshToonMaterial({ color: color, gradientMap: gradientMap });
    }

    const matWallA = toon(0x4a3d30);
    const matWallB = toon(0x413729);
    const matWallC = toon(0x50423a);
    const matWood = toon(0x2b2016);
    const matWoodDark = toon(0x1d1610);
    const matRoofA = toon(0x2e4059);
    const matRoofB = toon(0x28394e);
    const matRidge = toon(0x1b2634);
    const matStone = toon(0x232a38);
    const matGround = toon(0x11141d);
    const matMountain = toon(0x161e30);
    const matSilhouette = toon(0x070a12);
    const matBanner = toon(0x8a2a20);
    const matOutline = new THREE.MeshBasicMaterial({ color: 0x05070c, side: THREE.BackSide });
    const matLanternBody = new THREE.MeshBasicMaterial({ color: 0xe04630 });
    const matLanternCap = new THREE.MeshBasicMaterial({ color: 0xd8a44a });
    const matWindowGlow = new THREE.MeshBasicMaterial({ color: 0xffb35c });
    const matWindowGlowHot = new THREE.MeshBasicMaterial({ color: 0xffd28a });

    const wallMats = [matWallA, matWallB, matWallC];
    const roofMats = [matRoofA, matRoofB];

    /* ========================================================
       A1 — curved roof geometry (upturned eaves, 翹簷)
       LatheGeometry with 4 segments = square hip roof whose
       corner silhouette follows a concave curve with an
       upturned tip.
       ======================================================== */
    function buildRoofGeometry() {
      const pts = [];
      const N = 7;
      // quadratic bezier: ridge(0,1) -> ctrl(0.06, 0.10) -> eave(1, 0.16)
      for (let i = 0; i <= N; i++) {
        const t = i / N;
        const u = 1 - t;
        const x = 2 * u * t * 0.06 + t * t * 1.0;
        const y = u * u * 1.0 + 2 * u * t * 0.10 + t * t * 0.16;
        pts.push(new THREE.Vector2(Math.max(x, 0.001), y));
      }
      // upturned eave tip
      pts.push(new THREE.Vector2(1.07, 0.20));
      pts.push(new THREE.Vector2(1.12, 0.30));
      const geo = new THREE.LatheGeometry(pts, 4);
      geo.rotateY(Math.PI / 4); // corners to diagonals, eaves parallel to walls
      return geo;
    }
    const roofGeo = buildRoofGeometry();
    const unitBox = new THREE.BoxGeometry(1, 1, 1);
    const unitPlane = new THREE.PlaneGeometry(1, 1);

    function makeRoof(w, h, d, mat) {
      const m = new THREE.Mesh(roofGeo, mat || roofMats[Math.floor(Math.random() * roofMats.length)]);
      m.scale.set(w * 0.72, h, d * 0.72);
      return m;
    }

    function addOutline(mesh, k) {
      if (!mesh.parent) return;
      const o = new THREE.Mesh(mesh.geometry, matOutline);
      o.position.copy(mesh.position);
      o.rotation.copy(mesh.rotation);
      o.scale.copy(mesh.scale).multiplyScalar(k || 1.045);
      o.renderOrder = -1;
      mesh.parent.add(o);
    }

    /* ========================================================
       sky backdrop — painted dusk gradient plane
       ======================================================== */
    (function makeSky() {
      const c = document.createElement('canvas');
      c.width = 2; c.height = 512;
      const ctx = c.getContext('2d');
      const g = ctx.createLinearGradient(0, 0, 0, 512);
      g.addColorStop(0.00, '#04060d');
      g.addColorStop(0.42, '#0b1220');
      g.addColorStop(0.68, '#1a2233');
      g.addColorStop(0.85, '#3a2a24');
      g.addColorStop(0.96, '#4a2e22');
      g.addColorStop(1.00, '#241a12');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 2, 512);
      const tex = new THREE.CanvasTexture(c);
      const sky = new THREE.Mesh(
        new THREE.PlaneGeometry(500, 220),
        new THREE.MeshBasicMaterial({ map: tex, fog: false })
      );
      sky.position.set(0, 55, -150);
      scene.add(sky);
    })();

    /* ---------- lights ---------- */
    scene.add(new THREE.HemisphereLight(0x35466a, 0x0c0a08, 0.5));
    const moonLight = new THREE.DirectionalLight(0xa8c0e8, 0.55);
    moonLight.position.set(30, 40, -60);
    scene.add(moonLight);
    const warmFill = new THREE.DirectionalLight(0xff9a55, 0.10);
    warmFill.position.set(-10, 8, 20);
    scene.add(warmFill);

    /* ---------- ground + street ---------- */
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), matGround);
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);

    const street = new THREE.Mesh(new THREE.PlaneGeometry(6, 140), matStone);
    street.rotation.x = -Math.PI / 2;
    street.position.set(0, 0.02, -35);
    scene.add(street);

    function radialTexture(inner, outer, size) {
      const s = size || 128;
      const c = document.createElement('canvas');
      c.width = c.height = s;
      const ctx = c.getContext('2d');
      const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
      g.addColorStop(0, inner);
      g.addColorStop(1, outer);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, s, s);
      return new THREE.CanvasTexture(c);
    }

    // warm light pools under lanterns
    const poolTex = radialTexture('rgba(255,160,80,0.35)', 'rgba(255,120,50,0)');
    function addLightPool(x, z, scale) {
      const p = new THREE.Mesh(
        unitPlane,
        new THREE.MeshBasicMaterial({
          map: poolTex, transparent: true, depthWrite: false,
          blending: THREE.AdditiveBlending
        })
      );
      p.rotation.x = -Math.PI / 2;
      p.position.set(x, 0.05, z);
      p.scale.set(scale, scale, 1);
      scene.add(p);
      return p;
    }

    /* ========================================================
       A4 — lantern factory (capsule + caps + tassel + sway)
       ======================================================== */
    const lanterns = [];
    const lanternGlowTex = radialTexture('rgba(255,170,90,0.55)', 'rgba(255,110,50,0)');

    function makeLantern(scale, withLight) {
      const pivot = new THREE.Group(); // hang point at top

      const cord = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, 0.35, 4), matWoodDark);
      cord.position.y = -0.17;
      pivot.add(cord);

      const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 0.20, 4, 10), matLanternBody);
      body.position.y = -0.55;
      pivot.add(body);

      const capTop = new THREE.Mesh(new THREE.CylinderGeometry(0.10, 0.12, 0.06, 8), matLanternCap);
      capTop.position.y = -0.36;
      pivot.add(capTop);

      const capBot = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.09, 0.06, 8), matLanternCap);
      capBot.position.y = -0.74;
      pivot.add(capBot);

      const tassel = new THREE.Mesh(new THREE.ConeGeometry(0.05, 0.20, 6), matLanternBody);
      tassel.position.y = -0.86;
      tassel.rotation.x = Math.PI;
      pivot.add(tassel);

      const glow = new THREE.Sprite(new THREE.SpriteMaterial({
        map: lanternGlowTex, transparent: true, depthWrite: false,
        blending: THREE.AdditiveBlending, opacity: 0.8
      }));
      glow.scale.set(1.6, 1.6, 1);
      glow.position.y = -0.55;
      pivot.add(glow);

      let light = null;
      if (withLight) {
        light = new THREE.PointLight(0xff8a45, 1.5, 13, 2);
        light.position.y = -0.55;
        pivot.add(light);
      }

      pivot.scale.setScalar(scale);
      lanterns.push({
        pivot: pivot,
        glow: glow,
        light: light,
        base: 0.8 + Math.random() * 0.2,
        phase: Math.random() * Math.PI * 2,
        swayAmp: 0.06 + Math.random() * 0.05
      });
      return pivot;
    }

    /* ========================================================
       A2 — anime buildings
       ======================================================== */
    const windows = [];
    const chimneys = [];

    // vertical sign textures (酒 / 茶 / 客)
    function signTexture(ch) {
      const c = document.createElement('canvas');
      c.width = 64; c.height = 192;
      const ctx = c.getContext('2d');
      ctx.fillStyle = '#5a2018';
      ctx.fillRect(0, 0, 64, 192);
      ctx.strokeStyle = '#d8a44a';
      ctx.lineWidth = 3;
      ctx.strokeRect(5, 5, 54, 182);
      ctx.fillStyle = '#e8c96a';
      ctx.font = 'bold 52px "Microsoft YaHei", "Songti TC", serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(ch, 32, 96);
      return new THREE.CanvasTexture(c);
    }
    const signTexs = ['酒', '茶', '客'].map(signTexture);

    function makeBuilding(cfg) {
      const w = cfg.w, d = cfg.d, stories = cfg.stories;
      const storyH = 2.3;
      const g = new THREE.Group();
      const wallMat = wallMats[Math.floor(Math.random() * wallMats.length)];
      let y = 0;

      for (let s = 0; s < stories; s++) {
        const inset = 1 - s * 0.09;
        const bw = w * inset, bd = d * inset;

        const body = new THREE.Mesh(unitBox, wallMat);
        body.scale.set(bw, storyH, bd);
        body.position.y = y + storyH / 2;
        g.add(body);

        // corner posts (wooden frame)
        const postH = storyH;
        for (let px = -1; px <= 1; px += 2) {
          for (let pz = -1; pz <= 1; pz += 2) {
            const post = new THREE.Mesh(unitBox, matWoodDark);
            post.scale.set(0.14, postH, 0.14);
            post.position.set(px * (bw / 2 - 0.02), y + postH / 2, pz * (bd / 2 - 0.02));
            g.add(post);
          }
        }
        // top beam
        const beam = new THREE.Mesh(unitBox, matWood);
        beam.scale.set(bw * 1.02, 0.16, bd * 1.02);
        beam.position.y = y + storyH - 0.08;
        g.add(beam);

        // windows on street face (+z)
        if (!cfg.noWindows) {
          const count = Math.max(1, Math.floor(bw / 1.4));
          for (let i = 0; i < count; i++) {
            const wx = (i - (count - 1) / 2) * (bw / (count + 0.5));
            const frame = new THREE.Mesh(unitPlane, matWoodDark);
            frame.scale.set(0.62, 0.82, 1);
            frame.position.set(wx, y + storyH * 0.52, bd / 2 + 0.015);
            g.add(frame);

            const lit = Math.random() > 0.25;
            const win = new THREE.Mesh(unitPlane, lit ? (Math.random() > 0.4 ? matWindowGlow : matWindowGlowHot) : matWoodDark);
            win.scale.set(0.5, 0.68, 1);
            win.position.set(wx, y + storyH * 0.52, bd / 2 + 0.03);
            g.add(win);
            if (lit) windows.push({ mesh: win, timer: 4 + Math.random() * 10, on: true });
          }
        }

        // balcony on upper stories
        if (s > 0 && Math.random() > 0.35) {
          const plat = new THREE.Mesh(unitBox, matWood);
          plat.scale.set(bw * 0.8, 0.08, 0.55);
          plat.position.set(0, y + 0.04, bd / 2 + 0.28);
          g.add(plat);
          const rail = new THREE.Mesh(unitBox, matWoodDark);
          rail.scale.set(bw * 0.8, 0.06, 0.06);
          rail.position.set(0, y + 0.55, bd / 2 + 0.52);
          g.add(rail);
          for (let rp = -1; rp <= 1; rp++) {
            const rpPost = new THREE.Mesh(unitBox, matWoodDark);
            rpPost.scale.set(0.05, 0.55, 0.05);
            rpPost.position.set(rp * bw * 0.38, y + 0.3, bd / 2 + 0.52);
            g.add(rpPost);
          }
        }

        y += storyH;

        // skirt roof between stories
        if (s < stories - 1) {
          const skirt = makeRoof(bw * 1.02, 0.55, bd * 1.02);
          skirt.position.y = y;
          g.add(skirt);
          y += 0.34;
        }
      }

      // main curved roof
      const roofH = 1.3 + stories * 0.35;
      const roof = makeRoof(w * 1.05, roofH, d * 1.05);
      roof.position.y = y;
      g.add(roof);
      if (cfg.hero) addOutline(roof, 1.05);

      // ridge + ornaments (鴟尾)
      const ridgeY = y + roofH * 0.98;
      const ridge = new THREE.Mesh(unitBox, matRidge);
      ridge.scale.set(w * 0.52, 0.14, 0.18);
      ridge.position.y = ridgeY;
      g.add(ridge);
      for (let e = -1; e <= 1; e += 2) {
        const orn = new THREE.Mesh(unitBox, matRidge);
        orn.scale.set(0.12, 0.34, 0.20);
        orn.position.set(e * w * 0.26, ridgeY + 0.12, 0);
        orn.rotation.z = -e * 0.25;
        g.add(orn);
      }

      // chimney on some roofs
      if (cfg.chimney) {
        const ch = new THREE.Mesh(unitBox, matStone);
        ch.scale.set(0.3, 0.7, 0.3);
        const cx = w * 0.25;
        ch.position.set(cx, y + roofH * 0.55, d * 0.15);
        g.add(ch);
        chimneys.push({ group: g, local: new THREE.Vector3(cx, y + roofH * 0.55 + 0.4, d * 0.15) });
      }

      // hanging sign beside door
      if (cfg.sign !== undefined) {
        const sign = new THREE.Mesh(
          new THREE.PlaneGeometry(0.42, 1.25),
          new THREE.MeshBasicMaterial({ map: signTexs[cfg.sign] })
        );
        sign.position.set(w / 2 - 0.2, 1.7, d / 2 + 0.06);
        g.add(sign);
      }

      // lantern under front eave
      if (cfg.lantern) {
        const lp = makeLantern(0.9, cfg.lanternLight);
        lp.position.set(-w / 2 + 0.3, y - 0.05, d / 2 + 0.35);
        g.add(lp);
      }

      return { group: g, topY: y, w: w, d: d };
    }

    /* ---------- street layout ---------- */
    const signCycle = [0, 1, 2, 0, 2, 1, 0, 1];
    let signIdx = 0;

    for (let side = -1; side <= 1; side += 2) {
      for (let i = 0; i < 7; i++) {
        const stories = 1 + Math.floor(Math.random() * 3); // 1-3
        const cfg = {
          w: 2.0 + Math.random() * 0.9,
          d: 2.0 + Math.random() * 0.8,
          stories: stories,
          hero: i < 2,
          chimney: Math.random() > 0.6,
          lantern: Math.random() > 0.45,
          lanternLight: false
        };
        if (Math.random() > 0.55) cfg.sign = signCycle[signIdx++ % signCycle.length];
        const b = makeBuilding(cfg);
        const x = side * (4.8 + Math.random() * 1.6) + (Math.random() - 0.5) * 0.6;
        const z = 3 - i * 5.4 - Math.random() * 1.8;
        b.group.position.set(x, 0, z);
        b.group.rotation.y = side > 0 ? Math.PI : 0;
        scene.add(b.group);
      }
    }

    // deeper silhouette rows
    for (let side = -1; side <= 1; side += 2) {
      for (let i = 0; i < 6; i++) {
        const b = makeBuilding({
          w: 2.6 + Math.random() * 1.4,
          d: 2.6 + Math.random() * 1.2,
          stories: 2 + Math.floor(Math.random() * 2),
          noWindows: Math.random() > 0.3
        });
        b.group.position.set(
          side * (11 + Math.random() * 5) + (Math.random() - 0.5) * 2,
          0,
          -8 - i * 6.5 - Math.random() * 2
        );
        scene.add(b.group);
      }
    }

    /* ---------- pagoda (hero landmark, right third) ---------- */
    const pagoda = new THREE.Group();
    {
      let py = 0;
      let pw = 3.6;
      for (let t = 0; t < 5; t++) {
        const tierH = 1.9 - t * 0.14;
        const body = new THREE.Mesh(unitBox, t % 2 ? matWallB : matWallA);
        body.scale.set(pw, tierH, pw);
        body.position.y = py + tierH / 2;
        pagoda.add(body);

        // corner posts
        for (let px = -1; px <= 1; px += 2) {
          for (let pz = -1; pz <= 1; pz += 2) {
            const post = new THREE.Mesh(unitBox, matWoodDark);
            post.scale.set(0.16, tierH, 0.16);
            post.position.set(px * (pw / 2 - 0.02), py + tierH / 2, pz * (pw / 2 - 0.02));
            pagoda.add(post);
          }
        }

        // lit windows each tier
        const win = new THREE.Mesh(unitPlane, matWindowGlow);
        win.scale.set(0.55, 0.7, 1);
        win.position.set(0, py + tierH * 0.5, pw / 2 + 0.03);
        pagoda.add(win);

        py += tierH;
        const roof = makeRoof(pw * 1.5, 1.0 - t * 0.08, pw * 1.5);
        roof.position.y = py;
        pagoda.add(roof);
        addOutline(roof, 1.05);
        py += 0.62;
        pw *= 0.80;
      }
      // spire
      const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.09, 1.6, 6), matRidge);
      spire.position.y = py + 0.8;
      pagoda.add(spire);
      for (let sb = 0; sb < 3; sb++) {
        const ball = new THREE.Mesh(new THREE.SphereGeometry(0.16 - sb * 0.04, 8, 6), matLanternCap);
        ball.position.y = py + 0.4 + sb * 0.4;
        pagoda.add(ball);
      }
      pagoda.position.set(9.5, 0, -34);
      scene.add(pagoda);
    }

    /* ---------- gate archway (hero, foreground-mid) ---------- */
    {
      const gate = new THREE.Group();
      const pillarGeo = new THREE.BoxGeometry(0.55, 5.2, 0.55);
      const pl = new THREE.Mesh(pillarGeo, matWoodDark); pl.position.set(-3.0, 2.6, 0);
      const pr = new THREE.Mesh(pillarGeo, matWoodDark); pr.position.set(3.0, 2.6, 0);
      const beam1 = new THREE.Mesh(unitBox, matWood);
      beam1.scale.set(7.6, 0.4, 0.65); beam1.position.y = 4.4;
      const beam2 = new THREE.Mesh(unitBox, matWood);
      beam2.scale.set(6.6, 0.32, 0.55); beam2.position.y = 5.15;
      gate.add(pl, pr, beam1, beam2);

      const gRoof = makeRoof(7.2, 1.5, 1.6);
      gRoof.position.y = 5.45;
      gate.add(gRoof);
      addOutline(gRoof, 1.05);

      const gRidge = new THREE.Mesh(unitBox, matRidge);
      gRidge.scale.set(4.2, 0.14, 0.2); gRidge.position.y = 5.45 + 1.44;
      gate.add(gRidge);

      // plaque
      const pc = document.createElement('canvas');
      pc.width = 192; pc.height = 64;
      const pctx = pc.getContext('2d');
      pctx.fillStyle = '#141a26'; pctx.fillRect(0, 0, 192, 64);
      pctx.strokeStyle = '#d8a44a'; pctx.lineWidth = 3; pctx.strokeRect(4, 4, 184, 56);
      pctx.fillStyle = '#e8c96a';
      pctx.font = 'bold 34px "Microsoft YaHei", "Songti TC", serif';
      pctx.textAlign = 'center'; pctx.textBaseline = 'middle';
      pctx.fillText('青石鎮', 96, 34);
      const plaque = new THREE.Mesh(
        new THREE.PlaneGeometry(1.9, 0.62),
        new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(pc) })
      );
      plaque.position.set(0, 4.78, 0.36);
      gate.add(plaque);

      // two lanterns hanging from beam
      const gl1 = makeLantern(1.1, true); gl1.position.set(-2.2, 4.2, 0.2); gate.add(gl1);
      const gl2 = makeLantern(1.1, true); gl2.position.set(2.2, 4.2, 0.2); gate.add(gl2);

      gate.position.set(0, 0, 5.5);
      scene.add(gate);
      addLightPool(-2.2, 5.7, 4.5);
      addLightPool(2.2, 5.7, 4.5);
    }

    /* ---------- street lantern poles ---------- */
    for (let i = 0; i < 5; i++) {
      const side = i % 2 === 0 ? -1 : 1;
      const z = 1 - i * 7;
      const x = side * 3.4;

      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 3.6, 6), matWoodDark);
      pole.position.set(x, 1.8, z);
      scene.add(pole);
      const arm = new THREE.Mesh(unitBox, matWoodDark);
      arm.scale.set(0.9, 0.08, 0.08);
      arm.position.set(x - side * 0.4, 3.55, z);
      scene.add(arm);

      const lp = makeLantern(1.0, i < 3);
      lp.position.set(x - side * 0.8, 3.5, z);
      scene.add(lp);
      addLightPool(x - side * 0.8, z, 5);
    }

    /* ========================================================
       A5 — composition framing
       ======================================================== */
    // foreground silhouette rooftop (upper-left frame)
    {
      const fg = new THREE.Group();
      const fgRoof = makeRoof(9, 2.6, 5, matSilhouette);
      fgRoof.position.y = 0;
      fg.add(fgRoof);
      const fgRidge = new THREE.Mesh(unitBox, matSilhouette);
      fgRidge.scale.set(5.2, 0.2, 0.26);
      fgRidge.position.y = 2.55;
      fg.add(fgRidge);
      for (let e = -1; e <= 1; e += 2) {
        const orn = new THREE.Mesh(unitBox, matSilhouette);
        orn.scale.set(0.2, 0.5, 0.3);
        orn.position.set(e * 2.6, 2.75, 0);
        orn.rotation.z = -e * 0.3;
        fg.add(orn);
      }
      // near-camera street pole lantern (depth cue, guaranteed in frame)
      const nearPole = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.09, 3.6, 6), matWoodDark);
      nearPole.position.set(-3.3, 1.8, 8);
      scene.add(nearPole);
      const nearArm = new THREE.Mesh(unitBox, matWoodDark);
      nearArm.scale.set(0.9, 0.08, 0.08);
      nearArm.position.set(-2.9, 3.55, 8);
      scene.add(nearArm);
      const nearLant = makeLantern(1.3, true);
      nearLant.position.set(-2.5, 3.5, 8);
      scene.add(nearLant);
      addLightPool(-2.5, 8, 5);

      fg.position.set(-5.0, 4.4, 9.0);
      fg.rotation.y = 0.3;
      scene.add(fg);
    }

    // bare winter tree (right foreground silhouette)
    {
      const tree = new THREE.Group();
      const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.24, 3.4, 6), matSilhouette);
      trunk.position.y = 1.7;
      trunk.rotation.z = 0.08;
      tree.add(trunk);
      const branchData = [
        [0.5, 2.8, 0, 1.6, 0.7, 0.1],
        [-0.4, 2.4, 0.2, 1.3, 2.4, -0.15],
        [0.3, 3.4, -0.1, 1.1, 0.9, 0.3],
        [-0.2, 3.1, 0.1, 0.9, 2.1, 0.5]
      ];
      for (const bd of branchData) {
        const br = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.09, bd[3], 5), matSilhouette);
        br.position.set(bd[0], bd[1], bd[2]);
        br.rotation.z = bd[4];
        br.rotation.x = bd[5];
        tree.add(br);
      }
      tree.position.set(5.0, 0, 7.0);
      scene.add(tree);
    }

    /* ---------- mountains ---------- */
    for (let i = 0; i < 6; i++) {
      const mh = 15 + Math.random() * 16;
      const m = new THREE.Mesh(new THREE.ConeGeometry(13 + Math.random() * 10, mh, 5), matMountain);
      m.position.set(-55 + i * 21 + Math.random() * 6, mh / 2 - 1, -85 - Math.random() * 25);
      scene.add(m);
    }

    /* ---------- moon + glow (upper right third) ---------- */
    const moon = new THREE.Sprite(new THREE.SpriteMaterial({
      map: radialTexture('rgba(240,244,252,1)', 'rgba(205,220,245,0)'),
      transparent: true, depthWrite: false, fog: false
    }));
    moon.scale.set(14, 14, 1);
    moon.position.set(19, 27, -120);
    scene.add(moon);

    const moonGlow = new THREE.Sprite(new THREE.SpriteMaterial({
      map: radialTexture('rgba(185,205,240,0.4)', 'rgba(165,190,230,0)'),
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, fog: false
    }));
    moonGlow.scale.set(44, 44, 1);
    moonGlow.position.copy(moon.position);
    scene.add(moonGlow);

    /* ---------- stars ---------- */
    const starCount = 380;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i++) {
      const a = Math.random() * Math.PI * 2;
      const r = 70 + Math.random() * 60;
      starPos[i * 3] = Math.cos(a) * r;
      starPos[i * 3 + 1] = 16 + Math.random() * 70;
      starPos[i * 3 + 2] = Math.sin(a) * r - 50;
    }
    const starGeo = new THREE.BufferGeometry();
    starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
    const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({
      color: 0xcfd8e8, size: 0.30, sizeAttenuation: true,
      transparent: true, opacity: 0.85, fog: false
    }));
    scene.add(stars);

    /* ========================================================
       A4 — chimney smoke
       ======================================================== */
    const smokeTex = radialTexture('rgba(190,195,205,0.30)', 'rgba(190,195,205,0)');
    const smokes = [];
    const smokePuffsPerChimney = 6;
    for (const ch of chimneys.slice(0, 5)) {
      const world = ch.local.clone();
      ch.group.updateMatrixWorld(true);
      ch.group.localToWorld(world);
      for (let i = 0; i < smokePuffsPerChimney; i++) {
        const sp = new THREE.Sprite(new THREE.SpriteMaterial({
          map: smokeTex, transparent: true, depthWrite: false, opacity: 0
        }));
        sp.position.copy(world);
        scene.add(sp);
        smokes.push({
          sprite: sp, origin: world.clone(),
          life: (i / smokePuffsPerChimney) * 6,
          max: 6, drift: 0.2 + Math.random() * 0.3
        });
      }
    }

    /* ========================================================
       A4 — waving banners
       ======================================================== */
    const banners = [];
    function makeBanner(x, z, rotY) {
      const g = new THREE.Group();
      const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.07, 4.4, 6), matWoodDark);
      pole.position.y = 2.2;
      g.add(pole);
      const arm = new THREE.Mesh(unitBox, matWoodDark);
      arm.scale.set(1.1, 0.07, 0.07);
      arm.position.set(0.5, 4.3, 0);
      g.add(arm);

      const geo = new THREE.PlaneGeometry(0.85, 2.1, 1, 8);
      const banner = new THREE.Mesh(geo, new THREE.MeshToonMaterial({
        color: 0x8a2a20, gradientMap: gradientMap, side: THREE.DoubleSide
      }));
      banner.position.set(0.55, 3.15, 0);
      g.add(banner);

      // golden character on banner
      const bc = document.createElement('canvas');
      bc.width = 64; bc.height = 128;
      const bctx = bc.getContext('2d');
      bctx.fillStyle = '#e8c96a';
      bctx.font = 'bold 44px "Microsoft YaHei", "Songti TC", serif';
      bctx.textAlign = 'center'; bctx.textBaseline = 'middle';
      bctx.fillText('俠', 32, 64);
      const glyph = new THREE.Mesh(
        new THREE.PlaneGeometry(0.5, 1.0),
        new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(bc), transparent: true })
      );
      glyph.position.set(0.55, 3.15, 0.01);
      g.add(glyph);

      g.position.set(x, 0, z);
      g.rotation.y = rotY;
      scene.add(g);

      banners.push({
        geo: geo,
        glyph: glyph,
        base: geo.attributes.position.array.slice(),
        phase: Math.random() * Math.PI * 2
      });
    }
    makeBanner(-3.6, 1.5, 0.2);
    makeBanner(3.6, -5.5, Math.PI - 0.2);

    /* ========================================================
       A4 — birds crossing the moon
       ======================================================== */
    const birdTex = (function () {
      const c = document.createElement('canvas');
      c.width = 64; c.height = 32;
      const ctx = c.getContext('2d');
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 4;
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(6, 26);
      ctx.quadraticCurveTo(20, 8, 32, 22);
      ctx.quadraticCurveTo(44, 8, 58, 26);
      ctx.stroke();
      return new THREE.CanvasTexture(c);
    })();
    const birdMat = new THREE.SpriteMaterial({ map: birdTex, color: 0x0a0d14, transparent: true, fog: false });
    const birds = [];
    for (let i = 0; i < 4; i++) {
      const b = new THREE.Sprite(birdMat.clone());
      b.scale.set(2.2, 1.1, 1);
      b.visible = false;
      scene.add(b);
      birds.push({ sprite: b, off: i });
    }
    const birdFlight = { active: false, t: 0, next: 8 + Math.random() * 10 };

    /* ========================================================
       A4 — shooting star
       ======================================================== */
    const shootTex = (function () {
      const c = document.createElement('canvas');
      c.width = 128; c.height = 8;
      const ctx = c.getContext('2d');
      const g = ctx.createLinearGradient(0, 0, 128, 0);
      g.addColorStop(0, 'rgba(255,255,255,0)');
      g.addColorStop(0.7, 'rgba(220,230,255,0.7)');
      g.addColorStop(1, 'rgba(255,255,255,1)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, 128, 8);
      return new THREE.CanvasTexture(c);
    })();
    const shoot = new THREE.Mesh(
      new THREE.PlaneGeometry(9, 0.35),
      new THREE.MeshBasicMaterial({
        map: shootTex, transparent: true, depthWrite: false,
        blending: THREE.AdditiveBlending, opacity: 0, fog: false,
        side: THREE.DoubleSide
      })
    );
    scene.add(shoot);
    const shootState = { active: false, t: 0, dur: 1.2, next: 6 + Math.random() * 10, from: new THREE.Vector3(), to: new THREE.Vector3() };

    /* ---------- dust + embers (kept from v0.2) ---------- */
    const dustCount = innerWidth < 600 ? 120 : 240;
    const dustPos = new Float32Array(dustCount * 3);
    const dustSeed = [];
    for (let i = 0; i < dustCount; i++) {
      dustPos[i * 3] = (Math.random() - 0.5) * 30;
      dustPos[i * 3 + 1] = Math.random() * 9;
      dustPos[i * 3 + 2] = 12 - Math.random() * 50;
      dustSeed.push({ vx: 0.1 + Math.random() * 0.3, ph: Math.random() * Math.PI * 2 });
    }
    const dustGeo = new THREE.BufferGeometry();
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    const dustPts = new THREE.Points(dustGeo, new THREE.PointsMaterial({
      color: 0xd8cfb8, size: 0.09, sizeAttenuation: true,
      transparent: true, opacity: 0.5, depthWrite: false
    }));
    scene.add(dustPts);

    const emberCount = innerWidth < 600 ? 26 : 55;
    const emberPos = new Float32Array(emberCount * 3);
    const emberSeed = [];
    function resetEmber(i) {
      emberPos[i * 3] = (Math.random() - 0.5) * 12;
      emberPos[i * 3 + 1] = 0.2;
      emberPos[i * 3 + 2] = 6 - Math.random() * 28;
      emberSeed[i] = {
        vy: 0.4 + Math.random() * 0.8,
        vx: (Math.random() - 0.5) * 0.3,
        ph: Math.random() * Math.PI * 2,
        life: 0, max: 160 + Math.random() * 240
      };
    }
    for (let i = 0; i < emberCount; i++) {
      resetEmber(i);
      emberSeed[i].life = Math.random() * emberSeed[i].max;
      emberPos[i * 3 + 1] = Math.random() * 7;
    }
    const emberGeo = new THREE.BufferGeometry();
    emberGeo.setAttribute('position', new THREE.BufferAttribute(emberPos, 3));
    const emberPts = new THREE.Points(emberGeo, new THREE.PointsMaterial({
      color: 0xffa860, size: 0.16, sizeAttenuation: true,
      transparent: true, opacity: 0.85, depthWrite: false,
      blending: THREE.AdditiveBlending
    }));
    scene.add(emberPts);

    /* ---------- ground fog sprites ---------- */
    const fogSprites = [];
    const fogTex = radialTexture('rgba(190,200,215,0.13)', 'rgba(190,200,215,0)');
    for (let i = 0; i < 9; i++) {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({
        map: fogTex, transparent: true, depthWrite: false,
        opacity: 0.5 + Math.random() * 0.3
      }));
      s.scale.set(15 + Math.random() * 10, 4 + Math.random() * 2, 1);
      s.position.set((Math.random() - 0.5) * 26, 0.9 + Math.random() * 1.2, 8 - i * 6);
      scene.add(s);
      fogSprites.push({ sprite: s, speed: 0.12 + Math.random() * 0.2, baseX: s.position.x, ph: Math.random() * Math.PI * 2 });
    }

    /* ========================================================
       A5 — camera rig: slow push-in + sway + mouse parallax
       ======================================================== */
    const camState = { mouseX: 0, mouseY: 0, lookX: 1.2, lookY: 0 };
    addEventListener('pointermove', (e) => {
      camState.mouseX = (e.clientX / innerWidth - 0.5) * 2;
      camState.mouseY = (e.clientY / innerHeight - 0.5) * 2;
    }, { passive: true });

    addEventListener('resize', () => {
      camera.aspect = innerWidth / innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(innerWidth, innerHeight);
    });

    /* ========================================================
       main loop
       ======================================================== */
    const clock = new THREE.Clock();
    const lookTarget = new THREE.Vector3();

    function frame() {
      const dt = Math.min(clock.getDelta(), 0.05);
      const t = clock.elapsedTime;

      /* camera — 90s push-in loop toward the pagoda */
      const push = (Math.sin(t * 0.035 - Math.PI / 2) + 1) / 2; // 0..1 slow
      camera.position.z = 14.5 - push * 3.5;
      camera.position.x = Math.sin(t * 0.03) * 0.9 + camState.mouseX * 0.8;
      camera.position.y = 3.1 + Math.sin(t * 0.04) * 0.18 - camState.mouseY * 0.4;
      camState.lookX += (1.2 + camState.mouseX * 1.8 - camState.lookX) * 0.04;
      camState.lookY += ((-camState.mouseY * 0.7) - camState.lookY) * 0.04;
      lookTarget.set(camState.lookX, 3.4 + camState.lookY, -26);
      camera.lookAt(lookTarget);

      /* lanterns: sway + flicker */
      for (const l of lanterns) {
        l.pivot.rotation.z = Math.sin(t * 1.2 + l.phase) * l.swayAmp;
        l.pivot.rotation.x = Math.cos(t * 0.9 + l.phase * 1.7) * l.swayAmp * 0.6;
        const f = l.base + Math.sin(t * 5.5 + l.phase) * 0.10 + Math.sin(t * 15 + l.phase * 2) * 0.05;
        if (l.light) l.light.intensity = f * 1.8;
        l.glow.material.opacity = 0.55 + f * 0.3;
      }

      /* window flicker */
      for (const w of windows) {
        w.timer -= dt;
        if (w.timer <= 0) {
          w.on = !w.on;
          w.mesh.visible = w.on;
          w.timer = w.on ? 5 + Math.random() * 12 : 1.5 + Math.random() * 4;
        }
      }

      /* chimney smoke */
      for (const s of smokes) {
        s.life += dt;
        if (s.life > s.max) s.life -= s.max;
        const k = s.life / s.max;
        s.sprite.position.set(
          s.origin.x + Math.sin(t * 0.5 + s.origin.z) * s.drift * k * 2 + k * 1.2,
          s.origin.y + k * 5.5,
          s.origin.z + k * 0.5
        );
        const sc = 0.8 + k * 3.2;
        s.sprite.scale.set(sc, sc, 1);
        s.sprite.material.opacity = 0.28 * Math.sin(k * Math.PI);
      }

      /* banners wave (vertex displacement) */
      for (const b of banners) {
        const pos = b.geo.attributes.position.array;
        const base = b.base;
        for (let i = 0; i < pos.length; i += 3) {
          const bx = base[i], by = base[i + 1];
          const hang = (1.05 - by) / 2.1; // 0 at top, 1 at bottom
          pos[i] = bx;
          pos[i + 1] = by;
          pos[i + 2] = Math.sin(t * 2.2 + b.phase + by * 2.5) * 0.16 * hang
                     + Math.sin(t * 3.7 + b.phase * 2 + by * 4) * 0.05 * hang;
        }
        b.geo.attributes.position.needsUpdate = true;
        b.glyph.position.z = 0.01 + Math.sin(t * 2.2 + b.phase) * 0.05;
      }

      /* birds */
      birdFlight.next -= dt;
      if (!birdFlight.active && birdFlight.next <= 0) {
        birdFlight.active = true;
        birdFlight.t = 0;
        for (const b of birds) b.sprite.visible = true;
      }
      if (birdFlight.active) {
        birdFlight.t += dt;
        const k = birdFlight.t / 22; // 22s crossing
        if (k >= 1) {
          birdFlight.active = false;
          birdFlight.next = 25 + Math.random() * 25;
          for (const b of birds) b.sprite.visible = false;
        } else {
          for (const b of birds) {
            b.sprite.position.set(
              55 - k * 130 + b.off * 2.4,
              25 + Math.sin(k * 6 + b.off * 1.3) * 1.5 + b.off * 0.9,
              -95
            );
            const flap = 0.9 + Math.sin(t * 8 + b.off * 2) * 0.25;
            b.sprite.scale.set(2.2, 1.1 * flap, 1);
          }
        }
      }

      /* shooting star */
      shootState.next -= dt;
      if (!shootState.active && shootState.next <= 0) {
        shootState.active = true;
        shootState.t = 0;
        shootState.from.set(-35 + Math.random() * 25, 34 + Math.random() * 12, -100);
        shootState.to.copy(shootState.from).add(new THREE.Vector3(16 + Math.random() * 8, -9 - Math.random() * 5, 0));
      }
      if (shootState.active) {
        shootState.t += dt;
        const k = shootState.t / shootState.dur;
        if (k >= 1) {
          shootState.active = false;
          shootState.next = 14 + Math.random() * 18;
          shoot.material.opacity = 0;
        } else {
          shoot.position.lerpVectors(shootState.from, shootState.to, k);
          shoot.rotation.z = Math.atan2(
            shootState.to.y - shootState.from.y,
            shootState.to.x - shootState.from.x
          );
          shoot.material.opacity = Math.sin(k * Math.PI) * 0.9;
        }
      }

      /* dust */
      const dp = dustGeo.attributes.position.array;
      for (let i = 0; i < dustCount; i++) {
        const sd = dustSeed[i];
        dp[i * 3] += sd.vx * dt + Math.sin(t * 0.6 + sd.ph) * 0.002;
        dp[i * 3 + 1] += Math.cos(t * 0.4 + sd.ph) * 0.002;
        if (dp[i * 3] > 16) dp[i * 3] = -16;
      }
      dustGeo.attributes.position.needsUpdate = true;

      /* embers */
      const ep = emberGeo.attributes.position.array;
      for (let i = 0; i < emberCount; i++) {
        const es = emberSeed[i];
        es.life++;
        ep[i * 3] += (es.vx + Math.sin(t * 1.2 + es.ph) * 0.15) * dt * 2;
        ep[i * 3 + 1] += es.vy * dt * 2;
        if (es.life > es.max || ep[i * 3 + 1] > 9) resetEmber(i);
      }
      emberGeo.attributes.position.needsUpdate = true;

      /* ground fog */
      for (const f of fogSprites) {
        f.sprite.position.x = f.baseX + Math.sin(t * f.speed + f.ph) * 2.5;
      }

      stars.material.opacity = 0.7 + Math.sin(t * 0.8) * 0.15;

      renderer.render(scene, camera);
    }

    function loop() {
      if (!fxState.running || document.hidden) return;
      frame();
      requestAnimationFrame(loop);
    }

    window.__loginThree = {
      resume() { if (!document.hidden) requestAnimationFrame(loop); }
    };

    requestAnimationFrame(loop);
    return true;
  };
})();
