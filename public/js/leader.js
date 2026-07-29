// Leader view — browse songs, build setlist, share via WhatsApp

const MAX_SONGS = 8;
const USAGE_KEY = 'leader_usage_v1';
const SETLIST_HISTORY_KEY = 'leader_setlists_v1';
const THEME_KEY = 'leader_theme_v1';

let allSongs = [];
let selected = [];
let activeCat = 'all';
let searchQuery = '';
let usageStats = {};
let setlistHistory = [];

const songListEl = document.getElementById('songList');
const setlistSongsEl = document.getElementById('setlistSongs');
const setlistCount = document.getElementById('setlistCount');
const shareBtn = document.getElementById('shareBtn');
const shareTelegramBtn = document.getElementById('shareTelegramBtn');
const copyLinkBtn = document.getElementById('copyLinkBtn');
const clearBtn = document.getElementById('clearBtn');
const searchInput = document.getElementById('searchInput');

const catLabels = { praise: '赞美', worship: '敬拜', slow: '抒情', fast: '快歌', dialect: '方言' };

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Dark mode (leader app is dark by default; toggle adds light mode) ──
function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === 'light') document.documentElement.setAttribute('data-theme', 'light');
  updateThemeBtn();
}
function toggleTheme() {
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  if (isLight) {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem(THEME_KEY);
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem(THEME_KEY, 'light');
  }
  updateThemeBtn();
}
function updateThemeBtn() {
  const btn = document.getElementById('themeBtn');
  if (!btn) return;
  const isLight = document.documentElement.getAttribute('data-theme') === 'light';
  btn.textContent = isLight ? '🌙' : '☀️';
}
document.getElementById('themeBtn').addEventListener('click', toggleTheme);

// ── Usage stats ───────────────────────────────────────────────
function loadUsage() {
  try { usageStats = JSON.parse(localStorage.getItem(USAGE_KEY)) || {}; } catch { usageStats = {}; }
}
function trackUsage(id) {
  usageStats[id] = (usageStats[id] || 0) + 1;
  localStorage.setItem(USAGE_KEY, JSON.stringify(usageStats));
}

// ── Setlist history ───────────────────────────────────────────
function loadHistory() {
  try { setlistHistory = JSON.parse(localStorage.getItem(SETLIST_HISTORY_KEY)) || []; } catch { setlistHistory = []; }
}
function saveToHistory() {
  const songs = selected.map(id => allSongs.find(x => x.id === id)).filter(Boolean);
  if (!songs.length) return;
  const entry = {
    date: new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric', weekday: 'short' }),
    songs: songs.map(s => ({ id: s.id, title: s.title }))
  };
  setlistHistory.unshift(entry);
  if (setlistHistory.length > 30) setlistHistory.pop();
  localStorage.setItem(SETLIST_HISTORY_KEY, JSON.stringify(setlistHistory));
}

// ── Pinyin search ─────────────────────────────────────────────
const _pinyinCache = {};
function getPinyinStr(title) {
  if (_pinyinCache[title] !== undefined) return _pinyinCache[title];
  let result = '';
  try {
    if (window.pinyinPro) {
      const full = window.pinyinPro.pinyin(title, { toneType: 'none', separator: ' ' }).toLowerCase();
      result = full + ' ' + full.replace(/\s/g, '');
    }
  } catch (_) {}
  _pinyinCache[title] = result;
  return result;
}

// ── Render song library ───────────────────────────────────────
function renderList() {
  const q = searchQuery.trim().toLowerCase();
  const isAscii = q && /^[a-z\s]+$/.test(q);

  const filtered = allSongs.filter(s => {
    const matchesCat = (() => {
      if (activeCat === 'all') return true;
      if (activeCat === 'top') return (usageStats[s.id] || 0) > 0;
      if (activeCat === 'lifeline') return s.label === 'lifeline';
      if (activeCat === 'worship') return s.category === 'worship' || s.category === 'slow';
      return s.category === activeCat;
    })();
    if (!matchesCat) return false;
    if (!q) return true;
    if (s.title.toLowerCase().includes(q)) return true;
    if (isAscii && getPinyinStr(s.title).includes(q)) return true;
    return false;
  });

  if (activeCat === 'top') {
    filtered.sort((a, b) => (usageStats[b.id] || 0) - (usageStats[a.id] || 0));
  } else {
    filtered.sort((a, b) => a.title.localeCompare(b.title, 'zh'));
  }

  if (!filtered.length) {
    songListEl.innerHTML = activeCat === 'top'
      ? '<p class="text-muted" style="padding:20px 0;text-align:center">还没有使用记录<br><small>选歌后系统自动追踪</small></p>'
      : '<p class="text-muted" style="padding:20px 0;text-align:center">没有找到歌曲</p>';
    return;
  }

  songListEl.innerHTML = filtered.map(song => {
    const isSel = selected.includes(song.id);
    const isDisabled = !isSel && selected.length >= MAX_SONGS;
    const useCount = usageStats[song.id] || 0;
    return `<div class="song-card ${isSel ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}"
               data-id="${song.id}"
               style="${isDisabled ? 'opacity:0.45;cursor:not-allowed' : ''}">
      <div class="song-card-info">
        <div class="song-card-title">${escHtml(song.title)}</div>
        <div class="song-card-meta">
          <span class="tag tag-${song.category}">${catLabels[song.category] || song.category}</span>
          ${song.youtubeId ? '<span style="font-size:0.75rem;color:var(--text-muted)">▶ YouTube</span>' : ''}
          ${useCount > 0 ? `<span class="usage-badge">🔥 ${useCount}次</span>` : ''}
        </div>
      </div>
      <div class="song-check">${isSel ? '✓' : ''}</div>
    </div>`;
  }).join('');

  songListEl.querySelectorAll('.song-card').forEach(card => {
    card.addEventListener('click', () => toggleSong(card.dataset.id));
  });
}

// ── Render setlist panel ──────────────────────────────────────
function renderSetlist() {
  const count = selected.length;
  setlistCount.textContent = `（${count}/${MAX_SONGS}）`;
  shareBtn.disabled = count === 0;
  shareTelegramBtn.disabled = count === 0;
  copyLinkBtn.disabled = count === 0;
  const saveBtn = document.getElementById('saveSetlistBtn');
  if (saveBtn) saveBtn.disabled = count === 0;

  if (!count) {
    setlistSongsEl.innerHTML = '<span class="setlist-empty">尚未选择歌曲</span>';
    return;
  }

  setlistSongsEl.innerHTML = selected.map(id => {
    const song = allSongs.find(s => s.id === id);
    if (!song) return '';
    return `<div class="setlist-chip">
      ${escHtml(song.title)}
      <button class="setlist-chip-remove" data-id="${id}" title="移除">×</button>
    </div>`;
  }).join('');

  setlistSongsEl.querySelectorAll('.setlist-chip-remove').forEach(btn => {
    btn.addEventListener('click', e => {
      e.stopPropagation();
      toggleSong(btn.dataset.id);
    });
  });
}

function toggleSong(id) {
  if (selected.includes(id)) {
    selected = selected.filter(s => s !== id);
  } else {
    if (selected.length >= MAX_SONGS) return;
    selected.push(id);
    trackUsage(id);
  }
  renderList();
  renderSetlist();
}

// ── Preview modal ─────────────────────────────────────────────
const previewModal = document.getElementById('previewModal');
const previewList = document.getElementById('previewList');
const confirmWhatsappBtn = document.getElementById('confirmWhatsappBtn');
const confirmTelegramBtn = document.getElementById('confirmTelegramBtn');
const confirmCopyBtn = document.getElementById('confirmCopyBtn');
const closePreviewBtn = document.getElementById('closePreviewBtn');

function buildShareData() {
  const ids = selected.join(',');
  const appUrl = `${location.origin}/?ids=${ids}`;
  const songs = selected.map(id => allSongs.find(x => x.id === id)).filter(Boolean);
  const msg = `🎵 今天的敬拜歌单：\n${songs.map((s, i) => `${i + 1}. ${s.title}`).join('\n')}\n\n点击链接查看歌词：\n${appUrl}`;
  return { songs, msg, appUrl };
}

function openPreviewModal() {
  const { songs, appUrl } = buildShareData();
  previewList.innerHTML = `
    <p style="font-size:0.75rem;color:var(--text-muted);margin:0 0 10px">点击歌名可查看歌词 👇</p>
    <div style="border-radius:12px;overflow:hidden;border:1px solid var(--border);margin-bottom:12px">
      ${songs.map((s, i) => `
        <div class="preview-song-item" data-id="${s.id}" style="border-bottom:${i < songs.length - 1 ? '1px solid var(--border)' : 'none'}">
          <div class="preview-song-header" style="display:flex;align-items:center;padding:12px 14px;cursor:pointer;gap:10px;background:var(--surface)">
            <span style="color:var(--text-muted);font-size:0.8rem;min-width:18px">${i + 1}.</span>
            <span style="flex:1;font-size:1rem;color:var(--text);font-weight:500">${escHtml(s.title)}</span>
            <span class="preview-chevron" style="color:var(--text-muted);font-size:0.8rem;transition:transform 0.2s">▼</span>
          </div>
          <div class="preview-lyrics" style="display:none;padding:12px 14px 14px 42px;background:var(--bg);font-size:0.85rem;line-height:1.8;color:var(--text-muted);white-space:pre-wrap">${escHtml(s.lyrics || '（无歌词）')}</div>
        </div>`).join('')}
    </div>
    <p style="font-size:0.75rem;color:var(--text-muted);margin:0">🔗 ${escHtml(appUrl)}</p>`;

  previewList.querySelectorAll('.preview-song-header').forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const lyrics = item.querySelector('.preview-lyrics');
      const chevron = header.querySelector('.preview-chevron');
      const isOpen = lyrics.style.display !== 'none';
      lyrics.style.display = isOpen ? 'none' : 'block';
      chevron.style.transform = isOpen ? '' : 'rotate(180deg)';
    });
  });
  previewModal.style.display = 'flex';
}

shareBtn.addEventListener('click', () => { if (selected.length) openPreviewModal(); });
shareTelegramBtn.addEventListener('click', () => { if (selected.length) openPreviewModal(); });
copyLinkBtn.addEventListener('click', () => { if (selected.length) openPreviewModal(); });

confirmWhatsappBtn.addEventListener('click', () => {
  const { msg } = buildShareData();
  previewModal.style.display = 'none';
  saveToHistory();
  window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank');
});

confirmTelegramBtn.addEventListener('click', () => {
  const { msg } = buildShareData();
  previewModal.style.display = 'none';
  saveToHistory();
  window.open(`https://t.me/share/url?url=${encodeURIComponent(msg)}`, '_blank');
});

confirmCopyBtn.addEventListener('click', () => {
  const { msg } = buildShareData();
  previewModal.style.display = 'none';
  saveToHistory();
  navigator.clipboard.writeText(msg).then(() => {
    const orig = copyLinkBtn.textContent;
    copyLinkBtn.textContent = '✅ 已复制！';
    setTimeout(() => { copyLinkBtn.textContent = orig; }, 2000);
  });
});

closePreviewBtn.addEventListener('click', () => {
  previewModal.style.display = 'none';
});

// ── Manual save setlist button ────────────────────────────────
const saveSetlistBtn = document.getElementById('saveSetlistBtn');
if (saveSetlistBtn) {
  saveSetlistBtn.addEventListener('click', () => {
    saveToHistory();
    const orig = saveSetlistBtn.textContent;
    saveSetlistBtn.textContent = '✅ 已保存！';
    setTimeout(() => { saveSetlistBtn.textContent = orig; }, 2000);
  });
}

// ── History modal ─────────────────────────────────────────────
const historyModal = document.getElementById('historyModal');
const historyList = document.getElementById('historyList');
const historyBtn = document.getElementById('historyBtn');
const closeHistoryBtn = document.getElementById('closeHistoryBtn');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');

function openHistoryModal() {
  if (!setlistHistory.length) {
    historyList.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:30px 0">还没有保存的歌单记录</p>';
  } else {
    historyList.innerHTML = setlistHistory.map((entry, i) => `
      <div style="border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:10px">
        <div style="font-size:0.8rem;color:var(--text-muted);margin-bottom:8px;font-weight:600">${escHtml(entry.date)}</div>
        <div style="font-size:0.9rem;line-height:1.8;color:var(--text)">${entry.songs.map((s, j) => `${j + 1}. ${escHtml(s.title)}`).join('<br>')}</div>
        <button class="btn btn-ghost btn-sm restore-btn" data-idx="${i}" style="margin-top:10px">↩ 恢复此歌单</button>
      </div>`).join('');

    historyList.querySelectorAll('.restore-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const entry = setlistHistory[parseInt(btn.dataset.idx)];
        selected = entry.songs.map(s => s.id).filter(id => allSongs.find(s => s.id === id));
        historyModal.style.display = 'none';
        renderList();
        renderSetlist();
      });
    });
  }
  historyModal.style.display = 'flex';
}

if (historyBtn) historyBtn.addEventListener('click', openHistoryModal);
if (closeHistoryBtn) closeHistoryBtn.addEventListener('click', () => { historyModal.style.display = 'none'; });
if (clearHistoryBtn) {
  clearHistoryBtn.addEventListener('click', () => {
    if (!confirm('确定清除所有歌单历史？')) return;
    setlistHistory = [];
    localStorage.removeItem(SETLIST_HISTORY_KEY);
    openHistoryModal();
  });
}

clearBtn.addEventListener('click', () => {
  selected = [];
  renderList();
  renderSetlist();
});

// ── Search ────────────────────────────────────────────────────
if (searchInput) {
  searchInput.addEventListener('input', () => {
    searchQuery = searchInput.value;
    renderList();
  });
}

// ── Category filter ───────────────────────────────────────────
document.querySelectorAll('.cat-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeCat = btn.dataset.cat;
    renderList();
  });
});

// ── Force SW update + reload when new SW takes control ──────
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistration().then(reg => { if (reg) reg.update(); });
  navigator.serviceWorker.addEventListener('controllerchange', () => window.location.reload());
}

// ── Init ──────────────────────────────────────────────────────
async function init() {
  initTheme();
  loadUsage();
  loadHistory();
  try {
    const res = await fetch('/api/songs');
    allSongs = await res.json();
  } catch {
    allSongs = [];
    songListEl.innerHTML = '<p class="text-muted" style="text-align:center;padding:20px">无法加载歌曲</p>';
    return;
  }

  const allBtn = document.querySelector('.cat-btn[data-cat="all"]');
  if (allBtn) allBtn.textContent = `全部（${allSongs.length}）`;

  renderList();
  renderSetlist();
}

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

init();
