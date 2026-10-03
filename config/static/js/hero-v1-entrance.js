// Version 1 keeps its original topic entrance; the canvas owns relationship interaction.
(() => {
  'use strict';
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('.homepage-design-1 [data-hero-entrance]').forEach(hero => {
    const animations = new Set();
    const cancel = () => { animations.forEach(animation => animation.cancel()); animations.clear(); };
    motion.addEventListener('change', cancel); hero.addEventListener('focusin', cancel);
    const topics = [...hero.querySelectorAll('[data-constellation-topic]')];
    topics.forEach((link, index) => {
      if (motion.matches || typeof link.animate !== 'function') return;
      const animation = link.animate([
        { opacity: .55, transform: 'translateY(10px)' }, { opacity: 1, transform: 'translateY(0)' },
      ], { delay: 650 + index * (1000 / Math.max(1, topics.length - 1)), duration: 700,
        easing: 'cubic-bezier(.16, 1, .3, 1)', fill: 'backwards', iterations: 1 });
      animations.add(animation);
      animation.onfinish = animation.oncancel = () => animations.delete(animation);
    });
  });
})();
