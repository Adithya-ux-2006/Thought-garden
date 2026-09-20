from app.services.math_utils import extract_keywords, STOP_WORDS


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