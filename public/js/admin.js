// Admin panel — add, edit, delete songs

let allSongs = [];
let editingId = null;

const songForm = document.getElementById('songForm');
const formTitle = document.getElementById('formTitle');
const editIdInput = document.getElementById('editId');
const fieldTitle = document.getElementById('fieldTitle');
const fieldCategory = document.getElementById('fieldCategory');
const fieldYoutube = document.getElementById('fieldYoutube');
const fieldLyrics = document.getElementById('fieldLyrics');
const fieldNoAds = document.getElementById('fieldNoAds');
const submitBtn = document.getElementById('submitBtn');
const cancelBtn = document.getElementById('cancelBtn');
const adminSongList = document.getElementById('adminSongList');
const adminSearch = document.getElementById('adminSearch');
const toast = document.getElementById('toast');

const catLabels = { praise: '赞美 Praise', worship: '敬拜 Worship', slow: '抒情 Slow', fast: '快歌 Fast' };

function escHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showToast(msg, type = 'success') {
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), 2800);
}

// ── Render song list ──────────────────────────────────────────
function renderAdminList() {
  const q = adminSearch.value.trim().toLowerCase();
  const songs = q ? allSongs.filter(s => s.title.toLowerCase().includes(q)) : allSongs;
  if (!songs.length) {
    adminSongList.innerHTML = '<p class="text-muted">没有找到歌曲。</p>';
    return;
  }
  adminSongList.innerHTML = songs.map(song => `
    <div class="admin-song-item">
      <div>
        <div class="admin-song-item-title">${escHtml(song.title)}</div>
        <span class="tag tag-${song.category}">${catLabels[song.category] || song.category}</span>
        ${song.noAds ? '<span class="noads-badge">✅无广告</span>' : ''}
      </div>
      <div class="admin-song-item-actions">
        <button class="btn btn-ghost btn-sm" data-edit="${song.id}">编辑</button>
        <button class="btn btn-danger btn-sm" data-delete="${song.id}">删除</button>
      </div>
    </div>
  `).join('');

  adminSongList.querySelectorAll('[data-edit]').forEach((btn) => {
    btn.addEventListener('click', () => startEdit(btn.dataset.edit));
  });
  adminSongList.querySelectorAll('[data-delete]').forEach(btn => {
    btn.addEventListener('click', () => deleteSong(btn.dataset.delete));
  });
}

// ── Form: edit mode ───────────────────────────────────────────
function startEdit(id) {
  const song = allSongs.find(s => s.id === id);
  if (!song) return;
  editingId = id;
  formTitle.textContent = '✏️ 编辑歌曲';
  submitBtn.textContent = '保存更改';
  fieldTitle.value = song.title;
  fieldCategory.value = song.category;
  fieldYoutube.value = song.youtubeId || '';
  fieldLyrics.value = song.lyrics;
  fieldNoAds.checked = !!song.noAds;
  window.scrollTo({ top: 0, behavior: 'smooth' });
  fieldTitle.focus();
}

function resetForm() {
  editingId = null;
  formTitle.textContent = '➕ 添加新歌曲';
  submitBtn.textContent = '保存歌曲';
  songForm.reset();
}

cancelBtn.addEventListener('click', resetForm);
adminSearch.addEventListener('input', renderAdminList);

// ── Submit (add or update) ────────────────────────────────────
songForm.addEventListener('submit', async e => {
  e.preventDefault();
  const body = {
    title: fieldTitle.value.trim(),
    category: fieldCategory.value,
    youtubeId: fieldYoutube.value.trim(),
    lyrics: fieldLyrics.value.trim(),
    noAds: fieldNoAds.checked
  };
  if (!body.title || !body.category || !body.lyrics) {
    showToast('请填写必填项', 'error');
    return;
  }

  try {
    if (editingId) {
      const res = await fetch(`/api/songs/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) throw new Error();
      showToast('✅ 歌曲已更新');
    } else {
      const res = await fetch('/api/songs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || res.status); }
      showToast('✅ 歌曲已添加');
    }
    resetForm();
    await loadSongs();
  } catch (e) {
    showToast(`❌ 保存失败：${e.message}`, 'error');
  }
});

// ── Delete ────────────────────────────────────────────────────
async function deleteSong(id) {
  const song = allSongs.find(s => s.id === id);
  if (!confirm(`确定要删除《${song?.title}》吗？`)) return;
  try {
    const res = await fetch(`/api/songs/${id}`, { method: 'DELETE' });
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || res.status); }
    showToast('🗑️ 歌曲已删除');
    await loadSongs();
  } catch (e) {
    showToast(`❌ 删除失败：${e.message}`, 'error');
  }
}

// ── Load ──────────────────────────────────────────────────────
async function loadSongs() {
  try {
    const res = await fetch('/api/songs');
    allSongs = await res.json();
    renderAdminList();
  } catch {
    adminSongList.innerHTML = '<p class="text-muted">无法加载歌曲列表</p>';
  }
}

loadSongs();
