(function () {
  const year = document.getElementById('year');
  if (year) year.textContent = String(new Date().getFullYear());

  // Mobile menu
  const toggle = document.querySelector('.nav-toggle');
  const menu = document.getElementById('nav-menu');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    // close on click
    menu.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // Contact form: create mailto link so it works on static hosting.
  const form = document.getElementById('contact-form');
  const status = document.getElementById('form-status');
  if (form && status) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const data = new FormData(form);
      const naam = String(data.get('naam') || '').trim();
      const email = String(data.get('email') || '').trim();
      const telefoon = String(data.get('telefoon') || '').trim();
      const bericht = String(data.get('bericht') || '').trim();

      const subject = encodeURIComponent('Afspraak / vraag via website');
      const body = encodeURIComponent(
        `Naam: ${naam}\nE-mail: ${email}\nTelefoon: ${telefoon}\n\nBericht:\n${bericht}\n`
      );

      const to = 'info@mondhygienistzuid.nl';
      const url = `mailto:${to}?subject=${subject}&body=${body}`;

      status.textContent = 'Je e-mailprogramma wordt geopend…';
      window.location.href = url;
    });
  }
})();
