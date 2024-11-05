// Funkce pro nastavení tématu
function setTheme(theme) {
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('theme', theme); // Uložení tématu do localStorage
    
    // Změna obrázku podle aktuálního tématu
    const themeToggleImg = document.getElementById('themeToggle');
    themeToggleImg.src = theme === 'light' ? lightThemeIcon : darkThemeIcon; // Nastavení obrázku
}

// Načtení uloženého tématu
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    setTheme(savedTheme); // Nastavení uloženého tématu
}

// Přepínání témat
const toggleButton = document.getElementById('themeToggle');
toggleButton.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme); // Nastavení nového tématu a uložení
});
