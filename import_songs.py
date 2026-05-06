import sys, os, re, json, zipfile, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')

SONG_SHEET_DIR = r"C:\Users\owhwe\Dropbox\Second Brain Starter\02 Projects｜现行事工\WORSHIP MINISTRY\SONG SHEET"
OUTPUT_FILE = r"C:\Users\owhwe\Dropbox\Second Brain Starter\02 Projects｜现行事工\WORSHIP MINISTRY\worship-songs-app\data\songs.json"

def is_chord_line(line):
    stripped = line.strip()
    if not stripped:
        return False
    if any('一' <= c <= '鿿' for c in stripped):
        return False
    # Remove valid chord characters
    remaining = re.sub(r'[A-G][#b]?(?:maj|min|sus|add|dim|aug|m|M|7|9|11|13|2|4|6|\d)*(?:/[A-G][#b]?)?', '', stripped)
    remaining = remaining.replace(' ', '').replace('\t', '').replace('|', '').replace('-', '')
    return len(remaining) <= 3

def is_metadata_line(line):
    stripped = line.strip()
    return bool(re.search(r'\b(Key|key|bpm|BPM|4/4|3/4|6/8|12/8)\b', stripped))

def read_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            with z.open('word/document.xml') as f:
                tree = ET.parse(f)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                paragraphs = []
                for p in tree.findall('.//w:p', ns):
                    texts = [r.text for r in p.findall('.//w:t', ns) if r.text]
                    paragraphs.append(''.join(texts))
                return paragraphs
    except Exception as e:
        return []

def extract_title(filename):
    name = filename.replace('.docx', '').replace('.png', '')
    name = re.sub(r'^[A-Z]{2}\s+', '', name)           # strip leading 2-letter code
    name = re.sub(r'\s+[A-G][b#]?(?:-[A-G][b#]?)*\s*$', '', name)  # strip trailing key
    name = re.sub(r'\s*\([^)]+\)\s*$', '', name)       # strip (LOL) etc
    return name.strip()

SECTION_MAP = {
    'verse': '[诗段]', 'chorus': '[副歌]', 'bridge': '[桥段]',
    'pre-chorus': '[前副歌]', 'pre chorus': '[前副歌]',
    'tag': '[结尾]', 'outro': '[结尾]', 'intro': '[前奏]',
    'interlude': '[间奏]', 'hook': '[副歌]',
}

def extract_lyrics(paragraphs):
    lines = []
    first_key_done = False
    skip_rest = False

    for i, raw in enumerate(paragraphs):
        line = raw.strip()

        if skip_rest:
            break

        # Detect second key block → stop
        if is_metadata_line(line):
            if first_key_done:
                break
            first_key_done = True
            continue

        if not line:
            lines.append('')
            continue

        # Skip chord lines
        if is_chord_line(line):
            continue

        # Skip short non-Chinese lines near top (title, author, source)
        if i < 6 and len(line) < 25 and not any('一' <= c <= '鿿' for c in line):
            continue

        # Section labels
        low = line.lower()
        matched_section = None
        for key, label in SECTION_MAP.items():
            if re.match(r'^' + re.escape(key) + r'[\s\d]*$', low):
                matched_section = label
                break
        if matched_section:
            lines.append(matched_section)
            continue

        lines.append(line)

    # Clean up
    text = '\n'.join(lines).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

# Determine category from BPM or filename hints
def guess_category(paragraphs, filename):
    for line in paragraphs[:5]:
        m = re.search(r'(\d+)\s*bpm', line, re.IGNORECASE)
        if m:
            bpm = int(m.group(1))
            if bpm >= 100:
                return 'fast'
            elif bpm >= 76:
                return 'praise'
            else:
                return 'slow'
    return 'worship'

# Import all docx files
songs = []
errors = []

for filename in sorted(os.listdir(SONG_SHEET_DIR)):
    if not filename.endswith('.docx'):
        continue

    filepath = os.path.join(SONG_SHEET_DIR, filename)
    title = extract_title(filename)
    if not title:
        continue

    paragraphs = read_docx(filepath)
    if not paragraphs:
        errors.append(filename)
        continue

    lyrics = extract_lyrics(paragraphs)
    if len(lyrics) < 15:
        errors.append(f"{filename} (too short)")
        continue

    category = guess_category(paragraphs, filename)
    songs.append({
        "id": str(len(songs) + 1),
        "title": title,
        "lyrics": lyrics,
        "youtubeId": "",
        "category": category,
        "createdAt": "2026-01-01T00:00:00.000Z"
    })

print(f"✅ Imported {len(songs)} songs")
if errors:
    print(f"⚠️  Skipped {len(errors)}: {errors[:5]}")

# Preview first 3
for s in songs[:3]:
    print(f"\n--- {s['title']} ({s['category']}) ---")
    print(s['lyrics'][:200])

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)

print(f"\n💾 Saved to songs.json")
