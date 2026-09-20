/**
 * Medical Physics & Complex Systems - Script Vanilla
 * Zero dipendenze esterne
 */
document.addEventListener('DOMContentLoaded', function() {
  // 1. Gestione Menu Mobile
  const toggleBtn = document.querySelector('.mobile-menu-toggle');
  const navMenu = document.querySelector('.nav-menu');

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener('click', function() {
      const isOpen = navMenu.classList.toggle('open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
      toggleBtn.innerHTML = isOpen ? '✕' : '☰';
    });
  }

  // 2. Filtro di Ricerca Istantaneo per le Pubblicazioni (se presente nella pagina)
  const searchInput = document.getElementById('pubSearchInput');
  const pubItems = document.querySelectorAll('.pub-item');
  const pubCount = document.getElementById('pubCount');

  if (searchInput && pubItems.length > 0) {
    searchInput.addEventListener('input', function(e) {
      const query = e.target.value.toLowerCase().trim();
      let visibleCount = 0;

      pubItems.forEach(function(item) {
        const text = item.textContent.toLowerCase();
        if (text.includes(query)) {
          item.style.display = '';
          visibleCount++;
        } else {
          item.style.display = 'none';
        }
      });

      if (pubCount) {
        pubCount.textContent = `Visualizzate ${visibleCount} su ${pubItems.length} pubblicazioni`;
      }
    });
  }
});
