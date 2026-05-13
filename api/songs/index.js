// Vercel Serverless Function — /api/songs
// GET: return all songs
// POST: add a song (note: writes persist only until next deploy)

const fs = require('fs');
const path = require('path');

const SONGS_FILE = path.join(process.cwd(), 'data', 'songs.json');

function readSongs() {
  return JSON.parse(fs.readFileSync(SONGS_FILE, 'utf-8'));
}

module.exports = function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  if (req.method === 'GET') {
    try {
      const songs = readSongs();
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      return res.status(200).json(songs);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to read songs' });
    }
  }

  if (req.method === 'POST') {
    try {
      const songs = readSongs();
      const song = { id: Date.now().toString(), ...req.body, createdAt: new Date().toISOString() };
      songs.push(song);
      // Note: on Vercel this write is in-memory only; commit songs.json to git to persist
      fs.writeFileSync(SONGS_FILE, JSON.stringify(songs, null, 2), 'utf-8');
      return res.status(201).json(song);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to add song' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
