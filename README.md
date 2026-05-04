# 敬拜歌曲 Worship Songs App

Cell group worship app with lyrics, chords, YouTube embeds, and WhatsApp setlist sharing.

---

## Pages

| URL | Who Uses It | Purpose |
|-----|-------------|---------|
| `/` | Members | View shared setlist, read lyrics, toggle chords |
| `/leader` | Worship leader | Browse songs, build setlist, share via WhatsApp |
| `/admin` | Pastor/admin | Add, edit, delete songs |

---

## Running Locally

```bash
cd worship-songs-app
npm install
npm run dev        # uses nodemon for auto-reload
# or
npm start          # plain node
```

App runs at `http://localhost:3000`

---

## Managing Songs

### Option A — Admin UI (local only)
Go to `http://localhost:3000/admin` to add/edit/delete songs via the web interface.

> ⚠️ **Important:** On Render's free tier the disk is ephemeral — changes made via the admin UI will be lost when the server restarts. For permanent changes, use Option B.

### Option B — Edit the JSON file directly (recommended for production)
Edit `data/songs.json` directly. Each song looks like this:

```json
{
  "id": "unique-id",
  "title": "歌曲名称",
  "lyrics": "[G]感谢你，[D]我的主\n[Em]你的恩典[C]何等大",
  "youtubeId": "dQw4w9WgXcQ",
  "category": "worship",
  "createdAt": "2026-01-01T00:00:00.000Z"
}
```

**Categories:** `praise` | `worship` | `slow` | `fast`

**Chord format:** Place chords in square brackets directly before the syllable they belong to:
```
[G]感谢你，[D]我的主
[Em]你的恩典[C]何等大
```

**YouTube ID:** The string after `v=` in a YouTube URL. For `youtube.com/watch?v=dQw4w9WgXcQ`, the ID is `dQw4w9WgXcQ`.

---

## Deploying to GitHub + Render

### Step 1 — Push to GitHub

```bash
cd worship-songs-app
git init
git add .
git commit -m "Initial commit: 敬拜歌曲 app"
```

Go to github.com → New repository → name it `worship-songs-app` → Create

```bash
git remote add origin https://github.com/YOUR_USERNAME/worship-songs-app.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Render

1. Go to [render.com](https://render.com) and sign in (free account is fine)
2. Click **New → Web Service**
3. Connect your GitHub account and select the `worship-songs-app` repository
4. Render auto-detects the settings from `render.yaml`
5. Click **Create Web Service**
6. Wait ~2 minutes for the first deploy
7. Your app URL will be something like `https://worship-songs-app.onrender.com`

### Step 3 — Update songs permanently

1. Edit `data/songs.json` locally
2. `git add data/songs.json && git commit -m "Update songs" && git push`
3. Render auto-redeploys in ~1 minute

---

## PWA — Installing on Phone

Members can install the app on their home screen:

- **Android (Chrome):** Open the app → tap the banner "安装应用" → Add to Home Screen
- **iPhone (Safari):** Open the app → tap Share button → "Add to Home Screen"

---

## How Setlist Sharing Works

1. Leader goes to `/leader`, selects 1–5 songs
2. Taps "📲 分享歌单 WhatsApp"
3. WhatsApp opens with a pre-written message containing the link, e.g.:
   `https://yourapp.onrender.com/?ids=1,2,3`
4. Members tap the link — app opens showing just those songs with full lyrics

No accounts, no login needed.

---

## Folder Structure

```
worship-songs-app/
├── data/
│   └── songs.json          ← song database (edit this to add songs)
├── public/
│   ├── css/style.css
│   ├── js/
│   │   ├── app.js          ← member view logic
│   │   ├── leader.js       ← leader setlist logic
│   │   └── admin.js        ← admin panel logic
│   ├── index.html          ← member view
│   ├── leader.html         ← leader view
│   ├── admin.html          ← admin panel
│   ├── manifest.json       ← PWA manifest
│   └── sw.js               ← service worker (offline support)
├── server.js               ← Express server + API
├── package.json
├── render.yaml             ← Render deployment config
└── README.md
```
