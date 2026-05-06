// Member view — opened via shared setlist link: /?ids=1,2,3

let songs = [];
let currentIdx = 0;
let showChords = false;
let deferredInstallPrompt = null;

const chordToggle = document.getElementById('chordToggle');
const welcomeScreen = document.getElementById('welcomeScreen');
const songNav = document.getElementById('songNav');
const songView = document.getElementById('songView');
const installBanner = document.getElementById('installBanner');
const installBtn = document.getElementById('installBtn');

// ── Chord parser ──────────────────────────────────────────────
function parseLine(line) {
  // Returns [{chord, text}, ...]
  if (!line.includes('[')) return [{ chord: '', text: line }];
  const segments = [];
  const firstBracket = line.indexOf('[');
  if (firstBracket > 0) segments.push({ chord: '', text: line.slice(0, firstBracket) });
  const re = /\[([^\]]+)\]([^\[]*)/g;
  let m;
  while ((m = re.exec(line)) !== null) segments.push({ chord: m[1], text: m[2] });
  return segments;
}

function renderLyrics(raw, showCh) {
  const lines = raw.split('\n');
  return lines.map(line => {
    const trimmed = line.trim();
    // Section labels like [副歌] [Verse] — treat as label if no chord after ]
    if (/^\[[一-鿿\w ]+\]$/.test(trimmed)) {
      return `<div class="lyric-section-label">${trimmed.slice(1, -1)}</div>`;
    }
    if (trimmed === '') return '<div style="height:12px"></div>';

    const segments = parseLine(line);
    const hasChords = segments.some(s => s.chord);

    if (!showCh || !hasChords) {
      const text = segments.map(s => s.text).join('');
      return `<div class="lyric-line"><span class="lyric-text">${escHtml(text)}</span></div>`;
    }

    const segsHtml = segments.map(s =>
      `<span class="lyric-segment">` +
      `<span class="chord-symbol">${escHtml(s.chord) || ' '}</span>` +
      `<span class="lyric-text">${escHtml(s.text) || ' '}</span>` +
      `</span>`
    ).join('');
    return `<div class="lyric-line has-chords">${segsHtml}</div>`;
  }).join('');
}

function escHtml(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ── Rendering ─────────────────────────────────────────────────
function renderSong(song) {
  const ytHtml = song.youtubeId
    ? `<div class="yt-wrap">
        <iframe src="https://www.youtube.com/embed/${song.youtubeId}?rel=0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen loading="lazy"></iframe>
       </div>`
    : '';

  const catLabels = { praise: '赞美', worship: '敬拜', slow: '抒情', fast: '快歌', dialect: '方言' };

  songView.innerHTML = `
    <div class="song-title-big">${escHtml(song.title)}</div>
    <div class="song-meta-row">
      <span class="tag tag-${song.category}">${catLabels[song.category] || song.category}</span>
    </div>
    ${ytHtml}
    <div class="lyrics-block" id="lyricsBlock">
      ${renderLyrics(song.lyrics, showChords)}
    </div>
  `;
}

function updateNav() {
  songNav.innerHTML = songs.map((s, i) =>
    `<button class="song-nav-btn ${i === currentIdx ? 'active' : ''}" data-idx="${i}">
      ${i + 1}. ${escHtml(s.title)}
    </button>`
  ).join('');
  songNav.querySelectorAll('.song-nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      currentIdx = parseInt(btn.dataset.idx);
      updateNav();
      renderSong(songs[currentIdx]);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });
}

function updateChordToggle() {
  chordToggle.classList.toggle('on', showChords);
  chordToggle.querySelector('.dot').style.background = showChords ? 'var(--gold)' : '';
}

// ── Init ──────────────────────────────────────────────────────
async function init() {
  const params = new URLSearchParams(location.search);
  const idsParam = params.get('ids');
  if (!idsParam) return; // show welcome screen

  const ids = idsParam.split(',').map(s => s.trim()).filter(Boolean);
  if (!ids.length) return;

  try {
    const res = await fetch('/api/songs');
    const all = await res.json();
    songs = ids.map(id => all.find(s => s.id === id)).filter(Boolean);
  } catch {
    songs = [];
  }

  if (!songs.length) return;

  welcomeScreen.classList.add('hidden');
  songNav.classList.remove('hidden');
  songView.classList.remove('hidden');

  updateNav();
  renderSong(songs[0]);
}

// ── Events ────────────────────────────────────────────────────
chordToggle.addEventListener('click', () => {
  showChords = !showChords;
  updateChordToggle();
  if (songs.length) {
    const block = document.getElementById('lyricsBlock');
    if (block) block.innerHTML = renderLyrics(songs[currentIdx].lyrics, showChords);
  }
});

// PWA install
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredInstallPrompt = e;
  installBanner.classList.remove('hidden');
});

installBtn.addEventListener('click', async () => {
  if (!deferredInstallPrompt) return;
  deferredInstallPrompt.prompt();
  const { outcome } = await deferredInstallPrompt.userChoice;
  if (outcome === 'accepted') installBanner.classList.add('hidden');
  deferredInstallPrompt = null;
});

// Service worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

init();
