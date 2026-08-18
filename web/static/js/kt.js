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

function trackExternalLink(venue, title) {
  trackEvent('event_click', {
    venue,
    title,
    filter_venue: (typeof currentFilter !== 'undefined' && currentFilter.venue) || '',
    filter_category: (typeof currentFilter !== 'undefined' && currentFilter.category) || '',
    filter_date: (typeof currentFilter !== 'undefined' && currentFilter.date) || ''
  });
}

function trackFeaturedClick(venue, title) {
  trackEvent('featured_click', {
    venue,
    title,
    filter_venue: (typeof currentFilter !== 'undefined' && currentFilter.venue) || '',
    filter_category: (typeof currentFilter !== 'undefined' && currentFilter.category) || '',
    filter_date: (typeof currentFilter !== 'undefined' && currentFilter.date) || ''
  });
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

function trackEventsLoaded(ms, count, prideMode) {
  trackEvent('events_loaded', { ms: ms, count: count, pride: prideMode });
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

// Scroll depth tracking (25 / 50 / 75 / 100%)
let maxScrollDepth = 0;
let scrollTracked25 = false;
let scrollTracked50 = false;
let scrollTracked75 = false;
let scrollTracked100 = false;

function trackScrollDepth() {
  const scrollable = document.body.scrollHeight - window.innerHeight;
  if (scrollable <= 0) return;
  const pct = Math.round((window.scrollY / scrollable) * 100);
  if (pct > maxScrollDepth) maxScrollDepth = pct;

  if (!scrollTracked100 && maxScrollDepth >= 100) {
    trackEvent('scroll_depth', { depth: '100%' });
    scrollTracked100 = true;
  } else if (!scrollTracked75 && maxScrollDepth >= 75) {
    trackEvent('scroll_depth', { depth: '75%' });
    scrollTracked75 = true;
  } else if (!scrollTracked50 && maxScrollDepth >= 50) {
    trackEvent('scroll_depth', { depth: '50%' });
    scrollTracked50 = true;
  } else if (!scrollTracked25 && maxScrollDepth >= 25) {
    trackEvent('scroll_depth', { depth: '25%' });
    scrollTracked25 = true;
  }
}

// Session duration – pagehide fires on navigation, tab close, and bfcache eviction;
// more reliable than beforeunload on mobile and Safari.
const sessionStart = Date.now();
window.addEventListener('pagehide', () => {
  const duration = Math.round((Date.now() - sessionStart) / 1000);
  if (duration >= 5) {
    trackEvent('session_duration', { seconds: duration });
  }
});

// Time of day and device type at page load
function trackTimeOfDay() {
  const hour = new Date().getHours();
  let period;
  if (hour >= 5 && hour < 12) period = 'morning';
  else if (hour >= 12 && hour < 17) period = 'afternoon';
  else if (hour >= 17 && hour < 21) period = 'evening';
  else period = 'night';
  const theme = document.body.className.match(/theme-\w+/)?.[0] || 'unknown';
  trackEvent('time_of_day', { period: period, theme: theme });
}

function trackDeviceType() {
  trackEvent('device_type', { type: window.innerWidth < 768 ? 'mobile' : 'desktop' });
}

window.addEventListener('DOMContentLoaded', () => {
  trackDeviceType();

  let scrollTimeout;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(trackScrollDepth, 100);
  });
});
