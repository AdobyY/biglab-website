(() => {
  'use strict';
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const canvas = document.querySelector('[data-research-network]');
  const field = canvas?.closest('.constellation-field');
  const topics = field ? [...field.querySelectorAll('[data-constellation-topic]')] : [];

  // A deterministic, illustrative network, never presented as measured research data.
  if (canvas && field && topics.length <= 7) {
    const ctx = canvas.getContext('2d');
    if (ctx) {
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
      let pointerX = 300, pointerY = 276, box, heroBox, size = 0;
      const hero = field.closest('.hero');
      const constellation = field.closest('.constellation');
      const hint = constellation.querySelector('[data-network-hint]');
      const defaultHint = hint?.textContent;
      const weights = nodes.map(() => 0);
      const waves = [];
      const dust = Array.from({ length: 48 }, () => ({
        x: random() * 600, y: random() * 600, phase: random() * 6.28, size: .5 + random() * .8,
      }));
      const measure = () => {
        box = field.getBoundingClientRect();
        heroBox = hero.getBoundingClientRect();
        size = Math.round(box.width * Math.min(window.devicePixelRatio || 1, 2));
        if (canvas.width !== size || canvas.height !== size) canvas.width = canvas.height = size;
        targetSpread = Math.max(0, Math.min(1, -heroBox.top / heroBox.height));
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
        const expansion = (.72 + formation * .28) * (1 + spread * .15 + Math.sin(phase * .65) * .025);
        dust.forEach(star => {
          ctx.fillStyle = `rgba(246,243,233,${.12 + (Math.sin(phase * .65 + star.phase) + 1) * .1})`;
          ctx.beginPath();
          ctx.arc(star.x + yaw * 10, star.y + pitch * 10, star.size, 0, Math.PI * 2);
          ctx.fill();
        });
        // Quiet orbital traces frame the connections, rather than a UI progress ring.
        for (let i = 0; i < 2; i += 1) {
          ctx.strokeStyle = 'rgba(243,223,161,.12)';
          ctx.lineWidth = .7;
          ctx.beginPath();
          ctx.ellipse(300, 276, 220 + spread * 12, 100 + i * 65, -.5 + i * 1.3 + yaw * .2, 0, Math.PI * 2);
          ctx.stroke();
        }
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
          ctx.strokeStyle = `rgba(243,223,161,${.055 + a.depth * .15 + energy * .45})`;
          ctx.lineWidth = .6 + energy * .7;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          if (edgeIndex % 11 === 0 || (energy > .35 && edgeIndex % 3 === 0)) {
            const progress = (phase * (.2 + energy * .18) + edgeIndex * .137) % 1;
            // A short trailing segment makes the direction of influence legible.
            const tail = Math.max(0, progress - .1);
            ctx.strokeStyle = `rgba(246,243,233,${.3 + energy * .55})`;
            ctx.lineWidth = 1 + energy;
            ctx.beginPath(); ctx.moveTo(a.x + (b.x - a.x) * tail, a.y + (b.y - a.y) * tail);
            ctx.lineTo(a.x + (b.x - a.x) * progress, a.y + (b.y - a.y) * progress); ctx.stroke();
          }
        });
        positions.forEach((p, i) => {
          ctx.fillStyle = `rgba(243,223,161,${Math.min(1, .25 + p.depth * .6 + p.energy * .5)})`;
          ctx.beginPath(); ctx.arc(p.x, p.y, nodes[i].size * (1 + p.energy * .65), 0, Math.PI * 2); ctx.fill();
          if (p.energy > .45 && i % 3 === 0) {
            ctx.strokeStyle = `rgba(243,223,161,${p.energy * .3})`;
            ctx.lineWidth = .7;
            ctx.beginPath(); ctx.arc(p.x, p.y, nodes[i].size * 2.8, 0, Math.PI * 2); ctx.stroke();
          }
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
          angle += seconds * .075;
          yaw += (targetYaw - yaw) * .075;
          pitch += (targetPitch - pitch) * .075;
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
      hero.addEventListener('pointermove', (event) => {
        if (event.pointerType === 'touch' || motion.matches) return;
        targetYaw = ((event.clientX - heroBox.left) / heroBox.width - .5) * .85;
        targetPitch = ((event.clientY - heroBox.top) / heroBox.height - .5) * .5;
        pointerX = (event.clientX - box.left) / box.width * 600;
        pointerY = (event.clientY - box.top) / box.height * 600;
        pointerInside = pointerX >= 0 && pointerX <= 600 && pointerY >= 0 && pointerY <= 600;
      });
      const resetPointer = () => { targetYaw = targetPitch = 0; pointerInside = false; };
      hero.addEventListener('pointerleave', resetPointer);
      hero.addEventListener('pointercancel', resetPointer);
      field.addEventListener('pointerdown', (event) => {
        if (event.target.closest('a') || motion.matches) return;
        sendWave((event.clientX - box.left) / box.width * 600, (event.clientY - box.top) / box.height * 600);
      });
      const highlight = () => {
        const active = focused >= 0 ? focused : hovered;
        constellation.classList.toggle('network-exploring', active >= 0);
        if (hint) hint.textContent = active >= 0 ? topics[active].querySelector('.topic-label').textContent : defaultHint;
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
    }
  }

  // A single editorial reveal system: headings arrive, portraits open in a short stagger.
  // All content is visible at rest, without JavaScript and after preference changes.
  const animations = new Set();
  const arrive = (element, keyframes, delay = 0) => {
    if (motion.matches || typeof element.animate !== 'function') return;
    const animation = element.animate(keyframes, {
      duration: 800, delay, easing: 'cubic-bezier(.16, 1, .3, 1)', fill: 'backwards',
    });
    animations.add(animation);
    animation.onfinish = animation.oncancel = () => animations.delete(animation);
  };
  const clear = () => { animations.forEach(animation => animation.cancel()); animations.clear(); };
  motion.addEventListener('change', clear);
  document.querySelector('#home-sections')?.addEventListener('focusin', clear);
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        if (entry.target.matches('.people-grid')) {
          entry.target.querySelectorAll('.person-tile-image').forEach((image, index) => arrive(image, [
            { opacity: .75, clipPath: 'inset(0 0 12% 0)', transform: 'translateY(12px)' },
            { opacity: 1, clipPath: 'inset(0 0 0 0)', transform: 'translateY(0)' },
          ], Math.min(index, 5) * 65));
        } else if (entry.target.matches('.research-list')) {
          entry.target.querySelectorAll('.research-row img').forEach((image, index) => arrive(image, [
            { clipPath: 'inset(0 8% 0 0)', opacity: .7 },
            { clipPath: 'inset(0 0 0 0)', opacity: 1 },
          ], Math.min(index, 4) * 60));
        } else {
          arrive(entry.target, [
            { opacity: .7, transform: 'translateY(18px)' },
            { opacity: 1, transform: 'translateY(0)' },
          ]);
        }
      });
    }, { threshold: .12 });
    document.querySelectorAll('.builder-about .section-heading, .research-section .research-list, .people-preview .people-grid, .parta-band .section-heading').forEach(element => observer.observe(element));
  }
})();
