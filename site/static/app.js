'use strict';
(() => {
  const { papers, topics } = JSON.parse(document.getElementById('collection-data').textContent);
  const $ = id => document.getElementById(id);
  const topicMap = new Map(topics.map(t => [t.id, t]));
  const years = new Set(papers.map(p => String(p.year)));
  const validSorts = new Set(['newest', 'oldest', 'title']);
  const rows = new Map([...document.querySelectorAll('.paper')].map(row => [row.id, row]));
  const disclosure = document.querySelector('.topic-disclosure');
  const selectControls = [];
  let state;
  const readURL = () => {
    const p = new URLSearchParams(location.search);
    return { q: (p.get('q') || '').slice(0, 250), topic: topicMap.has(p.get('topic')) ? p.get('topic') : '', year: years.has(p.get('year')) ? p.get('year') : '', sort: validSorts.has(p.get('sort')) ? p.get('sort') : 'newest' };
  };
  const primaryNote = paper => paper.notes[state.topic] || paper.notes[paper.primaryTopic];
  const filteredPapers = () => {
    const words = state.q.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    return papers.filter(p => (!state.topic || p.tags.includes(state.topic)) && (!state.year || String(p.year) === state.year) && words.every(word => [p.title, p.venue, ...(p.authors || []), ...p.tags.map(t => topicMap.get(t).label), ...Object.values(p.notes)].join(' ').toLocaleLowerCase().includes(word)))
      .sort((a, b) => state.sort === 'title' ? a.title.localeCompare(b.title) : (state.sort === 'oldest' ? a.year - b.year : b.year - a.year) || a.title.localeCompare(b.title));
  };
  function render() {
    const results = filteredPapers();
    const shown = new Set(results.map(p => p.id));
    for (const paper of papers) {
      const row = rows.get(paper.id);
      row.hidden = !shown.has(paper.id);
      row.querySelector('.paper-note').textContent = primaryNote(paper);
      for (const tag of row.querySelectorAll('.paper-topic')) tag.classList.toggle('is-selected', tag.dataset.topic === state.topic);
      const extras = row.querySelector('.more-notes');
      if (extras) {
        let visible = 0;
        for (const note of extras.querySelectorAll('li')) {
          note.hidden = paper.notes[note.dataset.noteTopic] === primaryNote(paper);
          if (!note.hidden) visible++;
        }
        extras.hidden = visible === 0;
      }
    }
    for (const paper of results) $('paper-list').append(rows.get(paper.id));
    for (const link of document.querySelectorAll('.topic-link, .field-topic-link, .map-reset')) link.setAttribute('aria-current', String(link.dataset.topic === state.topic));
    $('collection-title').textContent = topicMap.get(state.topic)?.label || 'All papers';
    $('topic-description').textContent = topicMap.get(state.topic)?.description || 'Browse the full collection, or follow a topic.';
    $('result-count').textContent = `${results.length} ${results.length === 1 ? 'paper' : 'papers'}`;
    $('end-count').textContent = `End of ${state.q || state.topic || state.year ? 'results' : 'collection'} · ${results.length} ${results.length === 1 ? 'paper' : 'papers'}`;
    $('empty-state').hidden = results.length > 0;
    document.querySelector('.column-headings').hidden = results.length === 0;
    document.querySelector('.collection-end').hidden = results.length === 0;
    $('search').value = state.q;
    $('year').value = state.year;
    $('sort').value = state.sort;
    for (const control of selectControls) control.sync();
    $('clear-search').hidden = !state.q;
    $('active-filters').hidden = !(state.q || state.topic || state.year);
    $('filter-summary').textContent = [state.topic && topicMap.get(state.topic).label, state.year, state.q && `“${state.q}”`].filter(Boolean).join(' / ');
    document.title = [topicMap.get(state.topic)?.label, 'Awesome Social Simulation', 'Social Atoms'].filter(Boolean).join(' — ');
    return results;
  }
  function update(next, historyMode = 'replace', anchor = null) {
    state = { ...state, ...next };
    const url = new URL(location.href);
    if (anchor !== null) url.hash = anchor;
    for (const key of ['q', 'topic', 'year', 'sort']) {
      if (state[key] && !(key === 'sort' && state[key] === 'newest')) url.searchParams.set(key, state[key]);
      else url.searchParams.delete(key);
    }
    history[`${historyMode}State`](null, '', url);
    return render();
  }
  const reset = () => update({ q: '', topic: '', year: '', sort: 'newest' }, 'push');
  for (const id of ['year', 'sort']) selectControls.push(window.createRefinedSelect($(id)));
  $('filters').hidden = false;
  $('filters').addEventListener('submit', e => e.preventDefault());
  $('search').addEventListener('input', e => update({ q: e.target.value.slice(0, 250) }));
  $('year').addEventListener('change', e => update({ year: e.target.value }, 'push'));
  $('sort').addEventListener('change', e => update({ sort: e.target.value }, 'push'));
  $('clear-search').addEventListener('click', () => { update({ q: '' }); $('search').focus(); });
  $('reset').addEventListener('click', reset);
  $('empty-reset').addEventListener('click', () => { reset(); $('search').focus(); });
  document.addEventListener('click', event => {
    const link = event.target.closest('a[data-topic]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.dataset.topic && !topicMap.has(link.dataset.topic)) return;
    event.preventDefault();
    const fromMap = link.matches('.field-topic-link, .map-reset');
    update({ topic: link.dataset.topic, ...(fromMap ? { q: '', year: '' } : {}) }, 'push', 'papers');
    if (matchMedia('(max-width: 760px)').matches) disclosure.open = false;
    if (link.matches('.paper-topic, .topic-link, .field-topic-link, .map-reset')) {
      $('papers').scrollIntoView({ block: 'start' });
      $('collection-title').setAttribute('tabindex', '-1');
      $('collection-title').focus({ preventScroll: true });
    }
  });
  window.addEventListener('popstate', () => { state = readURL(); render(); });
  document.querySelectorAll('a[href="#criteria"]').forEach(a => a.addEventListener('click', () => { $('criteria').open = true; }));
  const breakpoint = matchMedia('(max-width: 760px)');
  disclosure.open = !breakpoint.matches;
  breakpoint.addEventListener('change', () => { disclosure.open = !breakpoint.matches; });
  if (location.hash === '#criteria') $('criteria').open = true;
  state = readURL();
  render();

  if (document.modelContext?.registerTool) {
    const lifecycle = new AbortController();
    const tool = {
      name: 'filter_social_simulation_papers',
      title: 'Filter social simulation papers',
      description: 'Apply search, topic, year, and sorting to the visible published-paper collection. Returns the matching papers and updates the page URL.',
      inputSchema: { type: 'object', properties: { query: { type: 'string', maxLength: 250 }, topic: { type: 'string', enum: ['', ...topicMap.keys()] }, year: { type: 'string', enum: ['', ...years] }, sort: { type: 'string', enum: [...validSorts] } }, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      execute(input) {
        if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(k => !['query','topic','year','sort'].includes(k))) throw new Error('Use query, topic, year, and sort only.');
        if (input.query !== undefined && (typeof input.query !== 'string' || input.query.length > 250)) throw new Error('Query must be a string of at most 250 characters.');
        if (input.topic !== undefined && input.topic !== '' && !topicMap.has(input.topic)) throw new Error('Unknown topic.');
        if (input.year !== undefined && input.year !== '' && !years.has(input.year)) throw new Error('Unknown publication year.');
        if (input.sort !== undefined && !validSorts.has(input.sort)) throw new Error('Unknown sort order.');
        const matches = update({ q: input.query ?? '', topic: input.topic ?? '', year: input.year ?? '', sort: input.sort ?? 'newest' }, 'push');
        return { count: matches.length, papers: matches.map(({ title, venue, url }) => ({ title, venue, url })) };
      }
    };
    try { Promise.resolve(document.modelContext.registerTool(tool, { signal: lifecycle.signal })).catch(() => {}); } catch (_) {}
    window.addEventListener('pagehide', () => lifecycle.abort(), { once: true });
  }
})();
