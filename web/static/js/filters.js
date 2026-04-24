// filters.js

function applyFilters() {
  return events.filter(event => {
    const dateMatch = !currentFilter.date || getDateKey(event.date) === currentFilter.date;
    const venueMatch = !currentFilter.venue || event.venue === currentFilter.venue;
    const categoryMatch = !currentFilter.category || event.category === currentFilter.category;
    return dateMatch && venueMatch && categoryMatch;
  });
}

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
  const dates = getNextDates(10).filter(({ key }) => key !== today).slice(0, 9);
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
      if (val) trackDateFilter(val); else if (oldDate) trackFilterClear('date');
      return;
    }

    const headerDate = document.getElementById('header-date');
    if (headerDate && headerDate.contains(e.target) && !e.target.closest('.date-dropdown')) {
      if (dropdown && dropdown.classList.contains('open')) {
        closeDateDropdown();
      } else {
        openDateDropdown();
      }
      return;
    }

    if (dropdown && dropdown.classList.contains('open')) {
      closeDateDropdown();
    }
  });
}
