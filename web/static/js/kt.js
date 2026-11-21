// kt.js - Analytics tracking wrapper (Umami)

function trackEvent(eventName, eventData = {}) {
  if (window.umami) {
    window.umami.track(eventName, eventData);
  }
}

function trackDateFilter(dateLabel) {
  trackEvent('date_filter', { date: dateLabel });
}

function trackVenueFilter(venue) {
  trackEvent('venue_filter', { venue: venue });
}

function trackCategoryFilter(category) {
  trackEvent('category_filter', { category: category });
}

function trackFilterClear(type) {
  trackEvent('filter_cleared', { type: type });
}

// days_ahead: kalenderdagar från idag till evenemanget (0 = idag).
// position: evenemangets plats i den visade listan (1 = överst).
function clickData(event, position) {
  const d = new Date(event.date);
  const t = new Date();
  const daysAhead = Math.round(
    (new Date(d.getFullYear(), d.getMonth(), d.getDate()) -
     new Date(t.getFullYear(), t.getMonth(), t.getDate())) / 86400000);
  return {
    venue: event.venue,
    title: event.title,
    days_ahead: daysAhead,
    position: position,
    filter_venue: (typeof currentFilter !== 'undefined' && currentFilter.venue) || '',
    filter_category: (typeof currentFilter !== 'undefined' && currentFilter.category) || '',
    filter_date: (typeof currentFilter !== 'undefined' && currentFilter.date) || ''
  };
}

function trackExternalLink(event, position) {
  trackEvent('event_click', clickData(event, position));
}

function trackFeaturedClick(event, position) {
  trackEvent('featured_click', clickData(event, position));
}

function trackWowFilter(nowVisible) {
  trackEvent('wow_filter', { state: nowVisible ? 'on' : 'off' });
}

function trackFilterEmpty(filters) {
  trackEvent('filter_empty', {
    venue: filters.venue || '',
    category: filters.category || '',
    date: filters.date || ''
  });
}

function trackFilterReset() {
  trackEvent('filter_reset');
}

function trackEventsLoaded(ms, count) {
  trackEvent('events_loaded', { ms: ms, count: count });
}

function trackDropdownDateFilter(date) {
  trackEvent('date_dropdown_filter', { date: date });
}

function trackFeedEnd(eventCount) {
  trackEvent('feed_end', { events: eventCount });
}

function trackFeedEndVenueClick(venue) {
  trackEvent('feed_end_venue_click', { venue: venue });
}
