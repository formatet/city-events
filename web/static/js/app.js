// app.js

let events = [];
let currentFilter = {
  date: null,
  venue: null,
  category: null
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
    fetch('/api/pride').then(r => r.json()).catch(() => ({ mode: 'off' }))
  ]).then(([json, pride]) => {
    events = json;
    applyPrideMode(pride.mode || 'off');
    renderRows();
    fadeTransition(true, introShownAt);
  }).catch(err => {
    trackEvent('data_load_error');
    console.error("Failed to load events.json:", err);
    document.getElementById("main-content").innerHTML = `
      <p>🚧 Events could not be loaded right now. Please try again later.</p>
    `;
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
  const main = document.getElementById("main-content");
  main.classList.remove("visible");
  main.style.display = "none";
  attachFilterListeners();
  eventInit();
});
