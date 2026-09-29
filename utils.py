import io
import re
import random
from PyPDF2 import PdfReader

# Expanded stopword list to prevent picking trivial candidate answers
STOPWORDS = {
    "the", "and", "is", "in", "to", "of", "a", "an", "for", "on", "with", "that", "this", "it",
    "as", "are", "was", "were", "by", "be", "or", "from", "at", "which", "has", "have", "had",
    "but", "not", "they", "their", "its", "he", "she", "you", "we", "i", "his", "her", "will",
    "can", "may", "also", "these", "those", "such", "there", "their", "then", "into", "more",
    "other", "some", "time", "than", "them", "very", "when", "what", "where", "who", "which",
    "how", "why", "each", "both", "all", "any", "over", "after", "before", "between", "under",
    "however", "although", "therefore", "furthermore", "moreover", "meanwhile", "since", "until",
    "about", "against", "among", "through", "during", "without", "within", "because", "while"
}

SENTENCE_STARTERS = {
    "The", "This", "That", "These", "Those", "There", "Here", "It", "They", "We", "You", "He",
    "She", "In", "On", "At", "For", "With", "As", "By", "From", "To", "However", "Therefore",
    "Moreover", "Furthermore", "Although", "Because", "Since", "While", "Meanwhile", "Today",
    "First", "Second", "Third", "Finally", "Next", "Then", "After", "Before", "Additionally"
}

def extract_text_from_pdf(file_storage):
    """
    Extracts text cleanly from a PDF FileStorage object.
    Returns: (extracted_text, page_count)
    """
    try:
        file_storage.seek(0)
    except Exception:
        pass
        
    file_bytes = file_storage.read()
    if not file_bytes:
        raise ValueError("The uploaded PDF file is empty (0 bytes).")

    reader = PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    if page_count == 0:
        raise ValueError("The PDF contains no pages.")

    pages_text = []
    for idx, page in enumerate(reader.pages):
        try:
            pt = page.extract_text()
            if pt:
                # Remove header/footer line patterns like "Page 1 of 5" or standalone page numbers
                cleaned_p = re.sub(r'(?i)\bpage\s+\d+(\s+of\s+\d+)?\b', '', pt)
                pages_text.append(cleaned_p)
        except Exception:
            continue

    full_text = "\n\n".join(pages_text)
    full_text = clean_text(full_text)

    if not full_text or len(full_text.strip()) < 15:
        raise ValueError("No readable text found in the PDF. The file might contain scanned images or non-selectable text.")

    return full_text, page_count

def clean_text(text):
    """
    Normalizes whitespace and removes unprintable characters while preserving sentence structure.
    """
    if not text:
        return ""
    # Fix hyphenated line breaks e.g. "com-\nputer" -> "computer"
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    # Replace non-breaking spaces and tabs with normal spaces
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    # Normalize multiple newlines and spaces
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Keep printable ASCII and common unicode punctuation
    text = "".join(ch for ch in text if ch.isprintable() or ch in '\n\r')
    return text.strip()

def split_into_sentences(text):
    """
    Splits text into meaningful sentences.
    """
    # Clean up excess whitespace
    clean = re.sub(r'\s+', ' ', text).strip()
    # Split on sentence boundaries (. ! ?) followed by space and capital letter
    raw_sents = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', clean)
    sents = []
    for s in raw_sents:
        s = s.strip()
        if len(s) >= 20 and not s.endswith(':'):
            sents.append(s)
    return sents

def extract_candidate_answers(text, max_candidates=10):
    """
    Extracts high-quality candidate answers from text:
    1. Explicit <hl>answer<hl> if provided by user
    2. Capitalized named entities and multi-word proper nouns
    3. Dates, years, and specific numerical quantities
    4. Salient domain keywords and noun phrases
    """
    candidates = []
    seen = set()

    def add_candidate(ans, sentence, passage, source_type):
        norm = ans.strip().lower()
        if norm in seen or len(norm) <= 2 or norm in STOPWORDS:
            return
        if norm.isdigit() and len(norm) < 3:
            return
        seen.add(norm)
        candidates.append({
            "answer": ans.strip(),
            "sentence": sentence,
            "passage": passage,
            "source_type": source_type
        })

    # 1. Check for manual <hl> tags in user input
    manual_matches = re.findall(r'<hl>(.*?)</hl>|<hl>(.*?)<hl>', text, flags=re.IGNORECASE)
    for m in manual_matches:
        val = (m[0] or m[1] or "").strip()
        if val and val.lower() not in seen:
            add_candidate(val, text, text, "manual")

    sentences = split_into_sentences(text)
    if not sentences:
        # Fallback if sentence splitter yields nothing
        sentences = [text]

    # Process sentences and locate candidates
    for i, sent in enumerate(sentences):
        # Create passage window (current sentence + previous/next for context)
        prev_s = sentences[i - 1] if i > 0 else ""
        next_s = sentences[i + 1] if i < len(sentences) - 1 else ""
        
        # Passage window of approx 1-3 sentences
        passage_parts = [p for p in [prev_s, sent, next_s] if p]
        passage = " ".join(passage_parts)

        # A) Multi-word capitalized phrases (e.g., "Guido van Rossum", "Artificial Intelligence", "World War II")
        cap_phrases = re.findall(r'\b[A-Z][a-zA-Z]*(?:\s+(?:of\s+|the\s+|de\s+|van\s+)?[A-Z][a-zA-Z]*)+\b', sent)
        for cp in cap_phrases:
            cp_clean = re.sub(r'^(During\s+the|In\s+the|At\s+the|On\s+the|By\s+the|For\s+the|With\s+the|To\s+the)\s+', '', cp, flags=re.IGNORECASE).strip()
            words = cp_clean.split()
            if words[0] in SENTENCE_STARTERS and len(words) == 1:
                continue
            add_candidate(cp_clean, sent, passage, "named_entity")

        # B) Years (e.g. 1991, 2024, 1850) and specific quantities with units
        years = re.findall(r'\b(?:1[789]\d{2}|20\d{2})\b', sent)
        for y in years:
            add_candidate(y, sent, passage, "year")

        num_units = re.findall(r'\b\d+(?:\.\d+)?\s*(?:percent|%|million|billion|trillion|km|miles|meters|seconds|years|degrees)?\b', sent, flags=re.IGNORECASE)
        for nu in num_units:
            nu = nu.strip()
            if len(nu) >= 2 and not nu.isdigit(): # Has units or decimals
                add_candidate(nu, sent, passage, "quantity")

        # C) Single Capitalized Proper Nouns (e.g., "Python", "Google", "Einstein", "Paris")
        single_caps = re.findall(r'\b[A-Z][a-zA-Z]{3,}\b', sent)
        for sc in single_caps:
            if sc not in SENTENCE_STARTERS and sc.lower() not in STOPWORDS:
                add_candidate(sc, sent, passage, "proper_noun")

        # D) Key technical / informative words
        words = re.findall(r'\b[a-z]{4,}\b', sent.lower())
        for w in words:
            if w not in STOPWORDS:
                # Only add if it appears as an exact whole word in original sentence
                m = re.search(r'\b' + re.escape(w) + r'\b', sent, re.IGNORECASE)
                if m:
                    add_candidate(m.group(0), sent, passage, "term")

    # Sort & prioritize diverse candidates: manual > named entities > years > terms
    priority = {"manual": 0, "named_entity": 1, "year": 2, "quantity": 3, "proper_noun": 4, "term": 5}
    candidates.sort(key=lambda x: (priority.get(x["source_type"], 9), -len(x["answer"])))

    # Distribute selections across sentences to avoid crowding one paragraph
    distributed = []
    used_sentences = set()
    for c in candidates:
        if c["sentence"] not in used_sentences:
            distributed.append(c)
            used_sentences.add(c["sentence"])
            if len(distributed) >= max_candidates:
                break

    # If we still need more candidates, backfill with remaining
    if len(distributed) < max_candidates:
        for c in candidates:
            if c not in distributed:
                distributed.append(c)
                if len(distributed) >= max_candidates:
                    break

    return distributed

def generate_distractors(answer, all_candidate_answers, full_text):
    """
    Generates 3 plausible distractors for multiple choice options.
    Returns: (options_list, correct_option_index)
    """
    ans_clean = answer.strip()
    distractors = set()

    # 1. Four-digit year logic
    if re.fullmatch(r'\b(1[789]\d{2}|20\d{2})\b', ans_clean):
        val = int(ans_clean)
        offsets = [-12, -8, -5, -3, 3, 5, 8, 12, 15]
        random.shuffle(offsets)
        for off in offsets:
            d = str(val + off)
            if d != ans_clean:
                distractors.add(d)
            if len(distractors) >= 3:
                break

    # 2. General numbers logic
    elif ans_clean.isdigit():
        val = int(ans_clean)
        offsets = [-10, -5, -2, -1, 1, 2, 5, 10, 20]
        random.shuffle(offsets)
        for off in offsets:
            d = str(max(1, val + off))
            if d != ans_clean:
                distractors.add(d)
            if len(distractors) >= 3:
                break

    # 3. Pull from other candidate answers of similar style/length
    if len(distractors) < 3:
        pool = [
            c for c in all_candidate_answers 
            if c.strip().lower() != ans_clean.lower() 
            and len(c.strip()) >= 2
            and c.strip().lower() not in ans_clean.lower()
            and ans_clean.lower() not in c.strip().lower()
        ]
        random.shuffle(pool)
        for c in pool:
            if c not in distractors and c.lower() != ans_clean.lower():
                distractors.add(c)
            if len(distractors) >= 3:
                break

    # 4. Fallback plausible options if text pool is too small
    fallbacks = [
        "None of the mentioned",
        "All of the above",
        "Data not specified",
        "Secondary factor",
        "Alternative principle"
    ]
    random.shuffle(fallbacks)
    for fb in fallbacks:
        if len(distractors) >= 3:
            break
        if fb.lower() != ans_clean.lower():
            distractors.add(fb)

    options = list(distractors)[:3] + [ans_clean]
    random.shuffle(options)
    correct_idx = options.index(ans_clean)

    return options, correct_idx