// app.js

let events = [];
let wowMode = 'off';
let currentFilter = {
  date: null,
  venue: null,
  category: null,
  wow: false,
};

function applyPrideMode(mode) {
  document.body.classList.remove('theme-pride-pastel');
  if (mode === 'pastel') {
    document.body.classList.add('theme-pride-pastel');
    document.body.classList.remove('theme-night', 'theme-transition');
    document.body.classList.add('theme-day');
  } else {
    setThemeBySun();
  }
}

function eventInit() {
  const introShownAt = Date.now();

  Promise.all([
    fetch('/data/events.json').then(r => r.json()),
    fetch('/api/pride').then(r => r.json()).catch(() => ({ mode: 'off' })),
    fetch('/api/wow').then(r => r.json()).catch(() => ({ mode: 'off' })),
  ]).then(([json, pride, wow]) => {
    events = json;
    window.allEvents = json;
    wowMode = wow.mode || 'off';
    applyPrideMode(pride.mode || 'off');
    renderRows();
    fadeTransition(true, introShownAt);
  }).catch(err => {
    trackEvent('data_load_error');
    console.error("Failed to load events.json:", err);
    const main = document.getElementById("main-content");
    main.innerHTML = `<p style="padding:2rem;opacity:0.7;">
      🚧 Evenemangen kunde inte laddas just nu. Försök ladda om sidan, eller
      <a href="#" id="ntfy-report">meddela oss</a> om felet kvarstår.
    </p>`;
    document.getElementById('ntfy-report').addEventListener('click', e => {
      e.preventDefault();
      const link = e.target;
      link.textContent = 'Skickar…';
      link.style.pointerEvents = 'none';
      fetch('https://ntfy.sh/kristall-scrape-tim', {
        method: 'POST',
        body: 'Kristall.info – evenemangen kunde inte laddas (besokarsignal)',
      }).then(() => {
        link.textContent = 'Skickat, tack!';
        trackEvent('error_reported');
      }).catch(() => {
        link.textContent = 'Gick inte att skicka.';
        link.style.pointerEvents = 'auto';
      });
    });
    fadeTransition(false, introShownAt);
  });
}

// Handles fade between intro screen and main content
function fadeTransition(success, introShownAt) {
  const intro = document.getElementById("intro");
  const main = document.getElementById("main-content");
  const minIntroTime = 500;
  const elapsed = Date.now() - introShownAt;
  const delay = Math.max(minIntroTime - elapsed, 0);

  setTimeout(() => {
    intro.classList.add("fading-out");
    setTimeout(() => {
      intro.style.display = "none";
      main.style.display = "block";
      setTimeout(() => {
        main.classList.add("visible");
      }, 30);
    }, 500);
  }, delay);
}


window.addEventListener("DOMContentLoaded", () => {
  setThemeBySun();
  trackTimeOfDay();
  const main = document.getElementById("main-content");
  main.classList.remove("visible");
  main.style.display = "none";
  attachFilterListeners();
  eventInit();
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href');
    if (href === '/om' || a.classList.contains('om-link')) trackEvent('om_click');
    if (href === '/anmal') trackEvent('anmal_click');
  });
});
