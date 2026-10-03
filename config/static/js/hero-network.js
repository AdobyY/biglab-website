(() => {
  'use strict';
  const canvas = document.querySelector('.homepage-design-2 .hero > [data-research-network]');
  const ctx = canvas?.getContext('2d');
  if (!ctx) return;
  const hero = canvas.closest('.hero');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const palette = getComputedStyle(document.body);
  const rgb = property => {
    const hex = palette.getPropertyValue(property).trim().replace('#', '');
    return [0, 2, 4].map(offset => parseInt(hex.slice(offset, offset + 2), 16)).join(',');
  };
  const colors = { tie: rgb('--design-network-secondary'), attention: rgb('--design-accent') };
  const surface = palette.getPropertyValue('--design-background').trim();
  document.documentElement.style.backgroundColor = surface;
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  let width = 0, height = 0, ratio = 1, bounds, quiet = [];
  let nodes = [], edges = [], positions = [], packets = [];
  let time = 0, last = 0, frame = 0, visible = true;
  let pointer = null, cursor = null, scroll = 0, scrollTarget = 0;
  let nextAttention = 0, nextAmbient = 1;
  let seed;
  const random = () => ((seed = seed * 16807 % 2147483647) - 1) / 2147483646;

  const build = () => {
    // An illustrative graph of individuals. It has no research-topic groups or measured data.
    seed = 27183;
    nodes = []; edges = []; packets = []; positions = [];
    const count = width < 600 ? 46 : width < 1100 ? 76 : 104;
    const separation = Math.sqrt(width * height / count) * .57;
    for (let attempt = 0; nodes.length < count && attempt < 5000; attempt += 1) {
      const u = -.025 + random() * 1.05, v = -.025 + random() * 1.04;
      if (nodes.some(node => Math.hypot((node.u - u) * width, (node.v - v) * height) < separation)) continue;
      nodes.push({ u, v, phase: random() * Math.PI * 2, size: 2.4 + random() * 1.8, activity: 0, ties: [] });
    }
    const distances = nodes.map((node, i) => nodes.map((other, j) => ({ j, distance: Math.hypot((node.u - other.u) * width, (node.v - other.v) * height) }))
      .filter(other => other.j !== i).sort((a, b) => a.distance - b.distance));
    const seen = new Set();
    const connect = (a, b, long = false) => {
      const key = [Math.min(a, b), Math.max(a, b)].join(':');
      if (seen.has(key) || nodes[a].ties.length >= 4 || nodes[b].ties.length >= 4) return false;
      seen.add(key);
      const edge = { a, b, long, strength: .25 + random() * .75, bend: (random() - .5) * (long ? .65 : .55) };
      const index = edges.push(edge) - 1;
      nodes[a].ties.push(index); nodes[b].ties.push(index);
      return true;
    };
    // Local relationships first, with a strict degree limit so no dominant star appears.
    for (let pass = 0; pass < 3; pass += 1) nodes.forEach((node, i) => {
      const neighbor = distances[i].find(other => nodes[other.j].ties.length < 4 && !seen.has([Math.min(i, other.j), Math.max(i, other.j)].join(':')));
      if (neighbor && node.ties.length < 3) connect(i, neighbor.j);
    });
    // Join disconnected paths through the nearest available individuals.
    for (let pass = 0; pass < nodes.length; pass += 1) {
      const reached = new Set([0]), pending = [0];
      while (pending.length) {
        const current = pending.pop();
        nodes[current].ties.forEach(index => {
          const edge = edges[index], other = edge.a === current ? edge.b : edge.a;
          if (!reached.has(other)) { reached.add(other); pending.push(other); }
        });
      }
      if (reached.size === nodes.length) break;
      let best;
      reached.forEach(i => {
        if (nodes[i].ties.length >= 4) return;
        const neighbor = distances[i].find(other => !reached.has(other.j) && nodes[other.j].ties.length < 4);
        if (neighbor && (!best || neighbor.distance < best.distance)) best = { a: i, b: neighbor.j, distance: neighbor.distance };
      });
      if (!best || !connect(best.a, best.b, true)) break;
    }
    // A handful of distant relationships carry influence beyond immediate neighbors.
    for (let attempt = 0, added = 0; attempt < 160 && added < 8; attempt += 1) {
      const a = Math.floor(random() * nodes.length), b = Math.floor(random() * nodes.length);
      if (a !== b && Math.hypot((nodes[a].u - nodes[b].u) * width, (nodes[a].v - nodes[b].v) * height) > Math.min(width, height) * .36 && connect(a, b, true)) added += 1;
    }
  };

  const measure = () => {
    bounds = hero.getBoundingClientRect();
    const changed = Math.abs(width - bounds.width) > 1 || Math.abs(height - bounds.height) > 1;
    width = bounds.width; height = bounds.height;
    ratio = Math.min(devicePixelRatio || 1, 1.75);
    const w = Math.round(width * ratio), h = Math.round(height * ratio);
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    quiet = [...hero.querySelectorAll('.hero-copy h1, .hero-copy .summary, .hero-copy .hero-actions, .hero-footnote')].map(element => {
      const rect = element.getBoundingClientRect();
      return { left: rect.left - bounds.left - 20, top: rect.top - bounds.top - 10, width: rect.width + 40, height: rect.height + 20 };
    });
    scrollTarget = clamp(-bounds.top / height, 0, 1);
    if (changed || !nodes.length) build();
  };

  const emit = (from, gain = 1, depth = 0, visited = []) => {
    if (motion.matches || !nodes[from]) return;
    nodes[from].activity = Math.max(nodes[from].activity, gain);
    const route = [...visited, from];
    const candidates = nodes[from].ties.filter(index => {
      const edge = edges[index];
      return !route.includes(edge.a === from ? edge.b : edge.a);
    }).sort((a, b) => edges[b].strength - edges[a].strength);
    candidates.slice(0, depth === 0 ? 3 : 2).forEach(index => {
      if (packets.length >= 28) return;
      const edge = edges[index], to = edge.a === from ? edge.b : edge.a;
      packets.push({ edge: index, from, to, gain, depth, visited: route, birth: time, duration: edge.long ? 1.05 : .6 + (1 - edge.strength) * .45 });
    });
  };
  const updateSignals = dt => {
    nodes.forEach(node => { node.activity *= Math.exp(-dt * 1.5); });
    const completed = packets.filter(packet => time - packet.birth >= packet.duration);
    packets = packets.filter(packet => time - packet.birth < packet.duration);
    completed.forEach(packet => {
      nodes[packet.to].activity = Math.max(nodes[packet.to].activity, packet.gain * .8);
      if (packet.depth < 2) emit(packet.to, packet.gain * .64, packet.depth + 1, packet.visited);
    });
    if (cursor && time >= nextAttention && positions.length) {
      const nearest = positions.map((point, index) => ({ index, distance: Math.hypot(point.x - cursor.x, point.y - cursor.y) })).sort((a, b) => a.distance - b.distance)[0];
      if (nearest.distance < 145) emit(nearest.index);
      nextAttention = time + .65;
    }
    if (time >= nextAmbient) {
      const available = nodes.map((node, index) => ({ node, index })).filter(({ node }) => node.u < .2 || node.u > .8 || node.v > .78 || node.v < .17);
      if (available.length) emit(available[Math.floor(random() * available.length)].index, .68);
      nextAmbient = time + 3.4;
    }
  };

  const curve = edge => {
    const a = positions[edge.a], b = positions[edge.b];
    const dx = b.x - a.x, dy = b.y - a.y;
    const bend = edge.bend * (1 + scroll * .8);
    const first = { x: a.x + dx * .34 - dy * bend, y: a.y + dy * .34 + dx * bend };
    const second = { x: a.x + dx * .66 + dy * bend * .45, y: a.y + dy * .66 - dx * bend * .45 };
    if (cursor) {
      const middle = { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
      const pull = Math.pow(Math.max(0, 1 - Math.hypot(cursor.x - middle.x, cursor.y - middle.y) / 230), 2) * .22;
      const x = clamp((cursor.x - middle.x) * pull, -24, 24), y = clamp((cursor.y - middle.y) * pull, -24, 24);
      first.x += x; first.y += y; second.x += x; second.y += y;
    }
    return [a, first, second, b];
  };
  const pointOn = (points, t) => {
    const [a, b, c, d] = points, u = 1 - t;
    return { x: u * u * u * a.x + 3 * u * u * t * b.x + 3 * u * t * t * c.x + t * t * t * d.x,
      y: u * u * u * a.y + 3 * u * u * t * b.y + 3 * u * t * t * c.y + t * t * t * d.y };
  };
  const stroke = points => {
    ctx.beginPath(); ctx.moveTo(points[0].x, points[0].y);
    ctx.bezierCurveTo(points[1].x, points[1].y, points[2].x, points[2].y, points[3].x, points[3].y); ctx.stroke();
  };
  const draw = () => {
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0); ctx.clearRect(0, 0, width, height);
    const flow = motion.matches ? 0 : time;
    const entrance = motion.matches ? 1 : Math.min(1, time / 1.4);
    positions = nodes.map(node => {
      // A low-frequency shared current gently reshapes the fabric rather than moving separate groups.
      const u = node.u, v = node.v;
      let x = width * (u + Math.sin(v * 5.8 + flow * .13) * .024 + scroll * .075 * Math.sin(v * 6.3));
      let y = height * (v + Math.sin(u * 6.4 - flow * .11) * .032 + scroll * .055 * Math.cos(u * 5));
      x += Math.sin(flow * .25 + node.phase) * 3;
      y += Math.cos(flow * .23 + node.phase) * 3;
      if (cursor) {
        const distance = Math.hypot(cursor.x - x, cursor.y - y);
        const attention = Math.pow(Math.max(0, 1 - distance / 165), 2);
        x += clamp((cursor.x - x) * attention * .16, -10, 10);
        y += clamp((cursor.y - y) * attention * .16, -10, 10);
        node.activity = Math.max(node.activity, attention * .7);
      }
      return { x, y };
    });
    ctx.globalAlpha = .35 + entrance * .65;
    const curves = edges.map(curve);
    edges.forEach((edge, index) => {
      const activity = Math.max(nodes[edge.a].activity, nodes[edge.b].activity);
      ctx.strokeStyle = `rgba(${colors.tie},${(edge.long ? .2 : .16 + edge.strength * .22) + activity * .15})`;
      ctx.lineWidth = (edge.long ? .8 : .65 + edge.strength * .6) + activity * .3;
      stroke(curves[index]);
      if (activity > .08) {
        ctx.strokeStyle = `rgba(${colors.attention},${activity * .35})`; ctx.lineWidth = 1.2; stroke(curves[index]);
      }
    });
    packets.forEach(packet => {
      const progress = clamp((time - packet.birth) / packet.duration, 0, 1);
      const reverse = edges[packet.edge].a !== packet.from;
      // Influence is a change in the relationship itself, rather than a bright flying particle.
      ctx.strokeStyle = `rgba(${colors.attention},${packet.gain * .62})`; ctx.lineWidth = 1.9; ctx.lineCap = 'round';
      ctx.beginPath();
      for (let segment = 0; segment <= 8; segment += 1) {
        const t = Math.max(0, progress - .17 + segment / 8 * .17), point = pointOn(curves[packet.edge], reverse ? 1 - t : t);
        if (segment === 0) ctx.moveTo(point.x, point.y); else ctx.lineTo(point.x, point.y);
      }
      ctx.stroke();
    });
    nodes.forEach((node, index) => {
      const point = positions[index], activity = node.activity;
      ctx.fillStyle = surface;
      ctx.strokeStyle = `rgba(${activity > .15 ? colors.attention : colors.tie},${.48 + activity * .4})`;
      ctx.lineWidth = .9 + activity * .5;
      ctx.beginPath(); ctx.arc(point.x, point.y, node.size + activity * .5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    });
    // Erase only the illustration behind copy, with a soft edge; text never moves or gets crossed by light.
    ctx.save(); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'destination-out';
    ctx.fillStyle = '#000'; ctx.shadowColor = '#000'; ctx.shadowBlur = width < 600 ? 28 : 40;
    quiet.forEach(rect => ctx.fillRect(rect.left, rect.top, rect.width, rect.height));
    ctx.restore(); ctx.globalAlpha = 1;
  };

  const stop = () => { cancelAnimationFrame(frame); frame = 0; last = 0; };
  const tick = timestamp => {
    if (!visible || document.hidden || motion.matches) { stop(); return; }
    const elapsed = last ? timestamp - last : 34;
    if (elapsed >= 32) {
      const dt = Math.min(elapsed, 80) / 1000; last = timestamp; time += dt;
      scroll += (scrollTarget - scroll) * .065;
      if (pointer) {
        if (!cursor) cursor = { ...pointer };
        cursor.x += (pointer.x - cursor.x) * .2; cursor.y += (pointer.y - cursor.y) * .2;
      }
      updateSignals(dt); draw();
    }
    frame = requestAnimationFrame(tick);
  };
  const start = () => { if (!frame && visible && !document.hidden && !motion.matches) frame = requestAnimationFrame(tick); };
  const clearPointer = () => { pointer = cursor = null; };
  hero.addEventListener('pointermove', event => {
    if (event.pointerType === 'touch' || motion.matches) return;
    pointer = { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  });
  hero.addEventListener('pointerleave', clearPointer); hero.addEventListener('pointercancel', clearPointer);
  hero.addEventListener('pointerdown', event => {
    if (motion.matches || event.target.closest('a, button') || !positions.length) return;
    const x = event.clientX - bounds.left, y = event.clientY - bounds.top;
    const nearest = positions.map((point, index) => ({ index, distance: Math.hypot(point.x - x, point.y - y) })).sort((a, b) => a.distance - b.distance);
    nearest.slice(0, 2).forEach(point => emit(point.index));
    nextAttention = time + .65;
  });
  const refresh = () => { measure(); if (motion.matches) draw(); };
  window.addEventListener('resize', refresh, { passive: true }); window.addEventListener('scroll', refresh, { passive: true });
  if ('ResizeObserver' in window) new ResizeObserver(() => { measure(); draw(); }).observe(hero);
  if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => { visible = entry.isIntersecting; if (visible) start(); else stop(); }).observe(hero);
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); else start(); });
  motion.addEventListener('change', () => {
    stop(); clearPointer(); packets = []; nodes.forEach(node => { node.activity = 0; }); scroll = 0;
    measure(); draw(); start();
  });
  measure(); draw(); start();
})();
