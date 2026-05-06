import sys, os, re, json, openpyxl
sys.stdout.reconfigure(encoding='utf-8')

EXCEL_FILE = r"C:\Users\owhwe\Downloads\-SONG LIST COOS Chinese.xlsx"
SONGS_JSON = r"C:\Users\owhwe\Dropbox\Second Brain Starter\02 Projects｜现行事工\WORSHIP MINISTRY\worship-songs-app\data\songs.json"

# ── helpers ─────────────────────────────────────────────────────────────────

def extract_youtube_id(raw):
    """Extract YouTube ID from URL strings (including IFERROR formulas)."""
    if not raw:
        return ""
    s = str(raw).strip()
    # pull URL out of IFERROR formula
    m = re.search(r'https?://[^\s"\']+', s)
    url = m.group(0) if m else s
    # youtu.be/ID
    m = re.search(r'youtu\.be/([A-Za-z0-9_-]{11})', url)
    if m:
        return m.group(1)
    # youtube.com/watch?v=ID
    m = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', url)
    if m:
        return m.group(1)
    # youtube.com/embed/ID
    m = re.search(r'embed/([A-Za-z0-9_-]{11})', url)
    if m:
        return m.group(1)
    return ""

def clean_title(raw):
    """Strip 2-letter prefix and trailing key from title."""
    name = str(raw).strip()
    name = re.sub(r'^[A-Z]{2}\s+', '', name)                      # strip leading 2-letter code
    name = re.sub(r'\s+[A-G][b#]?(?:-[A-G][b#]?)*\s*$', '', name)  # strip trailing key
    name = re.sub(r'\s*\([^)]*\)\s*$', '', name)                   # strip trailing (...)
    return name.strip()

def bpm_category(bpm_raw):
    try:
        bpm = int(float(str(bpm_raw).strip()))
        if bpm >= 100:
            return 'fast'
        elif bpm >= 76:
            return 'praise'
        else:
            return 'slow'
    except Exception:
        return 'worship'

def normalize(title):
    """Normalize title for fuzzy matching."""
    return re.sub(r'[\s\-_·•]+', '', title).lower()

# ── load existing songs ──────────────────────────────────────────────────────

with open(SONGS_JSON, encoding='utf-8') as f:
    existing = json.load(f)

existing_by_norm = {normalize(s['title']): s for s in existing}
print(f"Existing songs: {len(existing)}")

# ── parse Excel ──────────────────────────────────────────────────────────────

wb = openpyxl.load_workbook(EXCEL_FILE, data_only=True)

# Full List sheet
sheet = wb['Full List']
rows = list(sheet.iter_rows(values_only=True))
header = rows[0]
print(f"Full List header: {header[:10]}")

full_list = []
for row in rows[1:]:
    if not row[0]:
        continue
    raw_title = str(row[0]).strip()
    if not raw_title or raw_title.lower() == 'song title':
        continue
    title = clean_title(raw_title)
    if not title:
        continue

    bpm_val = row[3] if len(row) > 3 else None
    yt_ref1 = row[7] if len(row) > 7 else None
    yt_ref2 = row[8] if len(row) > 8 else None

    yt_id = extract_youtube_id(yt_ref1) or extract_youtube_id(yt_ref2)
    category = bpm_category(bpm_val)

    full_list.append({'title': title, 'youtubeId': yt_id, 'category': category})

print(f"Full List parsed: {len(full_list)}")

# Dialect sheet
dialect_sheet = wb['Dialect']
d_rows = list(dialect_sheet.iter_rows(values_only=True))
d_header = d_rows[0]
print(f"Dialect header: {d_header[:10]}")

dialect_list = []
for row in d_rows[1:]:
    if not row[0]:
        continue
    raw_title = str(row[0]).strip()
    if not raw_title or raw_title.lower() == 'song title':
        continue
    title = clean_title(raw_title)
    if not title:
        continue

    # Dialect: col 0=title, 1=type, 2=key, 3=bpm, 4=time, 5=artist, 6=original, 7=ref1, 8=ref2
    yt_ref1 = row[7] if len(row) > 7 else None
    yt_ref2 = row[8] if len(row) > 8 else None
    yt_id = extract_youtube_id(yt_ref1) or extract_youtube_id(yt_ref2)

    dialect_list.append({'title': title, 'youtubeId': yt_id, 'category': 'dialect'})

print(f"Dialect parsed: {len(dialect_list)}")

# ── merge into existing ──────────────────────────────────────────────────────

# Step 1: update existing songs from Full List
updated = 0
for item in full_list:
    key = normalize(item['title'])
    if key in existing_by_norm:
        song = existing_by_norm[key]
        if item['youtubeId'] and not song.get('youtubeId'):
            song['youtubeId'] = item['youtubeId']
            updated += 1
        # update category from BPM if we have BPM data
        if item['category'] != 'worship':  # 'worship' = no BPM found
            song['category'] = item['category']

print(f"Updated {updated} existing songs with new YouTube IDs")

# Step 2: add new songs from Full List not in existing
# We keep existing songs' lyrics — only add songs with no match
added_mandarin = 0
max_id = max(int(s['id']) for s in existing)

for item in full_list:
    key = normalize(item['title'])
    if key not in existing_by_norm:
        max_id += 1
        new_song = {
            "id": str(max_id),
            "title": item['title'],
            "lyrics": "",
            "youtubeId": item['youtubeId'],
            "category": item['category'],
            "createdAt": "2026-01-01T00:00:00.000Z"
        }
        existing.append(new_song)
        existing_by_norm[key] = new_song
        added_mandarin += 1

print(f"Added {added_mandarin} new mandarin songs from Full List")

# Step 3: add dialect songs
added_dialect = 0
for item in dialect_list:
    key = normalize(item['title'])
    if key not in existing_by_norm:
        max_id += 1
        new_song = {
            "id": str(max_id),
            "title": item['title'],
            "lyrics": "",
            "youtubeId": item['youtubeId'],
            "category": "dialect",
            "createdAt": "2026-01-01T00:00:00.000Z"
        }
        existing.append(new_song)
        existing_by_norm[key] = new_song
        added_dialect += 1
    else:
        # Update category to dialect
        existing_by_norm[key]['category'] = 'dialect'

print(f"Added {added_dialect} new dialect songs")

# ── save ────────────────────────────────────────────────────────────────────

with open(SONGS_JSON, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"\nTotal songs now: {len(existing)}")
print(f"Done! Saved to songs.json")
