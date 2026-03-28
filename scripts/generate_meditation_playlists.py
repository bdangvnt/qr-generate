import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

QUERIES = [
    '(mediatype:audio) AND (title:("nhac thien" OR "khong loi" OR "thien nhac" OR ambient OR instrumental OR "meditation music" OR zen OR healing))',
    '(mediatype:audio) AND (subject:(meditation OR ambient OR instrumental OR zen OR mindfulness OR relaxation))',
    '(mediatype:audio) AND (title:(piano OR flute OR guitar OR "sound bath" OR "singing bowl")) AND (title:(meditation OR ambient OR instrumental))',
]

INCLUDE_RE = re.compile(
    r'(meditation|ambient|instrumental|thien|nhac thien|khong loi|vo loi|healing|relax|calm|zen|mindful|soundscape|singing bowl|piano|flute|guitar)',
    re.I,
)
EXCLUDE_RE = re.compile(
    r'(podcast|episode|radio|interview|news|talk show|politics|sports|sermon|lecture|class|homily|speech|audiobook|truyen|vocal|lyrics|karaoke)',
    re.I,
)

CATEGORY_KEYWORDS = {
    'lap_trinh_vien': [
        'focus',
        'deep',
        'ambient',
        'minimal',
        'concentration',
        'zen',
        'mindful',
        'flow',
        'instrumental',
        'coding',
        'calm',
    ],
    'ke_toan': ['steady', 'calm', 'piano', 'instrumental', 'classical', 'focus', 'clarity', 'relax'],
    'phap_che': ['clarity', 'solemn', 'minimal', 'contemplative', 'piano', 'strings', 'calm', 'focus', 'ambient'],
    'kinh_doanh': ['uplift', 'positive', 'energy', 'morning', 'light', 'motivation', 'focus', 'bright', 'flow'],
    'sang_tao': ['inspire', 'creative', 'flow', 'ambient', 'cinematic', 'guitar', 'flute', 'soundscape', 'zen'],
}

CATEGORY_CAPS = {
    'lap_trinh_vien': 32,
    'ke_toan': 30,
    'phap_che': 30,
    'kinh_doanh': 28,
    'sang_tao': 30,
}


def fetch_json(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8', errors='ignore'))


def score_for_category(track, words):
    blob = f"{track.get('title', '')} {track.get('creator', '')} {track.get('tags', '')}".lower()
    score = sum(2 for word in words if word in blob)
    duration_seconds = track.get('durationSeconds') or 0

    if 600 <= duration_seconds <= 2400:
        score += 2
    elif 180 <= duration_seconds < 600:
        score += 1

    if 'nhac' in blob or 'thien' in blob or 'meditation' in blob:
        score += 1

    return score


def pick_playable_track(identifier, fallback_doc):
    try:
        metadata = fetch_json(f"https://archive.org/metadata/{urllib.parse.quote(identifier)}", timeout=25)
    except Exception:
        return None

    files = metadata.get('files') or []
    md = metadata.get('metadata') or {}
    title = md.get('title') or fallback_doc.get('title') or identifier
    creator = md.get('creator') or fallback_doc.get('creator') or ''

    if isinstance(creator, list):
        creator = ' '.join(str(item) for item in creator)

    best = None
    for file_item in files:
        name = str(file_item.get('name', ''))
        if not name:
            continue

        lowered_name = name.lower()
        file_format = str(file_item.get('format', '')).lower()
        playable = (
            lowered_name.endswith('.mp3')
            or lowered_name.endswith('.m4a')
            or lowered_name.endswith('.ogg')
            or 'mp3' in file_format
            or 'm4a' in file_format
            or 'ogg' in file_format
            or 'vorbis' in file_format
        )
        if not playable:
            continue

        raw_duration = file_item.get('length') or file_item.get('duration') or file_item.get('runtime') or 0
        try:
            duration_seconds = float(raw_duration)
        except Exception:
            duration_seconds = 0

        if duration_seconds <= 0 or duration_seconds < 180 or duration_seconds > 4200:
            continue

        candidate = {
            'id': f"{identifier}:{name}",
            'identifier': identifier,
            'title': str(title),
            'creator': str(creator),
            'durationSeconds': int(round(duration_seconds)),
            'url': f"https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(name)}",
        }

        if best is None or candidate['durationSeconds'] > best['durationSeconds']:
            best = candidate

    if not best:
        return None

    blob = f"{best['title']} {best['creator']}".lower()
    if EXCLUDE_RE.search(blob):
        return None

    best['tags'] = blob
    return best


def collect_candidates():
    candidates = {}

    for query in QUERIES:
        params = urllib.parse.urlencode(
            [
                ('q', query),
                ('fl[]', 'identifier'),
                ('fl[]', 'title'),
                ('fl[]', 'creator'),
                ('fl[]', 'subject'),
                ('rows', '220'),
                ('page', '1'),
                ('output', 'json'),
            ]
        )
        url = f"https://archive.org/advancedsearch.php?{params}"
        data = fetch_json(url)
        docs = data.get('response', {}).get('docs', [])

        for doc in docs:
            identifier = doc.get('identifier')
            if not identifier:
                continue

            subject = doc.get('subject')
            if isinstance(subject, list):
                subject_text = ' '.join(str(item) for item in subject)
            else:
                subject_text = str(subject or '')

            blob = f"{doc.get('title', '')} {doc.get('creator', '')} {subject_text}".lower()
            if not INCLUDE_RE.search(blob):
                continue
            if EXCLUDE_RE.search(blob):
                continue

            candidates[identifier] = doc

    return candidates


def main():
    candidates = collect_candidates()
    candidate_ids = list(candidates.keys())

    tracks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_map = {
            executor.submit(pick_playable_track, identifier, candidates[identifier]): identifier
            for identifier in candidate_ids[:420]
        }
        for future in as_completed(future_map):
            track = future.result()
            if track:
                tracks.append(track)

    unique_tracks = []
    seen = set()
    for track in tracks:
        key = (track['url'].lower(), track['title'].strip().lower())
        if key in seen:
            continue
        seen.add(key)
        unique_tracks.append(track)

    for track in unique_tracks:
        best_category = None
        best_score = -1
        for category, words in CATEGORY_KEYWORDS.items():
            category_score = score_for_category(track, words)
            if category_score > best_score:
                best_score = category_score
                best_category = category
        track['category'] = best_category
        track['categoryScore'] = best_score

    unique_tracks.sort(key=lambda item: (item['categoryScore'], item['durationSeconds']), reverse=True)

    selected = []
    category_counts = {name: 0 for name in CATEGORY_CAPS}
    for track in unique_tracks:
        category = track['category']
        if category not in CATEGORY_CAPS:
            continue
        if category_counts[category] >= CATEGORY_CAPS[category]:
            continue
        selected.append(track)
        category_counts[category] += 1
        if len(selected) >= 150:
            break

    if len(selected) < 150:
        selected_ids = {track['id'] for track in selected}
        for track in unique_tracks:
            if track['id'] in selected_ids:
                continue
            selected.append(track)
            selected_ids.add(track['id'])
            if len(selected) >= 150:
                break

    selected = selected[:150]

    by_category = {name: [] for name in CATEGORY_CAPS}
    for track in selected:
        by_category.setdefault(track['category'], []).append(track)

    for category in by_category:
        by_category[category].sort(key=lambda item: (item['categoryScore'], item['durationSeconds']), reverse=True)

    output = {
        'generatedAt': int(time.time() * 1000),
        'source': 'archive.org',
        'totalCandidates': len(candidates),
        'playableUnique': len(unique_tracks),
        'totalTracks': len(selected),
        'categoryCounts': {name: len(items) for name, items in by_category.items()},
        'categories': {
            'lap_trinh_vien': {
                'label': 'Lap trinh vien - Deep focus',
                'description': 'Nen nhe, it vocal, giup tap trung code duong dai',
                'tracks': by_category.get('lap_trinh_vien', []),
            },
            'ke_toan': {
                'label': 'Ke toan - On dinh va chi tiet',
                'description': 'Tiet tau deu, giam met khi xu ly so lieu',
                'tracks': by_category.get('ke_toan', []),
            },
            'phap_che': {
                'label': 'Phap che - Tinh va ro',
                'description': 'Khong gian nhac nghiem, giu dau oc ro rang khi doc dieu khoan',
                'tracks': by_category.get('phap_che', []),
            },
            'kinh_doanh': {
                'label': 'Kinh doanh - Tich cuc va ben bi',
                'description': 'Nang luong vua du, khong gay xao nhang',
                'tracks': by_category.get('kinh_doanh', []),
            },
            'sang_tao': {
                'label': 'Sang tao - Mo rong y tuong',
                'description': 'Ambient/nhac cu nhe giup vao trang thai flow',
                'tracks': by_category.get('sang_tao', []),
            },
        },
    }

    with open('assets/meditation_job_playlists_150.json', 'w', encoding='utf-8') as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print('TOTAL_CANDIDATES', len(candidates))
    print('PLAYABLE_UNIQUE', len(unique_tracks))
    print('SELECTED', len(selected))
    print('COUNTS', json.dumps(output['categoryCounts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
