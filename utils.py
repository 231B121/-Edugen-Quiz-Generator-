"""
==============================================================================
EDUGEN - Text Processing & Natural Language Assessment Utilities
==============================================================================
This module provides the core data ingestion, sentence tokenization,
candidate answer mining, and multiple-choice distractor generation logic.
"""

import io
import re
import random
from typing import List, Tuple, Dict, Any, Optional, Set
from PyPDF2 import PdfReader

# ==============================================================================
# Filter Lists: Stopwords & Generic Sentence Starters
# Used to eliminate low-quality, trivial candidate answers
# ==============================================================================
STOPWORDS: Set[str] = {
    "the", "and", "is", "in", "to", "of", "a", "an", "for", "on", "with", "that", "this", "it",
    "as", "are", "was", "were", "by", "be", "or", "from", "at", "which", "has", "have", "had",
    "but", "not", "they", "their", "its", "he", "she", "you", "we", "i", "his", "her", "will",
    "can", "may", "also", "these", "those", "such", "there", "their", "then", "into", "more",
    "other", "some", "time", "than", "them", "very", "when", "what", "where", "who", "which",
    "how", "why", "each", "both", "all", "any", "over", "after", "before", "between", "under",
    "however", "although", "therefore", "furthermore", "moreover", "meanwhile", "since", "until",
    "about", "against", "among", "through", "during", "without", "within", "because", "while"
}

SENTENCE_STARTERS: Set[str] = {
    "The", "This", "That", "These", "Those", "There", "Here", "It", "They", "We", "You", "He",
    "She", "In", "On", "At", "For", "With", "As", "By", "From", "To", "However", "Therefore",
    "Moreover", "Furthermore", "Although", "Because", "Since", "While", "Meanwhile", "Today",
    "First", "Second", "Third", "Finally", "Next", "Then", "After", "Before", "Additionally"
}


def extract_text_from_pdf(file_storage: Any) -> Tuple[str, int]:
    """
    Extracts plain text cleanly from a PDF FileStorage object.
    
    Args:
        file_storage: A Werkzeug/Flask FileStorage object representing the uploaded PDF.
        
    Returns:
        Tuple[str, int]: A tuple of (cleaned_extracted_text, total_page_count).
        
    Raises:
        ValueError: If the PDF is empty, unreadable, or contains only scanned images.
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

    pages_text: List[str] = []
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


def clean_text(text: str) -> str:
    """
    Normalizes whitespace and removes unprintable characters while preserving sentence structure.
    
    Args:
        text: Raw input string from user input or PDF extraction.
        
    Returns:
        str: Cleaned and normalized text.
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


def split_into_sentences(text: str) -> List[str]:
    """
    Splits a body of text into distinct sentences using boundary lookahead rules.
    
    Args:
        text: Normalized input text.
        
    Returns:
        List[str]: Filtered list of meaningful sentences.
    """
    clean = re.sub(r'\s+', ' ', text).strip()
    # Split on sentence boundaries (. ! ?) followed by space and capital letter/number
    raw_sents = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', clean)
    sents: List[str] = []
    for s in raw_sents:
        s = s.strip()
        if len(s) >= 20 and not s.endswith(':'):
            sents.append(s)
    return sents


def compute_text_statistics(text: str) -> Dict[str, Any]:
    """
    Computes reading time and structural metrics for the input text.
    
    Args:
        text: Cleaned input text.
        
    Returns:
        Dict[str, Any]: Metrics dictionary including word count, character count, and estimated reading time.
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    # Standard adult silent reading speed: ~200 words per minute
    reading_time_mins = max(1, round(word_count / 200)) if word_count > 0 else 0

    return {
        "word_count": word_count,
        "char_count": char_count,
        "estimated_reading_minutes": reading_time_mins
    }


def extract_candidate_answers(text: str, max_candidates: int = 10) -> List[Dict[str, Any]]:
    """
    Extracts high-quality candidate answers from text:
    1. Explicit <hl>answer<hl> if provided by user
    2. Capitalized named entities and multi-word proper nouns
    3. Dates, years, and specific numerical quantities
    4. Salient domain keywords and noun phrases
    
    Args:
        text: Normalized input text.
        max_candidates: Maximum number of target answers to extract.
        
    Returns:
        List[Dict[str, Any]]: List of candidate dicts with answer, sentence, passage, and type.
    """
    candidates: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    def add_candidate(ans: str, sentence: str, passage: str, source_type: str) -> None:
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
            if len(nu) >= 2 and not nu.isdigit():
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
                m = re.search(r'\b' + re.escape(w) + r'\b', sent, re.IGNORECASE)
                if m:
                    add_candidate(m.group(0), sent, passage, "term")

    # Prioritize candidates: manual > named entities > years > terms
    priority = {"manual": 0, "named_entity": 1, "year": 2, "quantity": 3, "proper_noun": 4, "term": 5}
    candidates.sort(key=lambda x: (priority.get(x["source_type"], 9), -len(x["answer"])))

    # Distribute selections across sentences to avoid clustering in a single paragraph
    distributed: List[Dict[str, Any]] = []
    used_sentences: Set[str] = set()
    for c in candidates:
        if c["sentence"] not in used_sentences:
            distributed.append(c)
            used_sentences.add(c["sentence"])
            if len(distributed) >= max_candidates:
                break

    # Backfill with remaining candidates if needed
    if len(distributed) < max_candidates:
        for c in candidates:
            if c not in distributed:
                distributed.append(c)
                if len(distributed) >= max_candidates:
                    break

    return distributed


def generate_distractors(answer: str, all_candidate_answers: List[str], full_text: str) -> Tuple[List[str], int]:
    """
    Generates 3 plausible distractors for multiple choice options.
    
    Args:
        answer: The correct target answer.
        all_candidate_answers: Pool of other mined candidate answers.
        full_text: Entire context string.
        
    Returns:
        Tuple[List[str], int]: (shuffled_4_options_list, correct_option_index)
    """
    ans_clean = answer.strip()
    distractors: Set[str] = set()

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

    # 3. Pull from other candidate answers (filter out exact matches and substrings)
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

    # 4. Fallback plausible academic options if text pool is small
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