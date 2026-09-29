/**
 * EDUGEN - Formal Academic Quiz & Question Generator
 * Clean, lightweight, professional controller.
 */

(function () {
  // DOM Elements
  const tabText = document.getElementById("tab_text");
  const tabPdf = document.getElementById("tab_pdf");
  const textTabContent = document.getElementById("text_tab_content");
  const pdfTabContent = document.getElementById("pdf_tab_content");

  const textInput = document.getElementById("text_input");
  const wordCountSpan = document.getElementById("word_count");
  const charCountSpan = document.getElementById("char_count");
  const clearBtn = document.getElementById("clear_btn");
  const hlBtn = document.getElementById("hl_btn");

  const pdfDropzone = document.getElementById("pdf_dropzone");
  const pdfFileInput = document.getElementById("pdf_file");
  const pdfInfoCard = document.getElementById("pdf_info_card");
  const pdfName = document.getElementById("pdf_name");
  const pdfStats = document.getElementById("pdf_stats");
  const pdfPreviewText = document.getElementById("pdf_preview_text");
  const removePdfBtn = document.getElementById("remove_pdf_btn");

  const numQuestionsInput = document.getElementById("num_questions");
  const numBadge = document.getElementById("num_badge");
  const diffInput = document.getElementById("difficulty");
  const generateBtn = document.getElementById("generate_btn");

  const emptyPlaceholder = document.getElementById("empty_placeholder");
  const loader = document.getElementById("loader");
  const errorBox = document.getElementById("error_box");
  const errorMessage = document.getElementById("error_message");

  const resultsMetaBadge = document.getElementById("results_meta_badge");
  const resultsActionButtons = document.getElementById("results_action_buttons");
  const viewTabs = document.getElementById("view_tabs");
  const viewInteractive = document.getElementById("view_interactive");
  const viewStudy = document.getElementById("view_study");

  const quizDisplayContainer = document.getElementById("quiz_display_container");
  const quizSubmitRow = document.getElementById("quiz_submit_row");
  const submitQuizBtn = document.getElementById("submit_quiz_btn");
  const quizScoreBanner = document.getElementById("quiz_score_banner");
  const scoreValue = document.getElementById("score_value");
  const scoreHeadline = document.getElementById("score_headline");
  const scoreSubtext = document.getElementById("score_subtext");
  const retryQuizBtn = document.getElementById("retry_quiz_btn");

  const toggleAnswersBtn = document.getElementById("toggle_answers_btn");
  const copyAllBtn = document.getElementById("copy_all_btn");
  const exportPdfBtn = document.getElementById("export_pdf_btn");
  const exportJsonBtn = document.getElementById("export_json_btn");

  const helpBtn = document.getElementById("help_btn");
  const helpModal = document.getElementById("help_modal");
  const closeHelpBtn = document.getElementById("close_help_btn");
  const toastContainer = document.getElementById("toast_container");

  // State
  let currentQuestions = [];
  let currentMeta = null;
  let allAnswersVisible = false;
  let uploadedPdfFile = null;

  // Sample texts
  const SAMPLES = {
    ai: `Artificial Intelligence was founded as an academic discipline in 1956. John McCarthy coined the term during the historic Dartmouth Conference. Machine Learning is a core branch of artificial intelligence that allows computational systems to learn patterns directly from empirical data without manual programming. In 2017, the Transformer architecture was introduced in the paper Attention Is All You Need, fundamentally advancing natural language processing and neural sequence modeling.`,
    solar: `The Solar System formed approximately 4.6 billion years ago from the gravitational collapse of a giant interstellar molecular cloud. The vast majority of the system's mass resides in the Sun, with most of the remaining mass concentrated within Jupiter. There are eight recognized planets in the solar system, with Mercury being the closest to the Sun and Neptune being the farthest. Earth is the only known celestial body in the universe that harbors liquid surface oceans and living organisms.`,
    history: `The Industrial Revolution began in Great Britain during the mid-18th century and rapidly transformed manufacturing and agricultural economies into mechanized, urban societies. James Watt developed significant mechanical improvements to the steam engine in 1769, dramatically enhancing its thermal efficiency and practical power output. The expansion of steam-powered railways and automated cotton mills catalyzed global trade and modern industrial development.`
  };

  /* ================= Toast Notification ================= */
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      setTimeout(() => toast.remove(), 250);
    }, 2800);
  }

  /* ================= Tab Switching ================= */
  tabText.addEventListener("click", () => {
    tabText.classList.add("active");
    tabPdf.classList.remove("active");
    tabText.setAttribute("aria-selected", "true");
    tabPdf.setAttribute("aria-selected", "false");
    textTabContent.hidden = false;
    pdfTabContent.hidden = true;
  });

  tabPdf.addEventListener("click", () => {
    tabPdf.classList.add("active");
    tabText.classList.remove("active");
    tabPdf.setAttribute("aria-selected", "true");
    tabText.setAttribute("aria-selected", "false");
    pdfTabContent.hidden = false;
    textTabContent.hidden = true;
  });

  /* ================= Word & Character Stats ================= */
  function updateTextStats() {
    const val = textInput.value;
    const words = val.trim() ? val.trim().split(/\s+/).length : 0;
    const chars = val.length;
    wordCountSpan.textContent = `${words} word${words === 1 ? '' : 's'}`;
    charCountSpan.textContent = `${chars} character${chars === 1 ? '' : 's'}`;
  }

  textInput.addEventListener("input", updateTextStats);

  clearBtn.addEventListener("click", () => {
    textInput.value = "";
    updateTextStats();
  });

  /* ================= Quick Sample Loader ================= */
  document.querySelectorAll(".sample-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const sampleKey = btn.dataset.sample;
      if (SAMPLES[sampleKey]) {
        textInput.value = SAMPLES[sampleKey];
        updateTextStats();
        tabText.click();
        showToast("Sample text inserted.", "info");
      }
    });
  });

  /* ================= Range Slider ================= */
  numQuestionsInput.addEventListener("input", (e) => {
    numBadge.textContent = e.target.value;
  });

  /* ================= Mode Chips ================= */
  document.querySelectorAll(".mode-chip input").forEach(radio => {
    radio.addEventListener("change", (e) => {
      document.querySelectorAll(".mode-chip").forEach(c => c.classList.remove("active"));
      e.target.closest(".mode-chip").classList.add("active");
      applyDisplayModeFilter(e.target.value);
    });
  });

  function applyDisplayModeFilter(mode) {
    const cards = document.querySelectorAll(".question-card");
    cards.forEach(card => {
      const optionsGrid = card.querySelector(".options-grid");
      const answerDrawer = card.querySelector(".answer-drawer");
      if (mode === "mcq") {
        if (optionsGrid) optionsGrid.style.display = "grid";
        if (answerDrawer) answerDrawer.style.display = "none";
      } else if (mode === "qa") {
        if (optionsGrid) optionsGrid.style.display = "none";
        if (answerDrawer) answerDrawer.style.display = "block";
      } else {
        if (optionsGrid) optionsGrid.style.display = "grid";
        if (answerDrawer) answerDrawer.style.display = "block";
      }
    });
  }

  /* ================= Highlight Answer Helper ================= */
  hlBtn.addEventListener("click", () => {
    const start = textInput.selectionStart;
    const end = textInput.selectionEnd;
    const sel = textInput.value.substring(start, end).trim();

    if (!sel) {
      showToast("Select a term or phrase in the text first.", "info");
      return;
    }

    const before = textInput.value.substring(0, start);
    const after = textInput.value.substring(end);
    textInput.value = `${before}<hl>${sel}<hl>${after}`;
    textInput.focus();
    textInput.setSelectionRange(start + 4, start + 4 + sel.length);
    updateTextStats();
    showToast(`Marked "${sel}" as target answer.`, "info");
  });

  /* ================= PDF Upload & Preview ================= */
  pdfDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    pdfDropzone.classList.add("dragover");
  });

  pdfDropzone.addEventListener("dragleave", () => {
    pdfDropzone.classList.remove("dragover");
  });

  pdfDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    pdfDropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        handlePdfSelection(file);
      } else {
        showToast("Please provide a valid PDF document.", "error");
      }
    }
  });

  pdfFileInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
      handlePdfSelection(e.target.files[0]);
    }
  });

  async function handlePdfSelection(file) {
    uploadedPdfFile = file;
    pdfName.textContent = file.name;
    pdfStats.textContent = `Processing PDF (${(file.size / 1024).toFixed(1)} KB)...`;
    pdfInfoCard.hidden = false;
    pdfDropzone.hidden = true;

    const form = new FormData();
    form.append("pdf_file", file);

    try {
      const res = await fetch("/preview-pdf", { method: "POST", body: form });
      const data = await res.json();
      if (res.ok && data.success) {
        pdfStats.textContent = `${data.page_count} page${data.page_count === 1 ? '' : 's'} · ${data.word_count.toLocaleString()} words · ${(file.size / 1024).toFixed(1)} KB`;
        pdfPreviewText.textContent = data.preview;
        showToast("PDF parsed successfully.", "success");
      } else {
        pdfStats.textContent = `Error: ${data.error || "Could not read PDF"}`;
        pdfPreviewText.textContent = "Could not extract text. Verify that the document contains selectable text.";
        showToast(data.error || "Failed to extract text from PDF", "error");
      }
    } catch (err) {
      pdfStats.textContent = "Error communicating with server.";
      console.error(err);
    }
  }

  removePdfBtn.addEventListener("click", () => {
    uploadedPdfFile = null;
    pdfFileInput.value = "";
    pdfInfoCard.hidden = true;
    pdfDropzone.hidden = false;
    pdfPreviewText.textContent = "";
  });

  /* ================= Question Generation ================= */
  generateBtn.addEventListener("click", generateQuestions);

  textInput.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") {
      generateQuestions();
    }
  });

  async function generateQuestions() {
    const textVal = textInput.value.trim();
    if (!textVal && !uploadedPdfFile) {
      showToast("Please enter source text or upload a PDF document.", "error");
      return;
    }

    const num = parseInt(numQuestionsInput.value, 10) || 5;
    const diff = diffInput.value || "medium";

    // Set UI to loading state (Clean, no multi-step scanning animation)
    setLoadingState(true);

    const form = new FormData();
    form.append("text_input", textVal);
    form.append("num_questions", String(num));
    form.append("difficulty", diff);
    if (uploadedPdfFile) {
      form.append("pdf_file", uploadedPdfFile);
    }

    try {
      const res = await fetch("/generate", { method: "POST", body: form });
      const data = await res.json();
      setLoadingState(false);

      if (!res.ok) {
        showError(data.error || "Failed to generate questions.");
        return;
      }

      if (data.questions && data.questions.length) {
        currentQuestions = data.questions;
        currentMeta = data.meta;
        renderQuizResults();
      } else {
        showError(data.error || "No questions could be produced from the input text.");
      }
    } catch (err) {
      setLoadingState(false);
      showError("Server error: " + err.message);
      console.error(err);
    }
  }

  function setLoadingState(isLoading) {
    if (isLoading) {
      emptyPlaceholder.hidden = true;
      quizDisplayContainer.hidden = true;
      quizSubmitRow.hidden = true;
      quizScoreBanner.hidden = true;
      resultsMetaBadge.hidden = true;
      resultsActionButtons.hidden = true;
      viewTabs.hidden = true;
      errorBox.hidden = true;

      loader.hidden = false;
      generateBtn.querySelector(".btn-content").hidden = true;
      generateBtn.querySelector(".btn-loader").hidden = false;
      generateBtn.disabled = true;
    } else {
      loader.hidden = true;
      generateBtn.querySelector(".btn-content").hidden = false;
      generateBtn.querySelector(".btn-loader").hidden = true;
      generateBtn.disabled = false;
    }
  }

  function showError(msg) {
    errorBox.hidden = false;
    errorMessage.textContent = msg;
    showToast(msg, "error");
  }

  /* ================= Render Quiz Results ================= */
  function renderQuizResults() {
    quizDisplayContainer.innerHTML = "";
    errorBox.hidden = true;
    quizScoreBanner.hidden = true;

    resultsMetaBadge.hidden = false;
    resultsMetaBadge.textContent = `${currentQuestions.length} Questions Generated · ${currentMeta?.source || 'Content'} (${currentMeta?.word_count || 0} words)`;
    resultsActionButtons.hidden = false;
    viewTabs.hidden = false;
    quizSubmitRow.hidden = false;
    quizDisplayContainer.hidden = false;

    const optLetters = ["A", "B", "C", "D"];

    currentQuestions.forEach((q, idx) => {
      const qNum = idx + 1;
      const card = document.createElement("div");
      card.className = "question-card";
      card.dataset.qid = q.id || qNum;
      card.dataset.correctIdx = q.correct_index !== undefined ? q.correct_index : 0;

      // Question Header
      const cardTop = document.createElement("div");
      cardTop.className = "card-top";
      cardTop.innerHTML = `
        <span class="q-num-pill">Q${qNum}</span>
        <h3 class="q-title">${escapeHtml(q.question)}</h3>
        <button class="btn-card-copy" title="Copy question" data-copy="${escapeHtml(q.question)}">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
        </button>
      `;
      card.appendChild(cardTop);

      // Multiple Choice Options
      if (q.options && q.options.length) {
        const optionsGrid = document.createElement("div");
        optionsGrid.className = "options-grid";

        q.options.forEach((optText, oIdx) => {
          const letter = optLetters[oIdx] || String(oIdx + 1);
          const optionLabel = document.createElement("label");
          optionLabel.className = "option-item";
          optionLabel.innerHTML = `
            <input type="radio" name="q_${qNum}" value="${oIdx}">
            <span class="opt-letter">${letter}.</span>
            <span class="opt-text">${escapeHtml(optText)}</span>
          `;
          optionsGrid.appendChild(optionLabel);
        });

        card.appendChild(optionsGrid);
      }

      // Answer Drawer
      const answerDrawer = document.createElement("div");
      answerDrawer.className = "answer-drawer";
      answerDrawer.innerHTML = `
        <button class="answer-header-btn" type="button">
          <span>Show Answer</span>
        </button>
        <div class="answer-box" hidden>
          <div class="ans-line"><strong>Answer:</strong> ${escapeHtml(q.answer || "")}</div>
          ${q.context ? `<div class="context-line">"${escapeHtml(q.context)}"</div>` : ''}
        </div>
      `;

      const revealBtn = answerDrawer.querySelector(".answer-header-btn");
      const answerBox = answerDrawer.querySelector(".answer-box");
      revealBtn.addEventListener("click", () => {
        const isHidden = answerBox.hidden;
        answerBox.hidden = !isHidden;
        revealBtn.querySelector("span").textContent = isHidden ? "Hide Answer" : "Show Answer";
      });

      card.appendChild(answerDrawer);
      quizDisplayContainer.appendChild(card);
    });

    // Copy handlers
    document.querySelectorAll(".btn-card-copy").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(btn.dataset.copy);
        showToast("Question copied to clipboard.", "info");
      });
    });

    // Apply active filter
    const activeChip = document.querySelector(".mode-chip.active input");
    if (activeChip) applyDisplayModeFilter(activeChip.value);
  }

  /* ================= Interactive Evaluation ================= */
  submitQuizBtn.addEventListener("click", evaluateQuiz);

  function evaluateQuiz() {
    let score = 0;
    const total = currentQuestions.length;

    const cards = document.querySelectorAll(".question-card");
    cards.forEach((card, idx) => {
      const correctIdx = parseInt(card.dataset.correctIdx, 10);
      const selectedRadio = card.querySelector(`input[name="q_${idx + 1}"]:checked`);
      const allOptionItems = card.querySelectorAll(".option-item");

      allOptionItems.forEach(item => {
        item.classList.remove("correct-answer", "incorrect-selected");
      });

      if (selectedRadio) {
        const chosenIdx = parseInt(selectedRadio.value, 10);
        if (chosenIdx === correctIdx) {
          score++;
          allOptionItems[chosenIdx].classList.add("correct-answer");
        } else {
          allOptionItems[chosenIdx].classList.add("incorrect-selected");
          allOptionItems[correctIdx].classList.add("correct-answer");
        }
      } else {
        allOptionItems[correctIdx].classList.add("correct-answer");
      }

      // Show answer details
      const answerBox = card.querySelector(".answer-box");
      if (answerBox) answerBox.hidden = false;
      const revealBtn = card.querySelector(".answer-header-btn span");
      if (revealBtn) revealBtn.textContent = "Hide Answer";
    });

    quizScoreBanner.hidden = false;
    scoreValue.textContent = `${score} / ${total}`;

    const percentage = Math.round((score / total) * 100);
    if (percentage >= 80) {
      scoreHeadline.textContent = `Strong Performance (${percentage}%)`;
      scoreSubtext.textContent = "You demonstrated a firm understanding of the primary topics.";
    } else if (percentage >= 50) {
      scoreHeadline.textContent = `Satisfactory Result (${percentage}%)`;
      scoreSubtext.textContent = "Review the highlighted correct answers to reinforce key concepts.";
    } else {
      scoreHeadline.textContent = `Needs Review (${percentage}%)`;
      scoreSubtext.textContent = "Consider reading the source material and retrying the quiz.";
    }

    quizScoreBanner.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  retryQuizBtn.addEventListener("click", () => {
    document.querySelectorAll(".question-card").forEach(card => {
      card.querySelectorAll("input[type='radio']").forEach(r => r.checked = false);
      card.querySelectorAll(".option-item").forEach(item => {
        item.classList.remove("correct-answer", "incorrect-selected");
      });
      const answerBox = card.querySelector(".answer-box");
      if (answerBox) answerBox.hidden = true;
      const revealBtn = card.querySelector(".answer-header-btn span");
      if (revealBtn) revealBtn.textContent = "Show Answer";
    });
    quizScoreBanner.hidden = true;
    showToast("Quiz reset.", "info");
  });

  /* ================= View Modes ================= */
  viewInteractive.addEventListener("click", () => {
    viewInteractive.classList.add("active");
    viewStudy.classList.remove("active");
    quizSubmitRow.hidden = false;
    document.querySelectorAll(".options-grid").forEach(el => el.style.display = "grid");
  });

  viewStudy.addEventListener("click", () => {
    viewStudy.classList.add("active");
    viewInteractive.classList.remove("active");
    quizSubmitRow.hidden = true;
    document.querySelectorAll(".answer-box").forEach(el => el.hidden = false);
    document.querySelectorAll(".answer-header-btn span").forEach(el => el.textContent = "Hide Answer");
  });

  /* ================= Toggle Answers ================= */
  toggleAnswersBtn.addEventListener("click", () => {
    allAnswersVisible = !allAnswersVisible;
    document.querySelectorAll(".answer-box").forEach(el => {
      el.hidden = !allAnswersVisible;
    });
    document.querySelectorAll(".answer-header-btn span").forEach(el => {
      el.textContent = allAnswersVisible ? "Hide Answer" : "Show Answer";
    });
    toggleAnswersBtn.querySelector("span").textContent = allAnswersVisible ? "Hide Answers" : "Show Answers";
  });

  /* ================= Export Tools ================= */
  copyAllBtn.addEventListener("click", () => {
    if (!currentQuestions.length) return;
    const optLetters = ["A", "B", "C", "D"];
    let formatted = `EDUGEN · Quiz Questions\n------------------------\n\n`;

    currentQuestions.forEach((q, idx) => {
      formatted += `${idx + 1}. ${q.question}\n`;
      if (q.options && q.options.length) {
        q.options.forEach((opt, oIdx) => {
          formatted += `   ${optLetters[oIdx]}. ${opt}\n`;
        });
      }
      formatted += `   Correct Answer: ${q.answer}\n`;
      if (q.context) formatted += `   Context: ${q.context}\n`;
      formatted += `\n`;
    });

    navigator.clipboard.writeText(formatted);
    showToast("Quiz copied to clipboard.", "success");
  });

  exportPdfBtn.addEventListener("click", () => {
    if (!currentQuestions.length) return;

    const optLetters = ["A", "B", "C", "D"];
    const printContainer = document.createElement("div");
    printContainer.style.padding = "24px";
    printContainer.style.fontFamily = "Helvetica, Arial, sans-serif";
    printContainer.style.color = "#000";

    let html = `
      <div style="border-bottom: 2px solid #2563eb; padding-bottom: 10px; margin-bottom: 20px;">
        <h1 style="margin: 0; font-size: 18px; color: #1e3a8a;">Quiz Worksheet</h1>
        <p style="margin: 4px 0 0 0; font-size: 11px; color: #555;">Generated on ${new Date().toLocaleDateString()} · Total Questions: ${currentQuestions.length}</p>
      </div>
      <ol style="padding-left: 20px; font-size: 12px; line-height: 1.6;">
    `;

    currentQuestions.forEach((q) => {
      html += `<li style="margin-bottom: 14px;"><strong>${escapeHtml(q.question)}</strong>`;
      if (q.options && q.options.length) {
        html += `<div style="margin: 4px 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 11px;">`;
        q.options.forEach((opt, oIdx) => {
          html += `<div><strong>${optLetters[oIdx]}.</strong> ${escapeHtml(opt)}</div>`;
        });
        html += `</div>`;
      }
      html += `</li>`;
    });

    html += `
      </ol>
      <div style="margin-top: 30px; padding-top: 12px; border-top: 1px dashed #ccc;">
        <h3 style="font-size: 13px; color: #222; margin-bottom: 8px;">Answer Key</h3>
        <ol style="padding-left: 20px; font-size: 11px; color: #333;">
    `;

    currentQuestions.forEach((q) => {
      html += `<li style="margin-bottom: 3px;"><strong>${escapeHtml(q.answer)}</strong></li>`;
    });

    html += `</ol></div>`;
    printContainer.innerHTML = html;

    const opt = {
      margin: 12,
      filename: `quiz-worksheet-${Date.now()}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    if (window.html2pdf) {
      window.html2pdf().set(opt).from(printContainer).save();
      showToast("Downloading PDF...", "info");
    } else {
      showToast("PDF generation service unavailable.", "error");
    }
  });

  exportJsonBtn.addEventListener("click", () => {
    if (!currentQuestions.length) return;
    const jsonStr = JSON.stringify({ questions: currentQuestions, meta: currentMeta }, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `quiz-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("JSON file exported.", "info");
  });

  /* ================= Help Modal ================= */
  helpBtn.addEventListener("click", () => helpModal.showModal());
  closeHelpBtn.addEventListener("click", () => helpModal.close());
  helpModal.addEventListener("click", (e) => {
    if (e.target === helpModal) helpModal.close();
  });

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Init
  updateTextStats();
})();