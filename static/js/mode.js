const toggleBtn = document.getElementById('toggle-dark-mode');
const body = document.body;

// Funkcja do włączenia dark mode
function enableDarkMode() {
  body.classList.add('dark-mode');
  toggleBtn.textContent = '☀️ Tryb jasny';
  localStorage.setItem('darkMode', 'enabled');
}

// Funkcja do wyłączenia dark mode
function disableDarkMode() {
  body.classList.remove('dark-mode');
  toggleBtn.textContent = '🌙 Tryb ciemny';
  localStorage.setItem('darkMode', 'disabled');
}

// Sprawdź localStorage
const localSetting = localStorage.getItem('darkMode');

if (localSetting === 'enabled') {
  enableDarkMode();
} else if (localSetting === 'disabled') {
  disableDarkMode();
} else {
  // Brak ustawienia w localStorage -> wykryj tryb systemowy
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    enableDarkMode();
  } else {
    disableDarkMode();
  }
}

// Obsługa kliknięcia przycisku
toggleBtn.addEventListener('click', () => {
  if (body.classList.contains('dark-mode')) {
    disableDarkMode();
  } else {
    enableDarkMode();
  }
});

// Nasłuchiwanie zmiany preferencji systemowych i automatyczna aktualizacja (opcjonalne)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
  if (!localStorage.getItem('darkMode')) { // tylko jeśli user nie wybrał ręcznie
    if (e.matches) {
      enableDarkMode();
    } else {
      disableDarkMode();
    }
  }
});