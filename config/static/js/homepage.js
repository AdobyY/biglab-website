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
      let hovered = -1;
      let focused = -1;
      let frame = 0;
      let angle = 0;
      let phase = 0;
      let lastTime = 0;
      let visible = true;
      let paused = false;
      let pointer = 0;
      let pointerTarget = 0;
      const constellation = field.closest('.constellation');
      const toggle = constellation.querySelector('[data-network-toggle]');
      constellation.classList.add('network-ready');
      const draw = (rotation = 0) => {
        const box = field.getBoundingClientRect();
        if (!box.width) return;
        const ratio = Math.min(window.devicePixelRatio || 1, 2);
        const size = Math.round(box.width * ratio);
        if (canvas.width !== size || canvas.height !== size) {
          canvas.width = size;
          canvas.height = size;
        }
        ctx.setTransform(size / 600, 0, 0, size / 600, 0, 0);
        ctx.clearRect(0, 0, 600, 600);
        const active = focused >= 0 ? focused : hovered;
        const positions = nodes.map((node) => {
          const x = node.x * Math.cos(rotation) + node.z * Math.sin(rotation);
          const z = node.z * Math.cos(rotation) - node.x * Math.sin(rotation);
          const perspective = 1 + z / 900;
          return { x: 300 + x * perspective, y: 276 + node.y * perspective, depth: (z + 180) / 360 };
        });
        edges.forEach(([i, j], edgeIndex) => {
          const lit = active >= 0 && (nodes[i].group === active || nodes[j].group === active);
          ctx.strokeStyle = lit ? 'rgba(243,223,161,.52)' : `rgba(243,223,161,${.055 + positions[i].depth * .13})`;
          ctx.lineWidth = lit ? 1 : .65;
          ctx.beginPath();
          ctx.moveTo(positions[i].x, positions[i].y);
          ctx.lineTo(positions[j].x, positions[j].y);
          ctx.stroke();
          // Moving signals make the relationships visible, especially on hover.
          if (edgeIndex % (lit ? 3 : 17) === 0) {
            const progress = (phase * .16 + edgeIndex * .137) % 1;
            ctx.fillStyle = lit ? 'rgba(243,223,161,.9)' : 'rgba(243,223,161,.45)';
            ctx.beginPath();
            ctx.arc(positions[i].x + (positions[j].x - positions[i].x) * progress,
              positions[i].y + (positions[j].y - positions[i].y) * progress, lit ? 1.7 : 1.1, 0, Math.PI * 2);
            ctx.fill();
          }
        });
        positions.forEach((position, i) => {
          const lit = nodes[i].group === active;
          ctx.fillStyle = `rgba(243,223,161,${lit ? 1 : .25 + position.depth * .65})`;
          ctx.beginPath();
          ctx.arc(position.x, position.y, nodes[i].size * (lit ? 1.45 : 1), 0, Math.PI * 2);
          ctx.fill();
        });
      };
      const stop = () => {
        cancelAnimationFrame(frame); frame = 0; lastTime = 0;
        constellation.classList.add('network-paused');
      };
      const tick = (time) => {
        if (motion.matches || paused || !visible || document.hidden) { stop(); return; }
        const elapsed = lastTime ? time - lastTime : 34;
        if (elapsed >= 32) {
          lastTime = time;
          const seconds = Math.min(elapsed, 80) / 1000;
          phase += seconds;
          angle += seconds * .035;
          pointer += (pointerTarget - pointer) * .08;
          draw(angle + pointer);
        }
        frame = requestAnimationFrame(tick);
      };
      const start = () => {
        if (motion.matches || paused || !visible || document.hidden || frame) return;
        constellation.classList.remove('network-paused');
        frame = requestAnimationFrame(tick);
      };
      toggle?.addEventListener('click', () => {
        paused = !paused;
        toggle.setAttribute('aria-pressed', String(paused));
        toggle.setAttribute('aria-label', paused ? toggle.dataset.playLabel : toggle.dataset.pauseLabel);
        if (paused) stop(); else start();
      });
      field.addEventListener('pointermove', (event) => {
        if (event.pointerType === 'touch' || motion.matches) return;
        const box = field.getBoundingClientRect();
        pointerTarget = ((event.clientX - box.left) / box.width - .5) * .3;
      });
      field.addEventListener('pointerleave', () => { pointerTarget = 0; });
      topics.forEach((topic, i) => {
        topic.addEventListener('pointerenter', (event) => {
          if (event.pointerType === 'touch') return;
          hovered = i; draw(angle);
        });
        const clear = () => { hovered = -1; draw(angle); };
        topic.addEventListener('pointerleave', clear);
        topic.addEventListener('pointercancel', clear);
        topic.addEventListener('focus', () => { focused = i; draw(angle); });
        topic.addEventListener('blur', () => { focused = -1; draw(angle); });
      });
      if ('ResizeObserver' in window) new ResizeObserver(() => draw(angle)).observe(field);
      if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (!visible) stop(); else start();
      }).observe(field);
      document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); else start(); });
      motion.addEventListener('change', () => {
        toggle.hidden = motion.matches;
        if (motion.matches) { stop(); angle = 0; draw(); } else start();
      });
      toggle.hidden = motion.matches;
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
