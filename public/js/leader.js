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

// ── Build share message ───────────────────────────────────────
function buildShareMsg() {
  const ids = selected.join(',');
  const appUrl = `${location.origin}/?ids=${ids}`;
  const songNames = selected.map(id => {
    const s = allSongs.find(x => x.id === id);
    return s ? s.title : id;
  });
  const text = `🎵 今天的敬拜歌单：\n${songNames.map((n, i) => `${i + 1}. ${n}`).join('\n')}\n\n点击链接查看歌词：\n${appUrl}`;
  return { text, appUrl };
}

// ── Share via WhatsApp ────────────────────────────────────────
shareBtn.addEventListener('click', () => {
  if (!selected.length) return;
  const { text } = buildShareMsg();
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank');
});

// ── Share via Telegram ────────────────────────────────────────
shareTelegramBtn.addEventListener('click', () => {
  if (!selected.length) return;
  const { text } = buildShareMsg();
  window.open(`https://t.me/share/url?url=${encodeURIComponent(text)}`, '_blank');
});

// ── Copy link ─────────────────────────────────────────────────
copyLinkBtn.addEventListener('click', () => {
  if (!selected.length) return;
  const { appUrl } = buildShareMsg();
  navigator.clipboard.writeText(appUrl).then(() => {
    const orig = copyLinkBtn.textContent;
    copyLinkBtn.textContent = '✅ 已复制！';
    setTimeout(() => { copyLinkBtn.textContent = orig; }, 2000);
  });
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
