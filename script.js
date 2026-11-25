javascript:
document.addEventListener('DOMContentLoaded', () => {
  /* ========================================================================
     1. MENU MOBILE INTERATIVO (HAMBÚRGUER + TOUCH)
     ======================================================================== */
  const menuToggle = document.getElementById('menuToggle');
  const navMenu = document.getElementById('navMenu');
  const navLinks = navMenu ? navMenu.querySelectorAll('a') : [];

  function abrirFecharMenu(forcarEstado) {
    if (!navMenu || !menuToggle) return;
    const deveAbrir = typeof forcarEstado === 'boolean'
      ? forcarEstado
      : !navMenu.classList.contains('aberto');

    navMenu.classList.toggle('aberto', deveAbrir);
    menuToggle.setAttribute('aria-expanded', String(deveAbrir));
  }

  if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      abrirFecharMenu();
    });

    // Fecha ao tocar ou clicar fora do menu
    document.addEventListener('click', (e) => {
      if (
        navMenu.classList.contains('aberto') &&
        !navMenu.contains(e.target) &&
        !menuToggle.contains(e.target)
      ) {
        abrirFecharMenu(false);
      }
    });

    document.addEventListener('touchstart', (e) => {
      if (
        navMenu.classList.contains('aberto') &&
        !navMenu.contains(e.target) &&
        !menuToggle.contains(e.target)
      ) {
        abrirFecharMenu(false);
      }
    }, { passive: true });

    // Fecha o menu suavemente ao selecionar qualquer opção
    navLinks.forEach((link) => {
      link.addEventListener('click', () => {
        abrirFecharMenu(false);
      });
    });
  }

  /* ========================================================================
     2. CARROSSEL INTERATIVO COM TOUCH (SWIPE) E BOTÕES (< e >)
     ======================================================================== */
  const carouselViewport = document.getElementById('carouselViewport');
  const carouselTrack = document.getElementById('carouselTrack');
  const btnPrev = document.getElementById('btnPrev');
  const btnNext = document.getElementById('btnNext');

  if (carouselViewport && carouselTrack && btnPrev && btnNext) {
    const cards = Array.from(carouselTrack.querySelectorAll('.card'));
    let currentIndex = 0;
    let startX = 0;
    let startY = 0;
    let currentDeltaX = 0;
    let isDragging = false;

    function isTabletCarouselActive() {
  const width = window.innerWidth;
  return width >= 600 && width <= 820;
}

    function getStepWidth() {
      if (cards.length === 0) return 0;
      const cardWidth = cards[0].getBoundingClientRect().width;
      const gap = parseFloat(getComputedStyle(carouselTrack).gap) || 16;
      return cardWidth + gap;
    }

    function getMaxIndex() {
      const visibleCards = 2;
      return Math.max(0, cards.length - visibleCards);
    }

    function updateCarousel(animate = true) {
      if (!isTabletCarouselActive()) {
        carouselTrack.style.transform = '';
        carouselTrack.style.transition = '';
        return;
      }

      carouselTrack.style.transition = animate
        ? 'transform 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)'
        : 'none';

      const offset = currentIndex * getStepWidth();
      carouselTrack.style.transform = `translate3d(-${offset}px, 0, 0)`;
    }

    function goNext() {
      const maxIndex = getMaxIndex();
      currentIndex = currentIndex >= maxIndex ? 0 : currentIndex + 1;
      updateCarousel(true);
    }

    function goPrev() {
      const maxIndex = getMaxIndex();
      currentIndex = currentIndex <= 0 ? maxIndex : currentIndex - 1;
      updateCarousel(true);
    }

    btnNext.addEventListener('click', goNext);
    btnPrev.addEventListener('click', goPrev);

    // Eventos Touch (Swipe natural com o dedo)
    carouselViewport.addEventListener('touchstart', (e) => {
      if (!isTabletCarouselActive() || e.touches.length !== 1) return;
      startX = e.touches[0].clientX;
      startY = e.touches[0].clientY;
      currentDeltaX = 0;
      isDragging = true;
      carouselTrack.style.transition = 'none';
    }, { passive: true });

    carouselViewport.addEventListener('touchmove', (e) => {
      if (!isDragging || !isTabletCarouselActive()) return;
      const touchX = e.touches[0].clientX;
      const touchY = e.touches[0].clientY;
      const diffX = touchX - startX;
      const diffY = touchY - startY;

      // Só arrasta horizontalmente se o movimento for predominantemente horizontal
      if (Math.abs(diffX) > Math.abs(diffY)) {
        currentDeltaX = diffX;
        const baseOffset = currentIndex * getStepWidth();
        const dragOffset = baseOffset - currentDeltaX * 0.45;
        carouselTrack.style.transform = `translate3d(-${dragOffset}px, 0, 0)`;
      }
    }, { passive: true });

    carouselViewport.addEventListener('touchend', () => {
      if (!isDragging || !isTabletCarouselActive()) return;
      isDragging = false;

      const swipeThreshold = 40; // Sensibilidade do toque em pixels
      if (currentDeltaX < -swipeThreshold) {
        goNext();
      } else if (currentDeltaX > swipeThreshold) {
        goPrev();
      } else {
        updateCarousel(true);
      }
      currentDeltaX = 0;
    });

    window.addEventListener('resize', () => {
      currentIndex = Math.min(currentIndex, getMaxIndex());
      updateCarousel(false);
    });

    updateCarousel(false);
  }
});
