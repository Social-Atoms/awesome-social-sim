'use strict';
// Progressive enhancement: the native select remains the source of value and change events.
window.createRefinedSelect = function createRefinedSelect(select) {
  const icon = paths => `<svg aria-hidden="true" width="16" height="16" viewBox="0 0 20 20">${paths}</svg>`;
  const chevron = icon('<path d="m6 8 4 4 4-4"/>');
  const check = icon('<path d="m4.5 10 3.5 3.5 7.5-8"/>');
  const prefix = select.id === 'year'
    ? icon('<rect x="3.5" y="5" width="13" height="12" rx="1.5"/><path d="M6.5 3v4m7-4v4M3.5 9h13"/>')
    : icon('<path d="M6 4v12m-3-3 3 3 3-3m2-8h6m-6 5h4m-4 5h2"/>');
  const originalLabel = document.querySelector(`label[for="${select.id}"]`);
  originalLabel.id = `${select.id}-label`;
  const wrapper = document.createElement('div');
  wrapper.className = `refined-select refined-select--${select.id}`;
  select.before(wrapper);
  wrapper.append(select);
  select.hidden = true;
  const trigger = document.createElement('button');
  trigger.type = 'button';
  trigger.id = `${select.id}-trigger`;
  trigger.className = 'select-trigger';
  trigger.setAttribute('role', 'combobox');
  trigger.setAttribute('aria-haspopup', 'listbox');
  trigger.setAttribute('aria-expanded', 'false');
  trigger.setAttribute('aria-controls', `${select.id}-options`);
  trigger.setAttribute('aria-labelledby', `${originalLabel.id} ${select.id}-value`);
  trigger.innerHTML = `<span class="select-icon">${prefix}</span><span class="select-value" id="${select.id}-value"></span><span class="select-chevron">${chevron}</span>`;
  originalLabel.htmlFor = trigger.id;
  const list = document.createElement('div');
  list.className = 'select-menu';
  list.id = `${select.id}-options`;
  list.setAttribute('role', 'listbox');
  list.setAttribute('aria-labelledby', originalLabel.id);
  list.hidden = true;
  const options = [...select.options].map((option, index) => {
    const row = document.createElement('div');
    row.id = `${select.id}-option-${index}`;
    row.className = 'select-option';
    row.setAttribute('role', 'option');
    row.dataset.value = option.value;
    const label = document.createElement('span');
    label.textContent = option.textContent;
    const mark = document.createElement('span');
    mark.className = 'option-check';
    mark.innerHTML = check;
    row.append(label, mark);
    row.addEventListener('pointerdown', event => event.preventDefault());
    row.addEventListener('pointermove', () => activate(index));
    row.addEventListener('click', () => commit(index));
    list.append(row);
    return row;
  });
  wrapper.append(trigger, list);
  let isOpen = false, active = 0, typed = '', typedAt = 0;
  function sync() {
    trigger.querySelector('.select-value').textContent = select.selectedOptions[0].textContent;
    options.forEach(option => option.setAttribute('aria-selected', String(option.dataset.value === select.value)));
    if (isOpen) activate(select.selectedIndex);
  }
  function position() {
    if (!isOpen) return;
    const rect = trigger.getBoundingClientRect();
    const viewportHeight = window.visualViewport?.height || innerHeight;
    const width = Math.min(Math.max(rect.width, 190), innerWidth - 24);
    list.style.width = `${width}px`;
    list.style.left = `${Math.max(12, Math.min(rect.left, innerWidth - width - 12))}px`;
    const natural = options.length * 36 + 10;
    const below = viewportHeight - rect.bottom - 18;
    const above = rect.top - 18;
    const openAbove = below < Math.min(natural, 200) && above > below;
    list.style.maxHeight = `${Math.max(72, Math.min(288, openAbove ? above : below))}px`;
    list.style.top = openAbove ? 'auto' : `${rect.bottom + 6}px`;
    list.style.bottom = openAbove ? `${innerHeight - rect.top + 6}px` : 'auto';
  }
  function activate(index) {
    active = Math.max(0, Math.min(options.length - 1, index));
    options.forEach((option, i) => option.classList.toggle('is-active', i === active));
    trigger.setAttribute('aria-activedescendant', options[active].id);
    const row = options[active];
    if (row.offsetTop < list.scrollTop) list.scrollTop = row.offsetTop;
    else if (row.offsetTop + row.offsetHeight > list.scrollTop + list.clientHeight) list.scrollTop = row.offsetTop + row.offsetHeight - list.clientHeight;
  }
  function open() {
    // Opening one control closes the other without moving keyboard focus.
    document.dispatchEvent(new CustomEvent('catalogue-select-open', { detail: trigger.id }));
    isOpen = true;
    list.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
    position();
    activate(select.selectedIndex);
  }
  function close() {
    isOpen = false;
    list.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    trigger.removeAttribute('aria-activedescendant');
    typed = '';
  }
  function commit(index) {
    const value = options[index].dataset.value;
    close();
    if (select.value !== value) {
      select.value = value;
      select.dispatchEvent(new Event('change', { bubbles: true }));
    }
    sync();
  }
  trigger.addEventListener('click', () => isOpen ? close() : open());
  trigger.addEventListener('keydown', event => {
    if (event.isComposing || event.ctrlKey || event.metaKey || event.altKey) return;
    const { key } = event;
    if (key === 'Escape') { if (isOpen) { event.preventDefault(); close(); } return; }
    if (key === 'Tab') { if (isOpen) commit(active); return; }
    if (key === 'Enter' || key === ' ') { event.preventDefault(); isOpen ? commit(active) : open(); return; }
    if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(key)) {
      event.preventDefault();
      if (!isOpen) { open(); if (key === 'Home') activate(0); if (key === 'End') activate(options.length - 1); }
      else activate(key === 'Home' ? 0 : key === 'End' ? options.length - 1 : active + (key === 'ArrowDown' ? 1 : -1));
      return;
    }
    if (key.length === 1) {
      event.preventDefault();
      const now = Date.now();
      const buffer = now - typedAt > 700 ? '' : typed;
      if (!isOpen) open();
      typed = buffer + key.toLocaleLowerCase();
      typedAt = now;
      const index = options.findIndex(option => option.textContent.toLocaleLowerCase().startsWith(typed));
      if (index >= 0) activate(index);
    }
  });
  document.addEventListener('catalogue-select-open', event => { if (event.detail !== trigger.id) close(); });
  document.addEventListener('pointerdown', event => { if (isOpen && !wrapper.contains(event.target)) close(); });
  trigger.addEventListener('blur', close);
  window.addEventListener('resize', position);
  window.addEventListener('scroll', position, { passive: true, capture: true });
  window.visualViewport?.addEventListener('resize', position);
  select.addEventListener('change', sync);
  sync();
  return { sync, close };
};
