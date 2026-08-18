// filters.js

// WoW-events ligger i egen kategori, inte i ett source-fält. (Kolumnen `source`
// finns i DB:n men /api/events SELECT:ar den inte, så den saknas i events.json.)
const WOW_CATEGORY = 'Way Out West';

function applyFilters() {
  return events.filter(event => {
    const isWow = event.category === WOW_CATEGORY;
    if (wowOnly) {
      // /wow – ren festivalvy, inget annat
      if (!isWow) return false;
    } else if (isWow && !currentFilter.wow) {
      // Stadsvyn – WoW dolt tills användaren togglar (kräver dyrt band)
      return false;
    }
    const dateMatch = !currentFilter.date || getDateKey(event.date) === currentFilter.date;
    const venueMatch = !currentFilter.venue || event.venue === currentFilter.venue;
    const categoryMatch = !currentFilter.category || event.category === currentFilter.category;
    return dateMatch && venueMatch && categoryMatch;
  });
}

window.toggleWowFilter = function(e) {
  e.preventDefault();
  // På /wow är WoW allt som visas – att kryssa över länken betyder därför
  // "visa staden i stället", dvs tillbaka till startsidan.
  if (wowOnly) {
    trackWowFilter(false);
    window.location.href = '/';
    return;
  }
  currentFilter.wow = !currentFilter.wow;
  renderRows();
  trackWowFilter(currentFilter.wow);
};

function getNextDates(limit) {
  const seen = new Set();
  const result = [];
  for (const event of events) {
    const key = getDateKey(event.date);
    if (!seen.has(key)) {
      seen.add(key);
      result.push({ key, dateString: event.date });
      if (result.length >= limit) break;
    }
  }
  return result;
}

function openDateDropdown() {
  const dropdown = document.getElementById('date-dropdown');
  if (!dropdown) return;
  const today = new Date().toISOString().split('T')[0];
  const dates = getNextDates(8).filter(({ key }) => key !== today).slice(0, 7);
  let html = '';
  for (const { key, dateString } of dates) {
    const { label } = formatDate(dateString, true);
    html += `<a href="#" class="date-dropdown-item${currentFilter.date === key ? ' active' : ''}" data-filter-date="${key}">${label}</a>`;
  }
  dropdown.innerHTML = html;
  dropdown.classList.add('open');
}

function closeDateDropdown() {
  const dropdown = document.getElementById('date-dropdown');
  if (dropdown) dropdown.classList.remove('open');
}

window.toggleDateDropdown = function(e) {
  e.stopPropagation();
  const dropdown = document.getElementById('date-dropdown');
  if (dropdown && dropdown.classList.contains('open')) {
    closeDateDropdown();
  } else {
    openDateDropdown();
  }
};

function attachFilterListeners() {
  document.getElementById("tbody").addEventListener("click", e => {
    const date = e.target.closest(".filter-date");
    const venue = e.target.closest(".filter-venue");
    const category = e.target.closest(".filter-category");

    if (date) {
      e.preventDefault();
      const val = date.dataset.date;
      const toggle = val === currentFilter.date;
      currentFilter.date = toggle ? null : val;
      renderRows();
      if (toggle) trackFilterClear('date'); else trackDateFilter(val);
    } else if (venue) {
      e.preventDefault();
      const val = venue.dataset.venue;
      const toggle = val === currentFilter.venue;
      currentFilter.venue = toggle ? null : val;
      renderRows();
      if (toggle) trackFilterClear('venue'); else trackVenueFilter(val);
    } else if (category) {
      e.preventDefault();
      const val = category.dataset.category;
      const toggle = val === currentFilter.category;
      currentFilter.category = toggle ? null : val;
      renderRows();
      if (toggle) trackFilterClear('category'); else trackCategoryFilter(val);
    }
  });

  document.addEventListener('click', e => {
    const dropdown = document.getElementById('date-dropdown');

    const item = e.target.closest('.date-dropdown-item');
    if (item) {
      e.preventDefault();
      const oldDate = currentFilter.date;
      const val = item.dataset.filterDate;
      currentFilter.date = val || null;
      closeDateDropdown();
      renderRows();
      if (val) trackDropdownDateFilter(val); else if (oldDate) trackFilterClear('date');
      return;
    }

    if (dropdown && dropdown.classList.contains('open')) {
      closeDateDropdown();
    }
  });
}
