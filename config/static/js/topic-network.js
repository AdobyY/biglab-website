(() => {
  'use strict';
  const canvas = document.querySelector('[data-topic-network]');
  const field = canvas?.closest('.constellation-field');
  const constellation = field?.closest('.relationship-network');
  if (!constellation) return;
  const topics = [...constellation.querySelectorAll('[data-constellation-topic]')];
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const palette = getComputedStyle(field);
  const channels = property => {
    const hex = palette.getPropertyValue(property).trim().slice(1);
    return [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16)).join(',');
  };
  const accent = channels('--design-accent');
  const foreground = channels('--design-foreground');

  let seed = 42;
  const random = () => {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  };
  const nodes = [];
  for (let i = 0; i < 150; i += 1) {
    const longitude = random() * Math.PI * 2;
    const latitude = Math.acos(2 * random() - 1);
    const radius = 125 + random() * 55;
    nodes.push({
      x: Math.sin(latitude) * Math.cos(longitude) * radius,
      y: Math.sin(latitude) * Math.sin(longitude) * radius,
      z: Math.cos(latitude) * radius,
      size: .8 + random() * 1.8,
      group: Math.floor(((longitude + Math.PI / 2) % (Math.PI * 2)) / (Math.PI * 2) * topics.length),
    });
  }
  const edges = [];
  nodes.forEach((node, i) => {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const other = nodes[j];
      if (Math.hypot(node.x - other.x, node.y - other.y, node.z - other.z) < 66) edges.push([i, j]);
    }
  });
  let hovered = -1, focused = -1, frame = 0, angle = 0, phase = 0, lastTime = 0;
  let visible = true, yaw = 0, pitch = 0, targetYaw = 0, targetPitch = 0;
  let spread = 0, targetSpread = 0, pointerInside = false;
  let pointerX = 300, pointerY = 276, box, size = 0;
  const weights = nodes.map(() => 0);
  const waves = [];
  const measure = () => {
    box = field.getBoundingClientRect();
    size = Math.round(box.width * Math.min(window.devicePixelRatio || 1, 2));
    if (canvas.width !== size || canvas.height !== size) canvas.width = canvas.height = size;
    targetSpread = Math.max(0, Math.min(1, -box.top / box.height));
  };
  const sendWave = (x = 300, y = 276) => {
    if (motion.matches) return;
    if (waves.length >= 3) waves.shift();
    waves.push({ x, y, birth: phase });
  };
  const draw = () => {
    if (!size) return;
    ctx.setTransform(size / 600, 0, 0, size / 600, 0, 0);
    ctx.clearRect(0, 0, 600, 600);
    const active = focused >= 0 ? focused : hovered;
    const rotation = angle + yaw + spread * .4;
    const tilt = pitch + Math.sin(phase * .18) * .12;
    const formation = motion.matches ? 1 : 1 - Math.pow(1 - Math.min(1, phase / 1.8), 3);
    const expansion = (.72 + formation * .28) * (1 + spread * .15 + Math.sin(phase * .65) * .018);
    const positions = nodes.map((node, i) => {
      weights[i] += ((active >= 0 && node.group === active ? 1 : 0) - weights[i]) * .12;
      const x = node.x * Math.cos(rotation) + node.z * Math.sin(rotation);
      const z = node.z * Math.cos(rotation) - node.x * Math.sin(rotation);
      const y = node.y * Math.cos(tilt) - z * Math.sin(tilt);
      const depthZ = node.y * Math.sin(tilt) + z * Math.cos(tilt);
      const perspective = (1 + depthZ / 900) * expansion;
      let px = 300 + x * perspective + Math.sin(phase * .6 + i) * 2;
      let py = 276 + y * perspective + Math.cos(phase * .5 + i) * 2;
      const distance = Math.hypot(pointerX - px, pointerY - py);
      const proximity = pointerInside ? Math.max(0, 1 - distance / 110) : 0;
      px += (pointerX - px) * proximity * .09;
      py += (pointerY - py) * proximity * .09;
      let energy = 0;
      waves.forEach(wave => {
        const age = phase - wave.birth;
        const d = Math.hypot(px - wave.x, py - wave.y) - age * 115;
        energy = Math.max(energy, Math.exp(-d * d / 650) * Math.max(0, 1 - age / 3.8));
      });
      return { x: px, y: py, depth: (depthZ + 180) / 360, energy: Math.max(weights[i], proximity * .8, energy) };
    });
    edges.forEach(([i, j], edgeIndex) => {
      const a = positions[i], b = positions[j], energy = Math.max(a.energy, b.energy);
      ctx.strokeStyle = `rgba(${accent},${.055 + a.depth * .15 + energy * .45})`;
      ctx.lineWidth = .6 + energy * .7;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      if (edgeIndex % 11 === 0 || (energy > .35 && edgeIndex % 3 === 0)) {
        const progress = (phase * (.2 + energy * .18) + edgeIndex * .137) % 1;
        // A short trailing segment makes the direction of influence legible.
        const tail = Math.max(0, progress - .1);
        ctx.strokeStyle = `rgba(${foreground},${.3 + energy * .55})`;
        ctx.lineWidth = 1 + energy;
        ctx.beginPath(); ctx.moveTo(a.x + (b.x - a.x) * tail, a.y + (b.y - a.y) * tail);
        ctx.lineTo(a.x + (b.x - a.x) * progress, a.y + (b.y - a.y) * progress); ctx.stroke();
      }
    });
    positions.forEach((p, i) => {
      ctx.fillStyle = `rgba(${accent},${Math.min(1, .25 + p.depth * .6 + p.energy * .5)})`;
      ctx.beginPath(); ctx.arc(p.x, p.y, nodes[i].size * (1 + p.energy * .65), 0, Math.PI * 2); ctx.fill();
    });
    while (waves.length && phase - waves[0].birth > 3.8) waves.shift();
  };
  constellation.classList.add('network-ready');
  const stop = () => {
    cancelAnimationFrame(frame); frame = 0; lastTime = 0;
    constellation.classList.add('network-paused');
  };
  const tick = (time) => {
    if (motion.matches || !visible || document.hidden) { stop(); return; }
    const elapsed = lastTime ? time - lastTime : 34;
    if (elapsed >= 32) {
      lastTime = time;
      const seconds = Math.min(elapsed, 80) / 1000;
      phase += seconds;
      angle += seconds * .06;
      yaw += (targetYaw - yaw) * .055;
      pitch += (targetPitch - pitch) * .055;
      spread += (targetSpread - spread) * .06;
      if (Math.floor((phase - seconds) / 7) !== Math.floor(phase / 7)) sendWave();
      draw();
    }
    frame = requestAnimationFrame(tick);
  };
  const start = () => {
    if (motion.matches || !visible || document.hidden || frame) return;
    constellation.classList.remove('network-paused');
    frame = requestAnimationFrame(tick);
  };
  field.addEventListener('pointermove', (event) => {
    if (event.pointerType === 'touch' || motion.matches) return;
    targetYaw = ((event.clientX - box.left) / box.width - .5) * .85;
    targetPitch = ((event.clientY - box.top) / box.height - .5) * .42;
    pointerX = (event.clientX - box.left) / box.width * 600;
    pointerY = (event.clientY - box.top) / box.height * 600;
    pointerInside = pointerX >= 0 && pointerX <= 600 && pointerY >= 0 && pointerY <= 600;
  });
  const resetPointer = () => { targetYaw = targetPitch = 0; pointerInside = false; };
  field.addEventListener('pointerleave', resetPointer);
  field.addEventListener('pointercancel', resetPointer);
  field.addEventListener('pointerdown', (event) => {
    if (event.target.closest('a') || motion.matches) return;
    sendWave((event.clientX - box.left) / box.width * 600, (event.clientY - box.top) / box.height * 600);
  });
  const highlight = () => {
    const active = focused >= 0 ? focused : hovered;
    constellation.classList.toggle('network-exploring', active >= 0);
    if (motion.matches) {
      nodes.forEach((node, i) => { weights[i] = node.group === active ? 1 : 0; });
      draw();
    }
  };
  topics.forEach((topic, i) => {
    topic.addEventListener('pointerenter', (event) => {
      if (event.pointerType === 'touch') return;
      hovered = i; highlight(); sendWave();
    });
    const clear = () => { hovered = -1; highlight(); };
    topic.addEventListener('pointerleave', clear);
    topic.addEventListener('pointercancel', clear);
    topic.addEventListener('focus', () => { focused = i; highlight(); sendWave(); });
    topic.addEventListener('blur', () => { focused = -1; highlight(); });
  });
  if ('ResizeObserver' in window) new ResizeObserver(() => { measure(); draw(); }).observe(field);
  window.addEventListener('scroll', measure, { passive: true });
  window.addEventListener('resize', measure, { passive: true });
  if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible) stop(); else start();
  }).observe(field);
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); else start(); });
  motion.addEventListener('change', () => {
    if (motion.matches) {
      stop(); resetPointer(); angle = yaw = pitch = spread = phase = 0; waves.length = 0; draw();
    } else start();
  });
  measure();
  sendWave();
  draw();
  start();
})();
