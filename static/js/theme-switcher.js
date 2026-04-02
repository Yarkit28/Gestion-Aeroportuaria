// Theme switcher functionality
document.addEventListener('DOMContentLoaded', function() {
  const themeSwitch = document.getElementById('theme-switch');
  const themeLabel = document.getElementById('theme-label');
  
  // Check for saved theme preference or default to light
  const savedTheme = localStorage.getItem('theme') || 'light';
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  // Set initial theme
  if (savedTheme === 'dark' || (savedTheme === 'auto' && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
    if (themeSwitch) themeSwitch.checked = true;
    if (themeLabel) themeLabel.textContent = '🌙';
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    if (themeSwitch) themeSwitch.checked = false;
    if (themeLabel) themeLabel.textContent = '☀️';
  }
  
  // Toggle theme when switch is clicked
  if (themeSwitch) {
    themeSwitch.addEventListener('change', function() {
      if (this.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        if (themeLabel) themeLabel.textContent = '🌙';
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        if (themeLabel) themeLabel.textContent = '☀️';
      }
    });
  }
  
  // Add theme toggle button for mobile
  const themeToggleBtn = document.createElement('button');
  themeToggleBtn.className = 'btn btn-outline-secondary d-lg-none theme-toggle-mobile';
  themeToggleBtn.innerHTML = '<i class="fas fa-adjust"></i>';
  themeToggleBtn.title = 'Cambiar tema';
  
  themeToggleBtn.addEventListener('click', function() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    if (themeSwitch) themeSwitch.checked = newTheme === 'dark';
    if (themeLabel) themeLabel.textContent = newTheme === 'dark' ? '🌙' : '☀️';
  });
  
  // Add mobile button to navbar if exists
  const navbarNav = document.querySelector('.navbar-nav');
  if (navbarNav) {
    const li = document.createElement('li');
    li.className = 'nav-item d-lg-none';
    li.appendChild(themeToggleBtn);
    navbarNav.appendChild(li);
  }
});