def filter_text_by_keywords(text, keywords):
    return [line for line in text.split('\n') if any(keyword in line for keyword in keywords)]