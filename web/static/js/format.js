// format.js

function formatDate(dateString, forFilter = false) {
  const eventDate = new Date(dateString);
  const now = new Date();
  const today = new Date(now);
  today.setHours(0, 0, 0, 0);
  const eventDay = new Date(eventDate);
  eventDay.setHours(0, 0, 0, 0);
  const dayDiff = Math.floor((eventDay - today) / (1000 * 60 * 60 * 24));

  const time = eventDate.toLocaleTimeString("sv-SE", {
    hour: "2-digit",
    minute: "2-digit"
  });

  const isMobile = window.innerWidth < 768;
  let label;
  const currentHour = now.getHours();
  
  if (dayDiff === 0) {
    // "Idag" or "Ikväll"
    const eventHour = eventDate.getHours();
    label = (!forFilter && eventHour >= 17) ? "Ikväll" : "Idag";
  } else if (dayDiff === 1) {
    label = "Imorgon";
  } else if (isMobile && !forFilter) {
    // Mobile table: short weekday + short date (7/11)
    const weekdayShort = eventDate.toLocaleDateString("sv-SE", { weekday: "short" });
    const day = eventDate.getDate();
    const month = eventDate.getMonth() + 1;
    label = `${weekdayShort.charAt(0).toUpperCase() + weekdayShort.slice(1).replace('.', '')} ${day}/${month}`;
  } else {
    // Desktop
    if (dayDiff === 2 || dayDiff === 3) {
      // "På <weekday>" for days 2–3
      const weekday = eventDate.toLocaleDateString("sv-SE", { weekday: "long" });
      label = `På ${weekday}`;
    } else {
      // "<Weekday> <date>" for day 4+
      const weekday = eventDate.toLocaleDateString("sv-SE", { weekday: "long" });
      let dateStr = eventDate.toLocaleDateString("sv-SE", {
        day: "numeric",
        month: "long"
      });
      // Shorten "september" to "sept"
      dateStr = dateStr.replace('september', 'sept');
      label = `${weekday.charAt(0).toUpperCase() + weekday.slice(1)} ${dateStr}`;
    }
  }
  return { label, time };
}


function getDateKey(dateString) {
  return new Date(dateString).toISOString().split("T")[0];
}

function getEventEnd(event) {
  if (event.end) return new Date(event.end);
  const start = new Date(event.date);
  const categoryDurations = {
    "Konsert": 2, "Film": 2, "Teater": 2.5, "Föreläsning": 1.5,
    "Klubb": 5, "Opera": 3, "Dans": 2, "Standup": 1.5,
    "Övrigt": 2, "Performance": 1.5, "Litteratur": 1.5, "Musik": 2
  };
  const hours = categoryDurations[event.category] || 2;
  return new Date(start.getTime() + hours * 60 * 60 * 1000);
}
