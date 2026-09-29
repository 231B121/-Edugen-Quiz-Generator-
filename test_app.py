"""
==============================================================================
Unit Test Suite for EDUGEN Utilities & Ingestion Pipelines
==============================================================================
Validates text normalization, sentence boundary detection, candidate answer
extraction, and multiple-choice distractor generation.
"""

import unittest
from utils import (
    clean_text,
    split_into_sentences,
    compute_text_statistics,
    extract_candidate_answers,
    generate_distractors,
)


class TestEdugenUtilities(unittest.TestCase):
    """Test cases for core text processing and NLP utilities."""

    def test_clean_text_normalizes_whitespace(self):
        raw = "Hello   world!\n\n\n\nThis is a    test."
        cleaned = clean_text(raw)
        self.assertNotIn("   ", cleaned)
        self.assertIn("Hello world!", cleaned)

    def test_clean_text_fixes_hyphenation(self):
        raw = "The trans-\nformer architecture was introduced."
        cleaned = clean_text(raw)
        self.assertIn("transformer", cleaned)

    def test_split_into_sentences_detects_boundaries(self):
        sample = "Python was released in 1991. It was designed by Guido van Rossum. It is widely used today."
        sents = split_into_sentences(sample)
        self.assertEqual(len(sents), 3)
        self.assertTrue(any("1991" in s for s in sents))

    def test_compute_text_statistics(self):
        text = "This is a simple sample text for testing word count and statistics."
        stats = compute_text_statistics(text)
        self.assertEqual(stats["word_count"], 12)
        self.assertGreater(stats["char_count"], 50)
        self.assertGreaterEqual(stats["estimated_reading_minutes"], 0)

    def test_extract_candidate_answers_prioritizes_entities_and_years(self):
        text = (
            "Alan Turing was an English mathematician. In 1936, he published a paper on computable numbers. "
            "He played a pivotal role in cracking coded messages during the Second World War."
        )
        candidates = extract_candidate_answers(text, max_candidates=5)
        self.assertTrue(len(candidates) > 0)
        answer_texts = [c["answer"] for c in candidates]
        self.assertTrue("Alan Turing" in answer_texts or "1936" in answer_texts)

    def test_generate_distractors_returns_four_options(self):
        answer = "1956"
        pool = ["Artificial Intelligence", "John McCarthy", "1956", "Dartmouth", "2017"]
        options, correct_idx = generate_distractors(answer, pool, "Sample text")
        self.assertEqual(len(options), 4)
        self.assertEqual(options[correct_idx], answer)
        self.assertEqual(len(set(options)), 4)  # All options must be unique


if __name__ == "__main__":
    unittest.main()
