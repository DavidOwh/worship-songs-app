const fs = require('fs');
const path = require('path');
const https = require('https');

const SONGS_FILE = path.join(process.cwd(), 'data', 'songs.json');
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
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
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  if (req.method === 'GET') {
    try {
      const songs = JSON.parse(fs.readFileSync(SONGS_FILE, 'utf-8'));
      res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate');
      return res.status(200).json(songs);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to read songs' });
    }
  }

  if (req.method === 'POST') {
    try {
      const fileResult = await githubRequest('GET', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`);
      const sha = fileResult.body.sha;
      const songs = JSON.parse(Buffer.from(fileResult.body.content, 'base64').toString('utf-8'));

      const newSong = {
        id: String(Math.max(...songs.map(s => parseInt(s.id) || 0)) + 1),
        ...req.body,
        createdAt: new Date().toISOString()
      };
      songs.push(newSong);

      const updatedContent = Buffer.from(JSON.stringify(songs, null, 2)).toString('base64');
      await githubRequest('PUT', `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${GITHUB_FILE}`, {
        message: `Add song: ${newSong.title} (ID ${newSong.id})`,
        content: updatedContent,
        sha
      });

      return res.status(201).json(newSong);
    } catch (e) {
      return res.status(500).json({ error: 'Failed to add song' });
    }
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
