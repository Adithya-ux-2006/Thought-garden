import re
from collections import Counter


STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him',
    'us', 'them', 'what', 'which', 'who', 'whom', 'whose', 'where',
    'when', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'now', 'then', 'also', 'well', 'even'
}


def extract_keywords(text, max_keywords=5):
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in STOP_WORDS]
    
    freq = Counter(words)
    return [word for word, _ in freq.most_common(max_keywords)]


def suggest_tags(title, content, current_tags, user_tags, related_notes, limit=5):
    """Existing tag names worth adding to a note being written.

    Only ever suggests tags the user already has: first those matching the
    text's keywords (in keyword rank order), then tags carried by related
    notes (most common first). Tags already on the note are skipped
    case-insensitively.
    """
    keywords = extract_keywords(f'{title} {content}', max_keywords=10)
    taken = {t.casefold() for t in current_tags}
    suggested = []

    def _add(name):
        if name.casefold() not in taken:
            taken.add(name.casefold())
            suggested.append(name)

    for kw in keywords:
        for tag in user_tags:
            key = tag.casefold()
            # Very short tags ("AI") would match inside unrelated words.
            if kw in key or (len(key) >= 3 and key in kw):
                _add(tag)

    related_counts = Counter(t.name for note in related_notes for t in note.tags)
    for name, _ in sorted(related_counts.items(), key=lambda item: (-item[1], item[0].casefold())):
        _add(name)

    return suggested[:limit]