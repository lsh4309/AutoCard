/**
 * 프로젝트 / 솔루션 / 계정과목 공통: 순서 편집 모드 (드래그 + 맨위/위/아래/맨아래)
 * config: { itemsScriptId, tbodyId, theadId, apiReorder, idType: 'string'|'number', nameLabel }
 */
(function () {
  'use strict';

  let cfg = null;
  let items = [];
  let snapshot = null;
  let reorderMode = false;
  let openMenuIndex = null;
  let dragFromHandle = false;

  function parseItems() {
    const el = document.getElementById(cfg.itemsScriptId);
    if (!el) return [];
    try {
      return JSON.parse(el.textContent || '[]');
    } catch {
      return [];
    }
  }

  function escapeHtml(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  function activeBadge(active) {
    return active
      ? '<span class="badge-ok">활성</span>'
      : '<span class="badge-error">비활성</span>';
  }

  function renderNormalThead() {
    const th = document.getElementById(cfg.theadId);
    if (!th) return;
    th.innerHTML =
      '<tr>' +
      `<th class="px-4 py-3 text-left text-gray-600">${escapeHtml(cfg.nameColumnTitle)}</th>` +
      '<th class="px-4 py-3 text-center text-gray-600 w-28">활성</th>' +
      '<th class="px-4 py-3 text-center text-gray-600 w-36">관리</th>' +
      '</tr>';
  }

  function renderNormalBody() {
    const tb = document.getElementById(cfg.tbodyId);
    if (!tb) return;
    if (!items.length) {
      tb.innerHTML =
        `<tr><td colspan="3" class="px-6 py-8 text-center text-gray-400">등록된 ${escapeHtml(cfg.emptyLabel)} 없습니다.</td></tr>`;
      return;
    }
    tb.innerHTML = items
      .map((row, index) => {
        const nameEsc = escapeHtml(String(row.name));
        return (
          `<tr class="border-t border-gray-100 hover:bg-gray-50">` +
          `<td class="px-4 py-3 font-medium ${cfg.nameCellClass || ''}">${nameEsc}</td>` +
          `<td class="px-4 py-3 text-center">${activeBadge(row.active_yn)}</td>` +
          `<td class="px-4 py-3 text-center whitespace-nowrap">` +
          `<button type="button" class="js-lookup-edit text-blue-600 hover:text-blue-800 mr-3" data-index="${index}" title="수정" aria-label="수정">` +
          `<i class="fa-solid fa-pen-to-square"></i></button>` +
          `<button type="button" class="js-lookup-delete text-red-500 hover:text-red-700" data-index="${index}" title="삭제" aria-label="삭제">` +
          `<i class="fa-solid fa-trash"></i></button>` +
          `</td></tr>`
        );
      })
      .join('');

    tb.querySelectorAll('.js-lookup-edit').forEach((btn) => {
      btn.addEventListener('click', () => {
        const row = items[Number(btn.dataset.index)];
        if (row && cfg.onEdit) cfg.onEdit(row);
      });
    });
    tb.querySelectorAll('.js-lookup-delete').forEach((btn) => {
      btn.addEventListener('click', () => {
        const row = items[Number(btn.dataset.index)];
        if (row && cfg.onDelete) cfg.onDelete(row.id);
      });
    });
  }

  function moveItem(from, to) {
    if (from === to) return;
    if (from < 0 || from >= items.length) return;
    if (to < 0 || to >= items.length) return;
    const copy = items.slice();
    const [removed] = copy.splice(from, 1);
    copy.splice(to, 0, removed);
    items = copy;
    renderReorderBody();
  }

  function closeMenu() {
    openMenuIndex = null;
    document.querySelectorAll('.js-reorder-menu-panel').forEach((p) => p.classList.add('hidden'));
  }

  document.addEventListener('click', (e) => {
    if (!reorderMode) return;
    if (!e.target.closest('.js-reorder-menu-wrap')) closeMenu();
  });

  function renderReorderThead() {
    const th = document.getElementById(cfg.theadId);
    if (!th) return;
    th.innerHTML =
      '<tr>' +
      `<th class="px-4 py-3 text-left text-gray-600">${escapeHtml(cfg.nameColumnTitle)}</th>` +
      '<th class="px-4 py-3 text-center text-gray-600 w-24">활성</th>' +
      '<th class="px-4 py-3 text-center text-gray-600 w-20">순서</th>' +
      '<th class="px-4 py-3 text-center text-gray-600 w-28">이동</th>' +
      '</tr>';
  }

  function renderReorderBody() {
    const tb = document.getElementById(cfg.tbodyId);
    if (!tb) return;
    tb.innerHTML = items
      .map((row, index) => {
        const nameEsc = escapeHtml(String(row.name));
        return (
          `<tr class="border-t border-gray-100 hover:bg-gray-50 lookup-reorder-row" data-index="${index}" draggable="true">` +
          `<td class="px-4 py-3 font-medium ${cfg.nameCellClass || ''}">${nameEsc}</td>` +
          `<td class="px-4 py-3 text-center">${activeBadge(row.active_yn)}</td>` +
          `<td class="px-4 py-3 text-center">` +
          `<button type="button" class="inline-flex items-center justify-center w-9 h-9 rounded-lg border border-gray-200 bg-gray-50 text-gray-600 hover:bg-gray-100 js-drag-handle cursor-grab active:cursor-grabbing" aria-label="끌어서 순서 변경">` +
          `<i class="fa-solid fa-grip-vertical" aria-hidden="true"></i></button>` +
          `</td>` +
          `<td class="px-4 py-3 text-center relative js-reorder-menu-wrap">` +
          `<button type="button" class="inline-flex items-center gap-1 text-xs text-gray-700 border border-gray-200 rounded-lg px-2 py-1.5 hover:bg-gray-50 js-reorder-menu-btn" data-index="${index}" aria-label="순서 이동 메뉴" aria-haspopup="true">` +
          `<i class="fa-solid fa-ellipsis-vertical"></i><span>이동</span></button>` +
          `<div class="js-reorder-menu-panel hidden absolute right-4 top-full mt-1 z-[60] min-w-[9rem] bg-white border border-gray-200 rounded-lg shadow-lg py-1 text-left">` +
          `<button type="button" class="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 js-move" data-move="top">맨 위</button>` +
          `<button type="button" class="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 js-move" data-move="up">위로</button>` +
          `<button type="button" class="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 js-move" data-move="down">아래로</button>` +
          `<button type="button" class="block w-full text-left px-3 py-2 text-xs hover:bg-gray-50 js-move" data-move="bottom">맨 아래</button>` +
          `</div></td></tr>`
        );
      })
      .join('');

    tb.querySelectorAll('.lookup-reorder-row').forEach((tr) => {
      const idx = Number(tr.dataset.index);

      tr.querySelectorAll('.js-drag-handle').forEach((h) => {
        h.addEventListener('mousedown', () => {
          dragFromHandle = true;
          window.addEventListener(
            'mouseup',
            () => {
              dragFromHandle = false;
            },
            { once: true }
          );
        });
      });

      tr.addEventListener('dragstart', (e) => {
        if (!dragFromHandle) {
          e.preventDefault();
          return;
        }
        if (e.target.closest('.js-reorder-menu-wrap')) {
          e.preventDefault();
          return;
        }
        tr.classList.add('opacity-50');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', String(idx));
      });

      tr.addEventListener('dragend', () => {
        tr.classList.remove('opacity-50');
        tb.querySelectorAll('.lookup-reorder-row').forEach((r) => r.classList.remove('ring-2', 'ring-blue-300'));
      });

      tr.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        tr.classList.add('ring-2', 'ring-blue-300');
      });

      tr.addEventListener('dragleave', () => {
        tr.classList.remove('ring-2', 'ring-blue-300');
      });

      tr.addEventListener('drop', (e) => {
        e.preventDefault();
        tr.classList.remove('ring-2', 'ring-blue-300');
        const from = Number(e.dataTransfer.getData('text/plain'));
        const to = idx;
        if (Number.isNaN(from)) return;
        moveItem(from, to);
      });
    });

    tb.querySelectorAll('.js-reorder-menu-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const i = Number(btn.dataset.index);
        const panel = btn.nextElementSibling;
        const wasOpen = openMenuIndex === i;
        closeMenu();
        if (!wasOpen && panel) {
          panel.classList.remove('hidden');
          openMenuIndex = i;
        }
      });
    });

    tb.querySelectorAll('.js-move').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const wrap = btn.closest('.js-reorder-menu-wrap');
        const tr = wrap && wrap.closest('tr');
        if (!tr) return;
        const i = Number(tr.dataset.index);
        const move = btn.dataset.move;
        closeMenu();
        if (move === 'top') moveItem(i, 0);
        else if (move === 'up') moveItem(i, i - 1);
        else if (move === 'down') moveItem(i, i + 1);
        else if (move === 'bottom') moveItem(i, items.length - 1);
      });
    });
  }

  function setToolbarMode(editing) {
    const enter = document.getElementById('btn-reorder-enter');
    const bar = document.getElementById('reorder-toolbar');
    const addBtn = document.getElementById('btn-lookup-add');
    if (enter) enter.classList.toggle('hidden', editing);
    if (bar) bar.classList.toggle('hidden', !editing);
    if (addBtn) addBtn.classList.toggle('hidden', editing);
  }

  function setTableWrapReorder(active) {
    const w = cfg.tableWrapId && document.getElementById(cfg.tableWrapId);
    if (!w) return;
    if (active) {
      w.classList.remove('overflow-hidden');
      w.classList.add('overflow-visible');
    } else {
      w.classList.add('overflow-hidden');
      w.classList.remove('overflow-visible');
    }
  }

  function enterReorder() {
    if (!items.length) {
      if (typeof showToast === 'function') {
        showToast('순서를 바꿀 항목이 없습니다', 'warning');
      }
      return;
    }
    snapshot = JSON.parse(JSON.stringify(items));
    reorderMode = true;
    setToolbarMode(true);
    setTableWrapReorder(true);
    renderReorderThead();
    renderReorderBody();
    closeMenu();
  }

  function exitReorder() {
    reorderMode = false;
    setToolbarMode(false);
    setTableWrapReorder(false);
    renderNormalThead();
    renderNormalBody();
    closeMenu();
  }

  function cancelReorder() {
    if (snapshot) items = snapshot;
    snapshot = null;
    exitReorder();
  }

  async function saveReorder() {
    const orderedIds = items.map((r) => r.id);
    try {
      const res = await fetch(cfg.apiReorder, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ordered_ids: orderedIds }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || '저장 실패');
      }
      if (typeof showToast === 'function') showToast('순서를 저장했습니다', 'success');
      snapshot = null;
      reorderMode = false;
      setToolbarMode(false);
      setTimeout(() => window.location.reload(), 400);
    } catch (e) {
      if (typeof showToast === 'function') showToast(e.message || '오류', 'error');
    }
  }

  function bindToolbar() {
    document.getElementById('btn-reorder-enter')?.addEventListener('click', enterReorder);
    document.getElementById('btn-reorder-cancel')?.addEventListener('click', cancelReorder);
    document.getElementById('btn-reorder-save')?.addEventListener('click', saveReorder);
  }

  window.LookupReorder = {
    init(config) {
      cfg = config;
      items = parseItems();
      bindToolbar();
      renderNormalThead();
      renderNormalBody();
    },
    refreshFromDom() {
      items = parseItems();
      if (!reorderMode) {
        renderNormalThead();
        renderNormalBody();
      }
    },
  };
})();
