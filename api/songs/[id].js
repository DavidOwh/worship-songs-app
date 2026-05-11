// Vercel Serverless Function — /api/songs/:id
// PUT: update a song
// DELETE: delete a song

const fs = require('fs');
const path = require('path');

const SONGS_FILE = path.join(process.cwd(), 'data', 'songs.json');

function readSongs() {
  return JSON.parse(fs.readFileSync(SONGS_FILE, 'utf-8'));
}

module.exports = function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { id } = req.query;

  if (req.method === 'GET') {
    try {
      const songs = readSongs();
      const song = songs.find(s => s.id === id);
      if (!song) return res.status(404).json({ error: 'Song not found' });
      return res.status(200).json(song);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to read songs' });
    }
  }

  if (req.method === 'PUT') {
    try {
      const songs = readSongs();
      const idx = songs.findIndex(s => s.id === id);
      if (idx === -1) return res.status(404).json({ error: 'Song not found' });
      songs[idx] = { ...songs[idx], ...req.body, id };
      fs.writeFileSync(SONGS_FILE, JSON.stringify(songs, null, 2), 'utf-8');
      return res.status(200).json(songs[idx]);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to update song' });
    }
  }

  if (req.method === 'DELETE') {
    try {
      const songs = readSongs();
      const idx = songs.findIndex(s => s.id === id);
      if (idx === -1) return res.status(404).json({ error: 'Song not found' });
      songs.splice(idx, 1);
      fs.writeFileSync(SONGS_FILE, JSON.stringify(songs, null, 2), 'utf-8');
      return res.status(200).json({ success: true });
    } catch (e) {
      return res.status(500).json({ error: 'Failed to delete song' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
