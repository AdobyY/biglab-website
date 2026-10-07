(() => {
  'use strict';

  document.querySelectorAll('[data-research-preview]').forEach(overview => {
    const frame = overview.querySelector('.research-visual-frame');
    const caption = overview.querySelector('.research-visual-caption');
    if (!frame || !caption || overview.classList.contains('preview-ready')) return;

    const entries = [...overview.querySelectorAll('.research-overview-item')]
      .map(article => ({
        article,
        image: article.querySelector('.research-overview-image img'),
        title: article.querySelector('h3 a'),
      }))
      .filter(entry => entry.image && entry.title);
    if (!entries.length) return;

    let selected = null;
    const preview = entry => {
      if (selected === entry) return;
      const image = entry.image.cloneNode(false);
      image.removeAttribute('id');
      image.removeAttribute('data-animation-src');
      image.removeAttribute('data-poster-src');
      image.alt = '';
      image.loading = 'eager';
      image.decoding = 'async';

      // A supplied poster always wins over a potentially animated source set.
      const poster = entry.image.dataset.posterSrc;
      if (poster) {
        image.src = poster;
        image.removeAttribute('srcset');
        image.removeAttribute('sizes');
      }

      frame.replaceChildren(image);
      caption.textContent = entry.title.textContent.trim();
      selected?.article.classList.remove('is-previewed');
      entry.article.classList.add('is-previewed');
      selected = entry;
    };

    preview(entries[0]);
    overview.classList.add('preview-ready');
    entries.forEach(entry => {
      entry.article.addEventListener('mouseenter', () => preview(entry));
      entry.article.addEventListener('focusin', () => preview(entry));
    });
  });
})();
