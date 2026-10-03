(() => {
  'use strict';
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
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
