document.addEventListener('DOMContentLoaded', () => {
  /* ========================================================================
     1. MENU MOBILE INTERATIVO (HAMBÚRGUER + TOUCH)
     ======================================================================== */
  const botaoMenuMobile = document.getElementById('botao-menu-mobile');
  const menuNavegacao = document.getElementById('menu-navegacao');
  const linksNavegacao = menuNavegacao ? menuNavegacao.querySelectorAll('a') : [];

  function alternarMenuMobile(forcarAbertura) {
    if (!menuNavegacao || !botaoMenuMobile) return;

    const deveAbrirMenu = typeof forcarAbertura === 'boolean'
      ? forcarAbertura
      : !menuNavegacao.classList.contains('menu-aberto');

    menuNavegacao.classList.toggle('menu-aberto', deveAbrirMenu);
    botaoMenuMobile.setAttribute('aria-expanded', String(deveAbrirMenu));
  }

  if (botaoMenuMobile && menuNavegacao) {
    botaoMenuMobile.addEventListener('click', (evento) => {
      evento.stopPropagation();
      alternarMenuMobile();
    });

    // Fecha o menu ao tocar ou clicar fora dele
    document.addEventListener('click', (evento) => {
      if (
        menuNavegacao.classList.contains('menu-aberto') &&
        !menuNavegacao.contains(evento.target) &&
        !botaoMenuMobile.contains(evento.target)
      ) {
        alternarMenuMobile(false);
      }
    });

    document.addEventListener('touchstart', (evento) => {
      if (
        menuNavegacao.classList.contains('menu-aberto') &&
        !menuNavegacao.contains(evento.target) &&
        !botaoMenuMobile.contains(evento.target)
      ) {
        alternarMenuMobile(false);
      }
    }, { passive: true });

    // Fecha o menu suavemente ao selecionar qualquer opção
    linksNavegacao.forEach((linkNavegacao) => {
      linkNavegacao.addEventListener('click', () => {
        alternarMenuMobile(false);
      });
    });
  }

  /* ========================================================================
     2. CARROSSEL INTERATIVO COM TOUCH (SWIPE) E BOTÕES (< e >)
     ======================================================================== */
  const janelaCarrossel = document.getElementById('janela-carrossel');
  const trilhaCards = document.getElementById('trilha-cards-diferenciais');
  const botaoAnterior = document.getElementById('botao-carrossel-anterior');
  const botaoProximo = document.getElementById('botao-carrossel-proximo');

  if (janelaCarrossel && trilhaCards && botaoAnterior && botaoProximo) {
    const listaCards = Array.from(trilhaCards.querySelectorAll('.card-diferencial'));
    let indiceAtual = 0;
    let posicaoInicialX = 0;
    let posicaoInicialY = 0;
    let deslocamentoAtualX = 0;
    let estaArrastando = false;

    function carrosselTabletEstaAtivo() {
      const larguraTela = window.innerWidth;
      return larguraTela >= 600 && larguraTela <= 820;
    }

    function calcularLarguraDeslocamento() {
      if (listaCards.length === 0) return 0;
      const larguraCard = listaCards[0].getBoundingClientRect().width;
      const espacamentoCards = parseFloat(getComputedStyle(trilhaCards).gap) || 16;
      return larguraCard + espacamentoCards;
    }

    function calcularIndiceMaximo() {
      const quantidadeCardsVisiveis = 2;
      return Math.max(0, listaCards.length - quantidadeCardsVisiveis);
    }

    function atualizarPosicaoCarrossel(animar = true) {
      if (!carrosselTabletEstaAtivo()) {
        trilhaCards.style.transform = '';
        trilhaCards.style.transition = '';
        return;
      }

      trilhaCards.style.transition = animar
        ? 'transform 0.35s cubic-bezier(0.25, 0.8, 0.25, 1)'
        : 'none';

      const deslocamentoPixels = indiceAtual * calcularLarguraDeslocamento();
      trilhaCards.style.transform = `translate3d(-${deslocamentoPixels}px, 0, 0)`;
    }

    function avancarCard() {
      const indiceMaximo = calcularIndiceMaximo();
      indiceAtual = indiceAtual >= indiceMaximo ? 0 : indiceAtual + 1;
      atualizarPosicaoCarrossel(true);
    }

    function voltarCard() {
      const indiceMaximo = calcularIndiceMaximo();
      indiceAtual = indiceAtual <= 0 ? indiceMaximo : indiceAtual - 1;
      atualizarPosicaoCarrossel(true);
    }

    botaoProximo.addEventListener('click', avancarCard);
    botaoAnterior.addEventListener('click', voltarCard);

    // Eventos Touch (Swipe natural com o dedo)
    janelaCarrossel.addEventListener('touchstart', (evento) => {
      if (!carrosselTabletEstaAtivo() || evento.touches.length !== 1) return;
      posicaoInicialX = evento.touches[0].clientX;
      posicaoInicialY = evento.touches[0].clientY;
      deslocamentoAtualX = 0;
      estaArrastando = true;
      trilhaCards.style.transition = 'none';
    }, { passive: true });

    janelaCarrossel.addEventListener('touchmove', (evento) => {
      if (!estaArrastando || !carrosselTabletEstaAtivo()) return;
      const toqueAtualX = evento.touches[0].clientX;
      const toqueAtualY = evento.touches[0].clientY;
      const diferencaX = toqueAtualX - posicaoInicialX;
      const diferencaY = toqueAtualY - posicaoInicialY;

      // Só arrasta horizontalmente se o movimento for predominantemente horizontal
      if (Math.abs(diferencaX) > Math.abs(diferencaY)) {
        deslocamentoAtualX = diferencaX;
        const deslocamentoBase = indiceAtual * calcularLarguraDeslocamento();
        const deslocamentoArrasto = deslocamentoBase - deslocamentoAtualX * 0.45;
        trilhaCards.style.transform = `translate3d(-${deslocamentoArrasto}px, 0, 0)`;
      }
    }, { passive: true });

    janelaCarrossel.addEventListener('touchend', () => {
      if (!estaArrastando || !carrosselTabletEstaAtivo()) return;
      estaArrastando = false;

      const limiteMinimoDeslize = 40;
      if (deslocamentoAtualX < -limiteMinimoDeslize) {
        avancarCard();
      } else if (deslocamentoAtualX > limiteMinimoDeslize) {
        voltarCard();
      } else {
        atualizarPosicaoCarrossel(true);
      }
      deslocamentoAtualX = 0;
    });

    window.addEventListener('resize', () => {
      indiceAtual = Math.min(indiceAtual, calcularIndiceMaximo());
      atualizarPosicaoCarrossel(false);
    });

    atualizarPosicaoCarrossel(false);
  }
});