// Vercel Serverless Function — /api/songs/:id
// PUT: update a song   DELETE: delete a song
// Writes persist via GitHub API (Vercel filesystem is read-only)

const fs = require('fs');
const path = require('path');
const https = require('https');

const SONGS_FILE = path.join(process.cwd(), 'data', 'songs.json');
const GITHUB_TOKEN = (process.env.GITHUB_TOKEN || '').trim();
const GITHUB_OWNER = 'DavidOwh';
const GITHUB_REPO = 'worship-songs-app';
const GITHUB_FILE = 'data/songs.json';

function githubRequest(method, urlPath, body) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: urlPath,
      method,
      headers: {
        'Authorization': `token ${GITHUB_TOKEN}`,
        'User-Agent': 'worship-songs-app',
        'Content-Type': 'application/json',
        'Accept': 'application/vnd.github.v3+json'
      }
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { id } = req.query;

  if (req.method === 'GET') {
    try {
      const songs = JSON.parse(fs.readFileSync(SONGS_FILE, 'utf-8'));
      const song = songs.find(s => s.id === id);
      if (!song) return res.status(404).json({ error: 'Song not found' });
      return res.status(200).json(song);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to read songs' });
    }
  }

  if (req.method === 'PUT') {
    try {
      const fileResult = await githubRequest('GET', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`);
      const sha = fileResult.body.sha;
      const songs = JSON.parse(Buffer.from(fileResult.body.content, 'base64').toString('utf-8'));
      const idx = songs.findIndex(s => s.id === id);
      if (idx === -1) return res.status(404).json({ error: 'Song not found' });
      songs[idx] = { ...songs[idx], ...req.body, id };
      const updatedContent = Buffer.from(JSON.stringify(songs, null, 2)).toString('base64');
      await githubRequest('PUT', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`, {
        message: `Update song: ${songs[idx].title} (ID ${id})`,
        content: updatedContent,
        sha
      });
      return res.status(200).json(songs[idx]);
    } catch (e) {
      return res.status(500).json({ error: e.message });
    }
  }

  if (req.method === 'DELETE') {
    try {
      const fileResult = await githubRequest('GET', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`);
      const sha = fileResult.body.sha;
      const songs = JSON.parse(Buffer.from(fileResult.body.content, 'base64').toString('utf-8'));
      const idx = songs.findIndex(s => s.id === id);
      if (idx === -1) return res.status(404).json({ error: 'Song not found' });
      const title = songs[idx].title;
      songs.splice(idx, 1);
      const updatedContent = Buffer.from(JSON.stringify(songs, null, 2)).toString('base64');
      await githubRequest('PUT', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`, {
        message: `Delete song: ${title} (ID ${id})`,
        content: updatedContent,
        sha
      });
      return res.status(200).json({ success: true });
    } catch (e) {
      return res.status(500).json({ error: e.message });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
