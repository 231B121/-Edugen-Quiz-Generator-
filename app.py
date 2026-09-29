from flask import Flask, render_template, request, jsonify
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import os
import re
import socket
import urllib3.util.connection as urllib3_cn

from utils import (
    extract_text_from_pdf,
    clean_text,
    extract_candidate_answers,
    generate_distractors,
)

# Force IPv4 to prevent network timeouts on systems where IPv6 is unreachable
def allowed_gai_family():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = allowed_gai_family

app = Flask(__name__)

MODEL_NAME = "valhalla/t5-small-qg-hl"

print("⏳ Loading AI model (valhalla/t5-small-qg-hl)... Please wait a moment...")

# Load tokenizer + model (use local cache first if available for instant startup)
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False, local_files_only=True)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, local_files_only=True)
except Exception:
    print("📥 Local cache not found. Downloading model from Hugging Face...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()
print(f"✅ Model loaded successfully on {device}!")


def generate_question_from_passage(passage_with_hl):
    """
    Passes passage containing <hl> answer <hl> through T5 QG model to generate a question.
    """
    prompt = f"generate question: {passage_with_hl}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)

    with torch.no_grad():
        out = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=64,
            num_beams=3,
            length_penalty=1.0,
            no_repeat_ngram_size=2,
            early_stopping=True,
            pad_token_id=tokenizer.pad_token_id if tokenizer.pad_token_id is not None else 0,
            eos_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id is not None else None,
        )

    q = tokenizer.decode(out[0], skip_special_tokens=True, clean_up_tokenization_spaces=True).strip()
    # Clean up artifacts
    q = q.replace("<hl>", "").strip()
    q = re.sub(r"^[\d\.\)\-\s]+", "", q).strip()
    if q and not q.endswith("?"):
        q += "?"
    if q:
        q = q[0].upper() + q[1:]
    return q


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/preview-pdf", methods=["POST"])
def preview_pdf():
    """
    Endpoint for fast PDF preview when user drops/selects a PDF.
    """
    pdf_file = request.files.get("pdf_file")
    if not pdf_file:
        return jsonify({"error": "No PDF file provided."}), 400
    try:
        extracted_text, page_count = extract_text_from_pdf(pdf_file)
        words = len(extracted_text.split())
        chars = len(extracted_text)
        preview_snippet = extracted_text[:350] + ("..." if chars > 350 else "")
        return jsonify({
            "success": True,
            "filename": pdf_file.filename,
            "page_count": page_count,
            "word_count": words,
            "char_count": chars,
            "preview": preview_snippet,
            "full_text": extracted_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/generate", methods=["POST"])
def generate():
    text_input = request.form.get("text_input", "") or ""
    try:
        num_q = max(1, min(15, int(request.form.get("num_questions", 5))))
    except Exception:
        num_q = 5

    difficulty = request.form.get("difficulty", "medium")
    source_desc = "Pasted Text"
    pdf_pages = 0

    pdf_file = request.files.get("pdf_file")
    if pdf_file and pdf_file.filename:
        try:
            pdf_text, pdf_pages = extract_text_from_pdf(pdf_file)
            text_input = (text_input + "\n\n" + pdf_text).strip()
            source_desc = f"PDF: {pdf_file.filename} ({pdf_pages} {'page' if pdf_pages == 1 else 'pages'})"
        except Exception as e:
            return jsonify({"error": f"PDF Error: {str(e)}"}), 400

    text_input = clean_text(text_input)
    if not text_input or len(text_input.strip()) < 20:
        return jsonify({
            "error": "Please provide more text (at least 2-3 sentences) or a readable PDF document."
        }), 400

    word_count = len(text_input.split())

    # Check if user provided manual <hl> tags
    has_manual_hl = "<hl>" in text_input.lower()

    # Extract candidate answers across the text
    # Request extra candidates so we have a strong pool
    candidates = extract_candidate_answers(text_input, max_candidates=max(12, num_q * 3))

    if not candidates:
        return jsonify({
            "error": "Could not identify sufficient concepts or key terms to generate questions. Please provide longer or more informative text."
        }), 400

    all_candidate_strings = [c["answer"] for c in candidates]
    generated_items = []
    seen_questions = set()

    for cand in candidates:
        ans = cand["answer"]
        passage = cand["passage"]

        # Insert <hl> tags around candidate answer in passage
        if "<hl>" in passage:
            passage_hl = passage
        else:
            pattern = re.compile(r'\b' + re.escape(ans) + r'\b', flags=re.IGNORECASE)
            passage_hl, n = pattern.subn(f"<hl> {ans} <hl>", passage, count=1)
            if n == 0:
                passage_hl = passage.replace(ans, f"<hl> {ans} <hl>", 1)

        try:
            q_text = generate_question_from_passage(passage_hl)
        except Exception as e:
            continue

        # Basic validity filter
        if not q_text or len(q_text) < 10 or q_text.lower() in seen_questions:
            continue

        seen_questions.add(q_text.lower())

        # Generate 4-option distractors
        options, correct_idx = generate_distractors(ans, all_candidate_strings, text_input)

        generated_items.append({
            "id": len(generated_items) + 1,
            "question": q_text,
            "answer": ans,
            "options": options,
            "correct_index": correct_idx,
            "context": cand["sentence"]
        })

        if len(generated_items) >= num_q:
            break

    if not generated_items:
        return jsonify({
            "error": "No questions could be synthesized from the text. Try highlighting specific terms with <hl>answer<hl> or providing more context."
        }), 500

    # Also provide questions list as plain strings for backwards compatibility
    plain_questions = [item["question"] for item in generated_items]

    return jsonify({
        "success": True,
        "questions": generated_items,
        "plain_questions": plain_questions,
        "meta": {
            "total_generated": len(generated_items),
            "word_count": word_count,
            "source": source_desc,
            "difficulty": difficulty
        }
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False)