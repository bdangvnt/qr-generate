import json
import re
import time
import urllib.parse
import urllib.request

QUERIES = [
    '(mediatype:audio) AND (title:("nhac thien" OR "khong loi" OR "thien nhac" OR ambient OR instrumental OR "meditation music" OR zen OR healing))',
    '(mediatype:audio) AND (subject:(meditation OR ambient OR instrumental OR zen OR mindfulness OR relaxation))',
    '(mediatype:audio) AND (title:(piano OR flute OR guitar OR "sound bath" OR "singing bowl")) AND (title:(meditation OR ambient OR instrumental))',
    '(mediatype:audio) AND (title:("new age" OR "background music" OR "relaxing music"))',
]

INCLUDE_RE = re.compile(
    r'(meditation|ambient|instrumental|thien|nhac thien|khong loi|vo loi|healing|relax|calm|zen|mindful|soundscape|singing bowl|piano|flute|guitar|new age|background)',
    re.I,
)
EXCLUDE_RE = re.compile(
    r'(podcast|episode|radio|interview|news|talk show|politics|sports|sermon|lecture|class|homily|speech|audiobook|truyen|karaoke)',
    re.I,
)

CATEGORY_KEYWORDS = {
    'lap_trinh_vien': ['focus', 'deep', 'ambient', 'minimal', 'concentration', 'zen', 'mindful', 'flow', 'instrumental', 'calm'],
    'ke_toan': ['steady', 'calm', 'piano', 'instrumental', 'classical', 'focus', 'clarity', 'relax'],
    'phap_che': ['clarity', 'solemn', 'minimal', 'contemplative', 'piano', 'strings', 'calm', 'focus', 'ambient'],
    'kinh_doanh': ['uplift', 'positive', 'energy', 'morning', 'light', 'motivation', 'focus', 'bright', 'flow'],
    'sang_tao': ['inspire', 'creative', 'flow', 'ambient', 'cinematic', 'guitar', 'flute', 'soundscape', 'zen'],
}

CATEGORY_CAPS = {
    'lap_trinh_vien': 30,
    'ke_toan': 30,
    'phap_che': 30,
    'kinh_doanh': 30,
    'sang_tao': 30,
}


def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8', errors='ignore'))


def to_text(value):
    if value is None:
        return ''
    if isinstance(value, list):
        return ' '.join(str(item) for item in value)
    return str(value)


def score_for_category(item, words):
    blob = f"{item.get('title', '')} {item.get('creator', '')} {item.get('tags', '')}".lower()
    score = sum(2 for word in words if word in blob)
    if 'nhac' in blob or 'thien' in blob or 'meditation' in blob:
        score += 1
    return score


def collect_items():
    items = {}
    for query in QUERIES:
        params = urllib.parse.urlencode(
            [
                ('q', query),
                ('fl[]', 'identifier'),
                ('fl[]', 'title'),
                ('fl[]', 'creator'),
                ('fl[]', 'subject'),
                ('fl[]', 'description'),
                ('rows', '350'),
                ('page', '1'),
                ('output', 'json'),
            ]
        )
        url = f'https://archive.org/advancedsearch.php?{params}'
        data = fetch_json(url)

        for doc in data.get('response', {}).get('docs', []):
            identifier = doc.get('identifier')
            if not identifier:
                continue

            title = to_text(doc.get('title')).strip()
            creator = to_text(doc.get('creator')).strip()
            subject = to_text(doc.get('subject')).strip()
            description = to_text(doc.get('description')).strip()
            blob = f"{title} {creator} {subject} {description}".lower()

            if not INCLUDE_RE.search(blob):
                continue
            if EXCLUDE_RE.search(blob):
                continue

            item = {
                'id': identifier,
                'identifier': identifier,
                'title': title or identifier,
                'creator': creator,
                'tags': blob,
                'url': f'https://archive.org/details/{urllib.parse.quote(identifier)}',
            }
            items[identifier] = item

    return list(items.values())


def main():
    items = collect_items()

    for item in items:
        best_category = None
        best_score = -1
        for category, words in CATEGORY_KEYWORDS.items():
            category_score = score_for_category(item, words)
            if category_score > best_score:
                best_score = category_score
                best_category = category
        item['category'] = best_category
        item['categoryScore'] = best_score

    items.sort(key=lambda row: (row['categoryScore'], len(row.get('title', ''))), reverse=True)

    ranked_by_category = {}
    for category, words in CATEGORY_KEYWORDS.items():
        ranked = []
        for item in items:
            ranked.append((score_for_category(item, words), item))
        ranked.sort(key=lambda row: (row[0], len(row[1].get('title', ''))), reverse=True)
        ranked_by_category[category] = ranked

    selected = []
    selected_ids = set()

    for category, cap in CATEGORY_CAPS.items():
        count = 0
        for score, item in ranked_by_category.get(category, []):
            if count >= cap:
                break
            if item['id'] in selected_ids:
                continue
            picked = dict(item)
            picked['category'] = category
            picked['categoryScore'] = score
            selected.append(picked)
            selected_ids.add(item['id'])
            count += 1

    if len(selected) < 150:
        for item in items:
            if item['id'] in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(item['id'])
            if len(selected) >= 150:
                break

    selected = selected[:150]

    grouped = {name: [] for name in CATEGORY_CAPS}
    for item in selected:
        grouped.setdefault(item['category'], []).append(item)

    for category in grouped:
        grouped[category].sort(key=lambda row: (row['categoryScore'], row['title']), reverse=True)

    output = {
        'generatedAt': int(time.time() * 1000),
        'source': 'archive.org',
        'totalCandidates': len(items),
        'totalTracks': len(selected),
        'categoryCounts': {name: len(rows) for name, rows in grouped.items()},
        'categories': {
            'lap_trinh_vien': {
                'label': 'Lap trinh vien - Deep focus',
                'description': 'Nen nhe, it vocal, giup tap trung code duong dai',
                'tracks': grouped.get('lap_trinh_vien', []),
            },
            'ke_toan': {
                'label': 'Ke toan - On dinh va chi tiet',
                'description': 'Tiet tau deu, giam met khi xu ly so lieu',
                'tracks': grouped.get('ke_toan', []),
            },
            'phap_che': {
                'label': 'Phap che - Tinh va ro',
                'description': 'Khong gian nhac nghiem, giu dau oc ro rang khi doc dieu khoan',
                'tracks': grouped.get('phap_che', []),
            },
            'kinh_doanh': {
                'label': 'Kinh doanh - Tich cuc va ben bi',
                'description': 'Nang luong vua du, khong gay xao nhang',
                'tracks': grouped.get('kinh_doanh', []),
            },
            'sang_tao': {
                'label': 'Sang tao - Mo rong y tuong',
                'description': 'Ambient/nhac cu nhe giup vao trang thai flow',
                'tracks': grouped.get('sang_tao', []),
            },
        },
    }

    with open('assets/meditation_job_collections_150.json', 'w', encoding='utf-8') as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print('TOTAL_CANDIDATES', len(items))
    print('SELECTED', len(selected))
    print('COUNTS', json.dumps(output['categoryCounts'], ensure_ascii=False))


if __name__ == '__main__':
    main()
