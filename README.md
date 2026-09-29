# EDUGEN · AI-Powered Quiz & Question Generator 🎓

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Framework](https://img.shields.io/badge/Framework-Flask-black?logo=flask)
![NLP](https://img.shields.io/badge/NLP-HuggingFace%20Transformers-orange?logo=huggingface)
![Model](https://img.shields.io/badge/Model-T5--small--qg--hl-green)
![License](https://img.shields.io/badge/License-MIT-purple)

**EDUGEN** is an intelligent academic question and quiz generation platform powered by Deep Learning and Natural Language Processing (NLP). It automatically transforms raw text, textbook chapters, lecture notes, and multi-page PDF documents into comprehensive, answer-aware quizzes and multiple-choice questions (MCQs).

Designed with a formal, professional academic interface for educators, researchers, and students.

---

## 📌 Table of Contents
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start Guide](#-quick-start-guide)
- [API Reference](#-api-reference)
- [Export & Quiz Modes](#-export--quiz-modes)
- [Author](#-author)
- [License](#-license)

---

## ✨ Key Features

* **Full-Document Text & PDF Processing:** Extracts text cleanly from multi-page PDFs, removes headers/footers, and distributes questions across the entire document.
* **Answer-Aware Question Generation (T5 Transformer):** Leverages `valhalla/t5-small-qg-hl` sequence-to-sequence model to synthesize contextually accurate questions.
* **Intelligent Entity & Concept Detection:** Automatically detects named entities, dates, years, numerical quantities, and core definitions without relying on naive word frequency.
* **Automatic 4-Option Multiple Choice Questions (MCQs):** Crafts plausible, context-aware distractors for every question to form realistic assessments.
* **🎮 Interactive Quiz & Practice Mode:** Take quizzes directly inside the web browser with instant self-evaluation, scorecard calculations, and green/red answer highlighting.
* **Targeted Questions (Highlight Tool):** Select any specific phrase and click *"Highlight Selection as Answer"* to force question generation around that exact keyword (`<hl>keyword<hl>`).
* **Instant PDF Text Preview:** Drag and drop any PDF to immediately view page count, word count, file size, and a live scrollable text excerpt.
* **Formal, Distraction-Free Academic UI:** Crisp light-mode institutional aesthetic with clean typography, no excessive scanning animations, and fast response times.
* **Comprehensive Export Options:** One-click exports to formatted Markdown/Word, downloadable JSON, and clean printable PDF worksheets with answer keys.

---

## 🔬 How It Works

```
                                      [User Input]
                                   (Text or PDF File)
                                           │
                                           ▼
                                 [Document Preprocessor]
                         (Extract pages, clean whitespace, segment)
                                           │
                                           ▼
                                [Candidate Answer Miner]
                    (Named entities, historical dates, key domain terms)
                                           │
                                           ▼
                                [Passage Window Extractor]
                       (Local context window + <hl> answer <hl>)
                                           │
                                           ▼
                             [T5 Question Generation Engine]
                               (valhalla/t5-small-qg-hl)
                                           │
                                           ▼
                               [Distractor Synthesizer]
                           (4-option MCQ options & answers)
                                           │
                                           ▼
                                  [EDUGEN Web Studio]
                       (Interactive Quiz, Study Key, PDF Export)
```

1. **Document Ingestion:** The uploaded PDF is parsed page-by-page via `PyPDF2`, removing broken line wraps, hyphenated words, and page headers.
2. **Candidate Mining:** Sentences are analyzed to identify key answers using regex patterns for proper nouns, capitalized phrases, historical years, and technical vocabulary.
3. **Passage Windowing:** The target answer is highlighted (`<hl> answer <hl>`) within its local sentence context (~80-120 words) to guarantee zero prompt truncation.
4. **Seq2Seq Inference:** The T5 model generates grammatically structured, relevant questions with beam search decoding (`num_beams=3`).
5. **Distractor Generation:** The system synthesizes 3 plausible alternative choices from other domain concepts in the text to form complete 4-option MCQs.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.10+
* **Framework:** Flask 2.x / 3.x
* **AI / NLP Model:** Hugging Face `transformers` (T5-small question generator)
* **Deep Learning Runtime:** PyTorch (`torch`)
* **Document Processing:** `PyPDF2`
* **Frontend:** Modern Semantic HTML5, Vanilla CSS3 (Custom design system), Vanilla JavaScript (ES6+)
* **Client-Side Export:** `html2pdf.js`

---

## 📂 Project Structure

```
-Edugen-Quiz-Generator-/
├── app.py              # Main Flask server, API routes & model inference
├── utils.py            # PDF parser, candidate answer miner & distractor logic
├── requirements.txt    # Project Python dependencies
├── .gitignore          # Git exclusion rules for clean version control
├── README.md           # Project documentation and guide
│
├── templates/
│   └── index.html      # Formal academic web application interface
│
└── static/
    ├── style.css       # Clean light-mode design system & responsive layout
    └── script.js       # Client controller: drag-drop, quiz engine, exports
```

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/231B121/-Edugen-Quiz-Generator-.git
cd -Edugen-Quiz-Generator-
```

### 2. Set Up a Virtual Environment (Optional but recommended)
```bash
python3 -m venv venv
source venv/bin/activate    # On Linux/macOS
# or: venv\Scripts\activate # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```

The application will start within seconds:
```text
⏳ Loading AI model (valhalla/t5-small-qg-hl)... Please wait a moment...
✅ Model loaded successfully on cpu!
🚀 Starting Flask server at http://127.0.0.1:5000 ...
```

### 5. Open in Your Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 📡 API Reference

### 1. Generate Quiz Questions
* **Endpoint:** `POST /generate`
* **Content-Type:** `multipart/form-data`
* **Parameters:**
  * `text_input` *(string, optional)*: Raw text or study notes.
  * `pdf_file` *(file, optional)*: PDF file to extract content from.
  * `num_questions` *(integer, default 5)*: Number of questions (1-15).
  * `difficulty` *(string, default "medium")*: "easy", "medium", or "hard".
* **Response:**
  ```json
  {
    "success": true,
    "questions": [
      {
        "id": 1,
        "question": "When was Artificial Intelligence founded as an academic discipline?",
        "answer": "1956",
        "options": ["1948", "1956", "1964", "1972"],
        "correct_index": 1,
        "context": "Artificial Intelligence was founded as an academic discipline in 1956."
      }
    ],
    "meta": {
      "total_generated": 1,
      "word_count": 85,
      "source": "Pasted Text",
      "difficulty": "medium"
    }
  }
  ```

### 2. Preview PDF Document
* **Endpoint:** `POST /preview-pdf`
* **Content-Type:** `multipart/form-data`
* **Parameters:**
  * `pdf_file` *(file, required)*: PDF file.
* **Response:**
  ```json
  {
    "success": true,
    "filename": "lecture_notes.pdf",
    "page_count": 4,
    "word_count": 1240,
    "preview": "Chapter 1: Principles of Computation..."
  }
  ```

---

## 📑 Export & Quiz Modes

* **Interactive Quiz Mode:** Enables students to test their knowledge with live radio buttons, automatic grading, and instant performance feedback.
* **Answer Key Mode:** Educators can review questions with answers and source contexts at a glance.
* **PDF Worksheet Export:** Generates formatted, clean, printable test papers complete with student instructions and a detached answer key.
* **Markdown & JSON:** Easily import questions into Notion, Google Docs, Canvas, Moodle, or custom LMS platforms.

---

## 👨‍💻 Author

**Gourav Ojha**  
GitHub: [@231B121](https://github.com/231B121) / 

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
