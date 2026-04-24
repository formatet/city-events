// theme.js
// Sunrise/sunset computed locally – no external API call.
// Algorithm: Wikipedia "Sunrise equation" (accuracy ~1 minute).

function getSunTimes(lat, lon, date) {
  const rad = Math.PI / 180;

  // Julian date
  const JD = date.getTime() / 86400000 + 2440587.5;

  // Mean value n (days since J2000 + longitude correction term)
  const n = Math.round(JD - 2451545.0 + 0.0008);
  const Jstar = n - lon / 360;

  // Solar mean anomaly
  const M = ((357.5291 + 0.98560028 * Jstar) % 360 + 360) % 360;

  // Equation of centre
  const C = 1.9148 * Math.sin(M * rad)
          + 0.0200 * Math.sin(2 * M * rad)
          + 0.0003 * Math.sin(3 * M * rad);

  // Ecliptic longitude
  const lambda = ((M + C + 180 + 102.9372) % 360 + 360) % 360;

  // Solar transit (culmination)
  const Jtransit = 2451545.0 + Jstar
    + 0.0053 * Math.sin(M * rad)
    - 0.0069 * Math.sin(2 * lambda * rad);

  // Declination
  const sinDec = Math.sin(lambda * rad) * Math.sin(23.4397 * rad);
  const cosDec = Math.cos(Math.asin(sinDec));

  // Hour angle
  const cosW = (Math.sin(-0.833 * rad) - Math.sin(lat * rad) * sinDec)
             / (Math.cos(lat * rad) * cosDec);

  if (Math.abs(cosW) > 1) return null; // midnight sun or polar night

  const w0 = Math.acos(cosW) / rad;

  // Julian dates for sunrise and sunset
  const Jrise = Jtransit - w0 / 360;
  const Jset  = Jtransit + w0 / 360;

  const toDate = jd => new Date((jd - 2440587.5) * 86400000);
  return { sunrise: toDate(Jrise), sunset: toDate(Jset) };
}

function setThemeBySun() {
  if (document.body.classList.contains('theme-pride-pastel')) return;

  const lat = 57.7089; // Göteborg
  const lon = 11.9746;
  const now = new Date();

  const times = getSunTimes(lat, lon, now);
  if (!times) {
    document.body.classList.add("theme-day");
    return;
  }

  const { sunrise, sunset } = times;
  const preDawn  = new Date(sunrise.getTime() - 60 * 60 * 1000);
  const postDusk = new Date(sunset.getTime()  + 60 * 60 * 1000);

  document.body.classList.remove("theme-day", "theme-night", "theme-transition");

  if (now >= preDawn && now <= postDusk) {
    document.body.classList.add(
      (now < sunrise || now > sunset) ? "theme-transition" : "theme-day"
    );
  } else {
    document.body.classList.add("theme-night");
  }
}

// Update theme every 10 minutes.
setInterval(setThemeBySun, 10 * 60 * 1000);

// iOS can freeze JS timers in background tabs and restore the page from bfcache
// without firing DOMContentLoaded again → stale theme. Ensure correct theme
// when the page becomes visible again.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible') setThemeBySun();
});
window.addEventListener('pageshow', e => {
  if (e.persisted) setThemeBySun();
});
