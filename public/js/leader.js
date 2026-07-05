// Leader view — browse songs, build setlist, share via WhatsApp

const MAX_SONGS = 8;
let allSongs = [];
let selected = []; // array of song ids
let activeCat = 'all';
let searchQuery = '';

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

// ── Render song library ───────────────────────────────────────
function renderList() {
  const q = searchQuery.trim().toLowerCase();
  const filtered = allSongs.filter(s => {
    const matchesCat = (() => {
      if (activeCat === 'all') return true;
      if (activeCat === 'lifeline') return s.label === 'lifeline';
      if (activeCat === 'worship') return s.category === 'worship' || s.category === 'slow';
      return s.category === activeCat;
    })();
    const matchesSearch = !q || s.title.toLowerCase().includes(q);
    return matchesCat && matchesSearch;
  });

  // Sort alphabetically by title (Chinese locale)
  filtered.sort((a, b) => a.title.localeCompare(b.title, 'zh'));

  if (!filtered.length) {
    songListEl.innerHTML = '<p class="text-muted" style="padding:20px 0;text-align:center">没有找到歌曲</p>';
    return;
  }

  songListEl.innerHTML = filtered.map(song => {
    const isSel = selected.includes(song.id);
    const isDisabled = !isSel && selected.length >= MAX_SONGS;
    return `<div class="song-card ${isSel ? 'selected' : ''} ${isDisabled ? 'disabled' : ''}"
               data-id="${song.id}"
               style="${isDisabled ? 'opacity:0.45;cursor:not-allowed' : ''}">
      <div class="song-card-info">
        <div class="song-card-title">${escHtml(song.title)}</div>
        <div class="song-card-meta">
          <span class="tag tag-${song.category}">${catLabels[song.category] || song.category}</span>
          ${song.youtubeId ? '<span style="font-size:0.75rem;color:var(--text-muted)">▶ YouTube</span>' : ''}
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
  window.open(`https://wa.me/?text=${encodeURIComponent(msg)}`, '_blank');
});

confirmTelegramBtn.addEventListener('click', () => {
  const { msg } = buildShareData();
  previewModal.style.display = 'none';
  window.open(`https://t.me/share/url?url=${encodeURIComponent(msg)}`, '_blank');
});

confirmCopyBtn.addEventListener('click', () => {
  const { appUrl } = buildShareData();
  previewModal.style.display = 'none';
  navigator.clipboard.writeText(appUrl).then(() => {
    const orig = copyLinkBtn.textContent;
    copyLinkBtn.textContent = '✅ 已复制！';
    setTimeout(() => { copyLinkBtn.textContent = orig; }, 2000);
  });
});

closePreviewBtn.addEventListener('click', () => {
  previewModal.style.display = 'none';
});

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
  try {
    const res = await fetch('/api/songs');
    allSongs = await res.json();
  } catch {
    allSongs = [];
    songListEl.innerHTML = '<p class="text-muted" style="text-align:center;padding:20px">无法加载歌曲</p>';
    return;
  }

  // Show total count on the 全部 tab
  const allBtn = document.querySelector('.cat-btn[data-cat="all"]');
  if (allBtn) allBtn.textContent = `全部（${allSongs.length}）`;

  renderList();
  renderSetlist();
}

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

init();
