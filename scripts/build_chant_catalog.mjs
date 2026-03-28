import { writeFile } from 'node:fs/promises';

const TARGET = 140;
const MAX_DOCS = 320;
const CONCURRENCY = 10;

function blobOf(doc) {
  const subject = Array.isArray(doc.subject) ? doc.subject.join(' ') : (doc.subject || '');
  return `${doc.title || ''} ${doc.creator || ''} ${subject}`.toLowerCase();
}

function likelyChant(doc) {
  const blob = blobOf(doc);
  const include = /(chant|sutra|mantra|buddh|zen|meditation|namo|om|tham|kinh|phat|mindful|amitabha|avalokiteshvara)/i;
  const exclude = /(podcast|episode|radio|interview|news|politics|sports|talk show)/i;
  return include.test(blob) && !exclude.test(blob);
}

function encodeArchiveSegment(pathPart) {
  return String(pathPart || '')
    .split('/')
    .map((p) => encodeURIComponent(p))
    .join('/');
}

async function mapWithConcurrency(items, mapper, concurrency = 8) {
  const out = [];
  let index = 0;

  async function worker() {
    while (index < items.length) {
      const local = index;
      index += 1;
      out[local] = await mapper(items[local], local);
    }
  }

  await Promise.all(Array.from({ length: concurrency }, () => worker()));
  return out;
}

function trackScore(track) {
  const text = `${track.title} ${track.creator} ${track.tags}`.toLowerCase();
  let score = 0;
  const add = (words, weight) => {
    for (const w of words) {
      if (text.includes(w)) score += weight;
    }
  };

  add(['chant', 'sutra', 'mantra', 'namo', 'om', 'buddh', 'zen'], 3);
  add(['calm', 'peace', 'mindful', 'meditation', 'healing'], 2);
  add(['focus', 'clarity', 'balance', 'gentle', 'light'], 1);
  add(['podcast', 'episode', 'news', 'interview'], -4);
  return score;
}

function parseDurationSeconds(file) {
  const candidates = [file.length, file.duration, file.runtime];
  for (const value of candidates) {
    const seconds = Number.parseFloat(value);
    if (Number.isFinite(seconds) && seconds > 0) {
      return Math.round(seconds);
    }
  }
  return null;
}

async function main() {
  const params = new URLSearchParams();
  params.set('q', '(mediatype:audio) AND (title:(chant OR chanting OR sutra OR mantra OR buddhist OR zen OR meditation OR namo OR om OR amitabha OR mindfulness))');
  params.append('fl[]', 'identifier');
  params.append('fl[]', 'title');
  params.append('fl[]', 'creator');
  params.append('fl[]', 'subject');
  params.set('rows', String(MAX_DOCS));
  params.set('page', '1');
  params.set('output', 'json');

  const searchRes = await fetch(`https://archive.org/advancedsearch.php?${params.toString()}`);
  if (!searchRes.ok) {
    throw new Error(`Search failed with status ${searchRes.status}`);
  }

  const searchData = await searchRes.json();
  const docsRaw = searchData?.response?.docs || [];
  const preferred = docsRaw.filter(likelyChant);
  const docs = (preferred.length >= TARGET ? preferred : docsRaw).slice(0, MAX_DOCS);

  const mapped = await mapWithConcurrency(
    docs,
    async (doc) => {
      try {
        const metaRes = await fetch(`https://archive.org/metadata/${encodeArchiveSegment(doc.identifier)}`);
        if (!metaRes.ok) return null;

        const meta = await metaRes.json();
        const files = Array.isArray(meta.files) ? meta.files : [];
        const playable = files.find((file) => {
          if (file.private) return false;
          const format = String(file.format || '').toLowerCase();
          const name = String(file.name || '').toLowerCase();
          return (
            format.includes('mp3') ||
            format.includes('ogg') ||
            format.includes('m4a') ||
            name.endsWith('.mp3') ||
            name.endsWith('.ogg') ||
            name.endsWith('.m4a')
          );
        });

        if (!playable || !playable.name) return null;

        return {
          id: `${doc.identifier}:${playable.name}`,
          title: doc.title || doc.identifier,
          creator: doc.creator || '',
          tags: blobOf(doc),
          durationSeconds: parseDurationSeconds(playable),
          url: `https://archive.org/download/${encodeArchiveSegment(doc.identifier)}/${encodeArchiveSegment(playable.name)}`
        };
      } catch {
        return null;
      }
    },
    CONCURRENCY
  );

  const seen = new Set();
  const unique = [];
  for (const item of mapped) {
    if (!item || seen.has(item.url)) continue;
    seen.add(item.url);
    unique.push(item);
  }

  unique.sort((a, b) => trackScore(b) - trackScore(a));
  const tracks = unique.slice(0, TARGET);

  const output = {
    generatedAt: new Date().toISOString(),
    source: 'archive.org',
    trackCount: tracks.length,
    tracks
  };

  await writeFile('assets/chant_catalog.json', JSON.stringify(output, null, 2));
  console.log(`Wrote assets/chant_catalog.json with ${tracks.length} tracks.`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
