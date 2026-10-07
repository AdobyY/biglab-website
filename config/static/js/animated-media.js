document.querySelectorAll('[data-animated-media]').forEach(container => {
  const image = container.querySelector('img');
  const button = container.querySelector('button');
  let playing = false;
  const stop = () => {
    playing = false;
    if (image.getAttribute('src') !== image.dataset.posterSrc) image.src = image.dataset.posterSrc;
    button.textContent = document.body.dataset.play;
    button.setAttribute('aria-pressed', 'false');
  };
  button.hidden = false;
  button.addEventListener('click', event => {
    event.preventDefault();
    if (playing) { stop(); return; }
    playing = true;
    image.src = image.dataset.animationSrc;
    button.textContent = document.body.dataset.pause;
    button.setAttribute('aria-pressed', 'true');
  });
  image.addEventListener('error', () => { if (playing) stop(); });
  if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => {
    if (!entry.isIntersecting && playing) stop();
  }).observe(container);
  document.addEventListener('visibilitychange', () => { if (document.hidden && playing) stop(); });
  matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', stop);
});
