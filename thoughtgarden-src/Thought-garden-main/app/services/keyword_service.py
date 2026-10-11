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


def suggest_tags(note, user_tags, related_notes):
    keywords = extract_keywords(note.title + ' ' + note.content, max_keywords=10)
    
    suggested = set()
    
    for kw in keywords:
        for tag in user_tags:
            if kw in tag.lower() or tag.lower() in kw:
                suggested.add(tag)
    
    for related in related_notes:
        for tag in related.tags:
            suggested.add(tag.name)
    
    existing_tag_names = {t.name for t in note.tags}
    suggested = [t for t in suggested if t not in existing_tag_names]
    
    return list(suggested)[:5]