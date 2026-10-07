// A reading aid only: anchors and contents remain usable without JavaScript.
document.querySelectorAll('[data-inline-collection]').forEach((collection) => {
  const links = [...collection.querySelectorAll(':scope > .section-toc a[href^="#"]')];
  const sections = links.map((link) => collection.querySelector(link.getAttribute('href')));
  let frame = 0;
  const update = () => {
    frame = 0;
    let active = -1;
    sections.forEach((section, index) => {
      if (!section) return;
      const bounds = section.getBoundingClientRect();
      if (bounds.top <= 180 && bounds.bottom > 110) active = index;
    });
    links.forEach((link, index) => {
      if (index === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  window.addEventListener('hashchange', schedule);
  update();
});
