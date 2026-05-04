const express = require('express');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const SONGS_FILE = path.join(__dirname, 'data', 'songs.json');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

async function readSongs() {
  const data = await fs.readFile(SONGS_FILE, 'utf-8');
  return JSON.parse(data);
}

async function writeSongs(songs) {
  await fs.writeFile(SONGS_FILE, JSON.stringify(songs, null, 2), 'utf-8');
}

// Routes for clean URLs
app.get('/leader', (req, res) => res.sendFile(path.join(__dirname, 'public', 'leader.html')));
app.get('/admin', (req, res) => res.sendFile(path.join(__dirname, 'public', 'admin.html')));

// API: get all songs
app.get('/api/songs', async (req, res) => {
  try {
    const songs = await readSongs();
    res.json(songs);
  } catch {
    res.status(500).json({ error: 'Failed to read songs' });
  }
});

// API: add song
app.post('/api/songs', async (req, res) => {
  try {
    const songs = await readSongs();
    const song = { id: Date.now().toString(), ...req.body, createdAt: new Date().toISOString() };
    songs.push(song);
    await writeSongs(songs);
    res.status(201).json(song);
  } catch {
    res.status(500).json({ error: 'Failed to add song' });
  }
});

// API: update song
app.put('/api/songs/:id', async (req, res) => {
  try {
    const songs = await readSongs();
    const idx = songs.findIndex(s => s.id === req.params.id);
    if (idx === -1) return res.status(404).json({ error: 'Song not found' });
    songs[idx] = { ...songs[idx], ...req.body, id: req.params.id };
    await writeSongs(songs);
    res.json(songs[idx]);
  } catch {
    res.status(500).json({ error: 'Failed to update song' });
  }
});

// API: delete song
app.delete('/api/songs/:id', async (req, res) => {
  try {
    const songs = await readSongs();
    const idx = songs.findIndex(s => s.id === req.params.id);
    if (idx === -1) return res.status(404).json({ error: 'Song not found' });
    songs.splice(idx, 1);
    await writeSongs(songs);
    res.json({ success: true });
  } catch {
    res.status(500).json({ error: 'Failed to delete song' });
  }
});

app.listen(PORT, () => console.log(`敬拜歌曲 App running on port ${PORT}`));
