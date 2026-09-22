const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.navigation');

const closeSubmenus = (except = null) => {
  document.querySelectorAll('.has-submenu.is-open').forEach((item) => {
    if (item === except || item.contains(except)) return;
    item.classList.remove('is-open');
    item.querySelector(':scope > .nav-entry .submenu-toggle')?.setAttribute('aria-expanded', 'false');
  });
};

if (menuButton && navigation) {
  menuButton.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!open));
    navigation.classList.toggle('is-open', !open);
    if (open) closeSubmenus();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && navigation.classList.contains('is-open')) {
      navigation.classList.remove('is-open');
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.focus();
    }
  });
}

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
  if (!event.target.closest('.navigation')) closeSubmenus();
});

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  const openItem = document.querySelector('.has-submenu.is-open');
  if (!openItem) return;
  const button = openItem.querySelector(':scope > .nav-entry .submenu-toggle');
  closeSubmenus();
  button?.focus();
});

const network = document.querySelector('[data-network]');
if (network && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const svg = network.querySelector('svg');
  network.addEventListener('pointermove', (event) => {
    const box = network.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    svg.style.transform = `translate(${x * 13}px, ${y * 13}px)`;
  });
  network.addEventListener('pointerleave', () => { svg.style.transform = ''; });
}

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
  let current = 0;
  let timer;

  const show = (index) => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.classList.toggle('is-active', active);
      slide.setAttribute('aria-hidden', String(!active));
    });
    status.textContent = `${current + 1} / ${slides.length}`;
  };
  const stop = () => window.clearInterval(timer);
  const start = () => {
    stop();
    if (slider.dataset.autoplay === 'true' && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      timer = window.setInterval(() => show(current + 1), Number(slider.dataset.interval) * 1000);
    }
  };

  previous.addEventListener('click', () => { show(current - 1); start(); });
  next.addEventListener('click', () => { show(current + 1); start(); });
  slider.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(current - 1); start(); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(current + 1); start(); }
  });
  slider.addEventListener('pointerenter', stop);
  slider.addEventListener('pointerleave', start);
  slider.addEventListener('focusin', stop);
  slider.addEventListener('focusout', start);
  start();
});

document.querySelectorAll('[data-card-carousel]').forEach((carousel) => {
  const track = carousel.querySelector('[data-carousel-track]');
  const previous = carousel.querySelector('[data-carousel-previous]');
  const next = carousel.querySelector('[data-carousel-next]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const update = () => {
    const end = track.scrollWidth - track.clientWidth;
    previous.disabled = track.scrollLeft <= 2;
    next.disabled = track.scrollLeft >= end - 2;
  };
  const move = (direction) => {
    const card = track.firstElementChild;
    if (!card) return;
    const cardWidth = card.getBoundingClientRect().width;
    const visibleCards = Math.max(1, Math.floor(track.clientWidth / cardWidth));
    track.scrollBy({
      left: direction * cardWidth * visibleCards,
      behavior: reducedMotion ? 'auto' : 'smooth',
    });
  };

  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  track.addEventListener('scroll', update, { passive: true });
  track.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); move(-1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); move(1); }
  });
  window.addEventListener('resize', update);
  update();
});

const lightboxGalleries = document.querySelectorAll('[data-lightbox-gallery]');
if (lightboxGalleries.length) {
  const dialog = document.createElement('dialog');
  dialog.className = 'lightbox';
  dialog.setAttribute('aria-label', document.documentElement.lang === 'cs' ? 'Náhled obrázku' : 'Image preview');
  dialog.innerHTML = `
    <button class="lightbox-close" type="button" data-lightbox-close aria-label="Close">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>
    </button>
    <button class="lightbox-previous" type="button" data-lightbox-previous aria-label="Previous image">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5 8 12l7 7"/></svg>
    </button>
    <figure><img alt=""><figcaption></figcaption></figure>
    <button class="lightbox-next" type="button" data-lightbox-next aria-label="Next image">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg>
    </button>`;
  document.body.append(dialog);

  const image = dialog.querySelector('img');
  const caption = dialog.querySelector('figcaption');
  let items = [];
  let current = 0;
  let opener;
  const show = (index) => {
    current = (index + items.length) % items.length;
    image.src = items[current].href;
    image.alt = items[current].dataset.caption || '';
    caption.textContent = items[current].dataset.caption || '';
    caption.hidden = !caption.textContent;
  };

  lightboxGalleries.forEach((gallery) => {
    gallery.addEventListener('click', (event) => {
      const item = event.target.closest('[data-lightbox-item]');
      if (!item) return;
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
  dialog.addEventListener('click', (event) => { if (event.target === dialog) dialog.close(); });
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') show(current - 1);
    if (event.key === 'ArrowRight') show(current + 1);
  });
  dialog.addEventListener('close', () => opener?.focus());
}
