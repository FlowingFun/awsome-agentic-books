const chapterMenu = document.querySelector('.volume-toc details');
const narrowReader = window.matchMedia('(max-width: 53rem)');

chapterMenu.open = !narrowReader.matches;
narrowReader.addEventListener('change', ({ matches }) => {
  chapterMenu.open = !matches;
});
