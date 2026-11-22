document.addEventListener("DOMContentLoaded", () => {
  // 1. Quick Demo Chips on Home Page
  document.querySelectorAll("[data-demo-desc]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const desc = document.getElementById("description");
      const osSelect = document.getElementById("target_os");
      if (desc) desc.value = btn.getAttribute("data-demo-desc") || "";
      if (osSelect && btn.getAttribute("data-demo-os")) {
        osSelect.value = btn.getAttribute("data-demo-os");
      }
    });
  });

  // 2. Cross-OS Learning Drawer Tabs
  document.querySelectorAll("[data-os-tab]").forEach((tab) => {
    tab.addEventListener("click", () => {
      const target = tab.getAttribute("data-os-tab");
      document.querySelectorAll("[data-os-tab]").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      document.querySelectorAll("[data-os-panel]").forEach((panel) => {
        panel.classList.toggle("hidden", panel.getAttribute("data-os-panel") !== target);
      });
    });
  });

  // 3. Copy to Clipboard buttons (commands & Markdown report)
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      let text = btn.getAttribute("data-copy-text") || "";
      const targetId = btn.getAttribute("data-copy-target");
      if (targetId) {
        const el = document.getElementById(targetId);
        if (el) text = el.value || el.textContent || "";
      }
      if (!text) return;
      try {
        await navigator.clipboard.writeText(text);
        const orig = btn.textContent;
        btn.textContent = btn.getAttribute("data-copied-label") || "Copied!";
        setTimeout(() => { btn.textContent = orig; }, 1600);
      } catch {
        // Clipboard fallback
      }
    });
  });

  // 4. Instant Command Output Auto-Parser (fetch /api/parse-output)
  const parseBtn = document.getElementById("btn-parse-output");
  if (parseBtn) {
    parseBtn.addEventListener("click", async () => {
      const rawBox = document.getElementById("raw_command_output");
      const preview = document.getElementById("parser-preview");
      if (!rawBox || !preview) return;

      const parserKey = parseBtn.getAttribute("data-parser-key");
      const targetOs = parseBtn.getAttribute("data-target-os") || "windows";

      const res = await fetch("/api/parse-output", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          parser_key: parserKey,
          raw_output: rawBox.value,
          target_os: targetOs,
        }),
      });
      const data = await res.json();

      preview.classList.remove("hidden");
      if (!res.ok) {
        preview.textContent = data.error || "Parser error";
        return;
      }

      preview.innerHTML =
        `<strong>Result:</strong> <code>${data.suggested_result_code}</code> — ${data.summary}`;

      // Highlight and auto-select matching outcome radio card
      document.querySelectorAll(".outcome-card").forEach((c) => c.classList.remove("suggested"));
      let matchedCard = null;
      if (data.suggested_outcome_id) {
        matchedCard = document.querySelector(
          `.outcome-card[data-outcome-id="${data.suggested_outcome_id}"]`
        );
      } else if (data.suggested_result_code) {
        const byCode = document.querySelectorAll(
          `.outcome-card[data-result-code="${data.suggested_result_code}"]`
        );
        if (byCode.length === 1) matchedCard = byCode[0];
      }
      if (matchedCard) {
        matchedCard.classList.add("suggested");
        const radio = matchedCard.querySelector('input[type="radio"]');
        if (radio) radio.checked = true;
      }
    });
  }
});
