document.querySelectorAll('.fp-gallery').forEach((gallery) => {
    const carousel = gallery.querySelector('.vanilla-carousel');
    const slides = Array.from(carousel.querySelectorAll('.carousel-slide'));
    const thumbnails = Array.from(gallery.querySelectorAll('[data-slide-index]'));
    let activeIndex = 0;
    let timer;

    function showSlide(index) {
        activeIndex = (index + slides.length) % slides.length;
        slides.forEach((slide, slideIndex) => {
            const active = slideIndex === activeIndex;
            slide.classList.toggle('active', active);
            const video = slide.querySelector('video');
            if (video && !active) video.pause();
        });
        thumbnails.forEach((thumbnail, thumbnailIndex) => {
            const active = thumbnailIndex === activeIndex;
            thumbnail.classList.toggle('active', active);
            thumbnail.setAttribute('aria-current', active ? 'true' : 'false');
        });
    }

    function startAutoPlay() {
        clearInterval(timer);
        timer = setInterval(() => showSlide(activeIndex + 1), Number(carousel.dataset.interval) || 5000);
    }

    thumbnails.forEach((thumbnail) => thumbnail.addEventListener('click', (event) => {
        event.preventDefault();
        clearInterval(timer);
        showSlide(Number(thumbnail.dataset.slideIndex));
    }));
    gallery.querySelector('.fp-thumbnails').addEventListener('pointerenter', () => clearInterval(timer));
    gallery.querySelectorAll('[data-direction]').forEach((button) => button.addEventListener('click', () => {
        showSlide(activeIndex + Number(button.dataset.direction));
        startAutoPlay();
    }));
    showSlide(0);
    startAutoPlay();
});

document.querySelectorAll('.fp-text a[href^="http://"], .fp-text a[href^="https://"]').forEach((link) => {
    link.target = '_blank';
    link.rel = 'noopener';
});

//
// RESIZE GRID ITEM
//

/**
 * Calcule et applique le span correct pour un élément
 */
function resizeGridItem(item) {
  const content = item.querySelector('.content');
  if (!content) return;

  const rowHeight = 10; // Doit correspondre à grid-auto-rows
  const verticalGap = 20; // L'espace vertical souhaité entre vos cartes (en px)

  // Mesure ultra-précise de la hauteur réelle actuelle du contenu
  const contentHeight = content.offsetHeight;

  // Calcul du nombre de rangées (en incluant l'espace vertical voulu)
  const rowSpan = Math.ceil((contentHeight + verticalGap) / rowHeight);

  // Application immédiate à la grille
  item.style.gridRowEnd = `span ${rowSpan}`;
}

/**
 * Initialisation avec observation dynamique des changements de taille
 */
function initMasonry() {
  const items = document.querySelectorAll('.masonry-item');
  if (items.length === 0) return;

  // Création d'un observateur qui recalcule la taille dès qu'un élément change (ex: chargement image)
  const resizeObserver = new ResizeObserver((entries) => {
    for (let entry of entries) {
      // On retrouve le parent '.masonry-item' de la boîte de contenu modifiée
      const item = entry.target.closest('.masonry-item');
      if (item) {
        resizeGridItem(item);
      }
    }
  });

  // On lance le premier calcul et on attache l'observateur sur chaque carte
  items.forEach((item) => {
    resizeGridItem(item);
    const content = item.querySelector('.content');
    if (content) {
      resizeObserver.observe(content);
    }
  });
}

// Lancement automatique dès que le DOM est prêt
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMasonry);
} else {
  initMasonry();
}

// Sécurité finale au chargement complet de la page (polices, styles)
window.addEventListener('load', () => {
  const items = document.querySelectorAll('.masonry-item');
  items.forEach(item => resizeGridItem(item));
});

// Sécurité lors du redimensionnement de l'écran
window.addEventListener('resize', () => {
  const items = document.querySelectorAll('.masonry-item');
  items.forEach(item => resizeGridItem(item));
});
