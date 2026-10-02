document.documentElement.classList.add('has-js');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.navigation');

// Only the homepage opening is choreographed; markup remains visible without JS.
document.querySelectorAll('[data-hero-entrance]').forEach((hero) => {
  const animations = new Set();
  const cancelEntrance = () => {
    animations.forEach((animation) => animation.cancel());
    animations.clear();
  };
  const animate = (element, keyframes, delay, duration) => {
    if (!element || typeof element.animate !== 'function' || reducedMotion.matches) return;
    const animation = element.animate(keyframes, {
      delay, duration, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', fill: 'backwards', iterations: 1,
    });
    animations.add(animation);
    animation.onfinish = animation.oncancel = () => animations.delete(animation);
  };
  reducedMotion.addEventListener('change', cancelEntrance);
  // Keyboard users should never have to wait for the entrance to settle.
  hero.addEventListener('focusin', cancelEntrance);
  const arrive = (element, delay) => animate(element, [
    { opacity: 0.55, transform: 'translateY(10px)' },
    { opacity: 1, transform: 'translateY(0)' },
  ], delay, 700);
  arrive(hero.querySelector('.hero-copy h1'), 0);
  arrive(hero.querySelector('.hero-copy .summary'), 110);
  hero.querySelectorAll('.hero-actions > a').forEach((link, index) => arrive(link, 220 + index * 90));

  const constellation = hero.querySelector('.constellation');
  if (!constellation) return;
  const connections = new Map([...constellation.querySelectorAll('[data-constellation-connection]')]
    .map((path) => [path.dataset.constellationConnection, path]));
  const topics = [...constellation.querySelectorAll('[data-constellation-topic]')];
  let hoveredTopic = null;
  let focusedTopic = null;
  const highlight = () => {
    connections.forEach((path, key) => {
      path.classList.toggle('is-active', key === hoveredTopic || key === focusedTopic);
    });
  };
  topics.forEach((link, index) => {
    const key = link.dataset.constellationTopic;
    link.addEventListener('pointerenter', (event) => {
      if (event.pointerType === 'touch') return;
      hoveredTopic = key;
      highlight();
    });
    const clearHover = () => {
      if (hoveredTopic === key) hoveredTopic = null;
      highlight();
    };
    link.addEventListener('pointerleave', clearHover);
    link.addEventListener('pointercancel', clearHover);
    link.addEventListener('focus', () => { focusedTopic = key; highlight(); });
    link.addEventListener('blur', () => {
      if (focusedTopic === key) focusedTopic = null;
      highlight();
    });
    // Animate the link, never the li whose transform positions the topic.
    const stagger = index * (1000 / Math.max(1, topics.length - 1));
    const path = connections.get(key);
    if (path && !reducedMotion.matches && typeof path.getTotalLength === 'function') {
      const length = path.getTotalLength();
      if (Number.isFinite(length) && length > 0) {
        animate(path, [
          { strokeDasharray: `${length} ${length}`, strokeDashoffset: length },
          { strokeDasharray: `${length} ${length}`, strokeDashoffset: 0 },
        ], 400 + stagger, 1000);
      }
    }
    arrive(link, 650 + stagger);
  });
  const dust = constellation.querySelector('.star-dust');
  if (dust) {
    const opacity = Number.parseFloat(window.getComputedStyle(dust).opacity);
    animate(dust, [{ opacity: opacity * 0.4 }, { opacity }], 200, 1800);
  }
  animate(constellation.querySelector('.central-star'), [
    { opacity: 0.6, transform: 'scale(0.82)', transformOrigin: '300px 276px' },
    { opacity: 1, transform: 'scale(1)', transformOrigin: '300px 276px' },
  ], 100, 1100);
});

const closeSubmenus = (except = null) => {
  document.querySelectorAll('.has-submenu.is-open').forEach((item) => {
    if (item === except || (except && item.contains(except))) return;
    item.classList.remove('is-open');
    item.querySelector(':scope > .nav-entry .submenu-toggle')?.setAttribute('aria-expanded', 'false');
  });
};
const closeNavigation = (restoreFocus = false) => {
  if (!menuButton || !navigation) return;
  navigation.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
  closeSubmenus();
  if (restoreFocus) menuButton.focus();
};
menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') === 'true';
  menuButton.setAttribute('aria-expanded', String(!open));
  navigation?.classList.toggle('is-open', !open);
  if (open) closeSubmenus();
});
navigation?.addEventListener('click', (event) => {
  if (event.target.closest('a')) closeNavigation();
});
document.querySelectorAll('.submenu-toggle').forEach((button) => {
  button.addEventListener('click', () => {
    const item = button.closest('.has-submenu');
    const open = item.classList.contains('is-open');
    closeSubmenus(open ? null : item);
    item.classList.toggle('is-open', !open);
    button.setAttribute('aria-expanded', String(!open));
  });
});
document.addEventListener('click', (event) => {
  if (!event.target.closest('.site-header')) closeNavigation();
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  const openItem = document.querySelector('.has-submenu.is-open');
  if (openItem) {
    const button = openItem.querySelector(':scope > .nav-entry .submenu-toggle');
    closeSubmenus();
    button?.focus();
  } else if (navigation?.classList.contains('is-open')) {
    closeNavigation(true);
  }
});

// Each comparison has its own input; keyboard changes preserve the same state.
document.querySelectorAll('[data-image-comparison]').forEach((comparison) => {
  const range = comparison.querySelector('[data-comparison-range]');
  if (!range) return;
  const update = () => comparison.style.setProperty('--comparison-position', `${range.value}%`);
  range.addEventListener('input', update);
  update();
});

document.querySelectorAll('[data-image-slider]').forEach((slider) => {
  const slides = [...slider.querySelectorAll('[data-slide]')];
  const status = slider.querySelector('[data-slider-status]');
  const previous = slider.querySelector('[data-slider-previous]');
  const next = slider.querySelector('[data-slider-next]');
  const controls = slider.querySelector('.slider-controls');
  if (!slides.length || !status || !previous || !next) return;
  let current = 0;
  let timer;
  let paused = false;
  const autoplay = slider.dataset.autoplay === 'true';
  let pauseButton;
  if (autoplay && controls) {
    pauseButton = document.createElement('button');
    pauseButton.type = 'button';
    pauseButton.className = 'slider-pause';
    pauseButton.textContent = document.body.dataset.pause;
    pauseButton.setAttribute('aria-pressed', 'false');
    controls.append(pauseButton);
  }
  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.classList.toggle('is-active', active);
      slide.setAttribute('aria-hidden', String(!active));
    });
    status.textContent = `${current + 1} / ${slides.length}`;
  };
  const stop = () => { window.clearInterval(timer); timer = undefined; };
  const start = () => {
    stop();
    const interval = Number(slider.dataset.interval);
    if (autoplay && !paused && !reducedMotion.matches && !document.hidden && !slider.matches(':hover') && !slider.contains(document.activeElement)) {
      timer = window.setInterval(() => show(current + 1), Math.max(3, interval || 6) * 1000);
    }
  };
  pauseButton?.addEventListener('click', () => {
    paused = !paused;
    pauseButton.textContent = paused ? document.body.dataset.play : document.body.dataset.pause;
    pauseButton.setAttribute('aria-pressed', String(paused));
    start();
  });
  previous.addEventListener('click', () => { show(current - 1); start(); });
  next.addEventListener('click', () => { show(current + 1); start(); });
  slider.addEventListener('keydown', (event) => {
    if (event.target.matches('input, textarea, select')) return;
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); }
  });
  slider.addEventListener('pointerenter', stop);
  slider.addEventListener('pointerleave', start);
  slider.addEventListener('focusin', stop);
  slider.addEventListener('focusout', () => window.setTimeout(start, 0));
  document.addEventListener('visibilitychange', start);
  reducedMotion.addEventListener('change', start);
  show(0);
  start();
});

document.querySelectorAll('[data-card-carousel]').forEach((carousel) => {
  const track = carousel.querySelector('[data-carousel-track]');
  const previous = carousel.querySelector('[data-carousel-previous]');
  const next = carousel.querySelector('[data-carousel-next]');
  if (!track || !previous || !next) return;
  const update = () => {
    const end = track.scrollWidth - track.clientWidth;
    previous.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= end - 2;
  };
  const move = (direction) => {
    const card = track.firstElementChild;
    if (!card) return;
    const styles = window.getComputedStyle(track);
    const cardWidth = card.getBoundingClientRect().width + (parseFloat(styles.columnGap) || 0);
    const visibleCards = Math.max(1, Math.floor((track.clientWidth + 1) / cardWidth));
    track.scrollBy({ left: direction * cardWidth * visibleCards, behavior: reducedMotion.matches ? 'auto' : 'smooth' });
  };
  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('scroll', update, { passive: true });
  track.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
  });
  new ResizeObserver(update).observe(track);
  update();
});

const galleries = document.querySelectorAll('[data-lightbox-gallery]');
if (galleries.length && typeof HTMLDialogElement !== 'undefined') {
  const dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('aria-label', document.body.dataset.imagePreview);
  dialog.innerHTML = '<button class="lightbox-close" type="button" data-lightbox-close><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg></button><button class="lightbox-previous" type="button" data-lightbox-previous><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5 8 12l7 7"/></svg></button><figure><img alt=""><figcaption></figcaption></figure><button class="lightbox-next" type="button" data-lightbox-next><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></button>';
  dialog.querySelector('[data-lightbox-close]').setAttribute('aria-label', document.body.dataset.close);
  dialog.querySelector('[data-lightbox-previous]').setAttribute('aria-label', document.body.dataset.previousImage);
  dialog.querySelector('[data-lightbox-next]').setAttribute('aria-label', document.body.dataset.nextImage);
  document.body.append(dialog);
  const image = dialog.querySelector('img');
  const caption = dialog.querySelector('figcaption');
  let items = [];
  let current = 0;
  let opener;
  const show = (index) => {
    current = (index + items.length) % items.length;
    image.src = items[current].href;
    image.alt = items[current].dataset.caption || items[current].querySelector('img')?.alt || '';
    caption.textContent = items[current].dataset.caption || '';
    caption.hidden = !caption.textContent;
  };
  galleries.forEach((gallery) => {
    gallery.addEventListener('click', (event) => {
      const item = event.target.closest('[data-lightbox-item]');
      if (!item || !gallery.contains(item)) return;
      event.preventDefault();
      items = [...gallery.querySelectorAll('[data-lightbox-item]')];
      opener = item;
      show(items.indexOf(item));
      dialog.showModal();
    });
  });
  dialog.querySelector('[data-lightbox-close]').addEventListener('click', () => dialog.close());
  dialog.querySelector('[data-lightbox-previous]').addEventListener('click', () => show(current - 1));
  dialog.querySelector('[data-lightbox-next]').addEventListener('click', () => show(current + 1));
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); }
  });
  dialog.addEventListener('close', () => opener?.focus());
}
