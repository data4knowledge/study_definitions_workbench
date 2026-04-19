/*
 * Annotated-document interactivity.
 *
 * The server-side annotator (app/utility/m11_annotate.py) injects
 * <span class="m11-doc-marker" data-m11-finding-index="N"> elements
 * inside each validated element on the rendered protocol. The full
 * findings list is embedded on #m11-document-tab as a JSON data
 * attribute. This script wires up:
 *
 *   - click / keyboard activation on each marker → open a side panel
 *     showing the finding details for that marker's index.
 *   - close button / Esc key / click outside → close the panel.
 *   - visual focus highlight on the element the finding applies to.
 *
 * No dependency on Bootstrap's offcanvas — a plain CSS-animated <aside>
 * is enough and keeps the JS footprint minimal.
 */
(function () {
  "use strict";

  const docTab = document.getElementById("m11-document-tab");
  const panel = document.getElementById("m11-finding-panel");
  if (!docTab || !panel) return;

  let findings = [];
  try {
    findings = JSON.parse(docTab.dataset.findings || "[]");
  } catch (err) {
    console.error("Could not parse M11 findings JSON for annotated doc:", err);
    return;
  }

  const body = document.getElementById("m11-finding-panel-body");
  const title = document.getElementById("m11-finding-panel-title");
  const closeBtn = panel.querySelector(".m11-close");

  // Track the element currently highlighted as "active" so we can
  // strip the highlight when the panel closes or moves.
  let activeElement = null;

  function clearFocus() {
    if (activeElement) {
      activeElement.classList.remove("m11-element-focus");
      activeElement = null;
    }
  }

  function closePanel() {
    panel.classList.remove("open");
    clearFocus();
  }

  function openForIndex(index, markerElement) {
    const finding = findings[index];
    if (!finding) return;

    title.textContent = `${finding.rule_id || "Finding"}${finding.element_name ? " — " + finding.element_name : ""}`;

    // Populate the definition list. Skipped fields don't render —
    // nothing more awkward than "Expected:" with no value.
    const entries = [
      ["Severity", finding.status || finding.severity],
      ["Section", finding.section_title],
      ["Message", finding.message],
      ["Expected", finding.expected],
      ["Actual", finding.actual],
    ];
    body.innerHTML = "";
    entries.forEach(function ([label, value]) {
      if (value === undefined || value === null || value === "") return;
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      body.appendChild(dt);
      body.appendChild(dd);
    });

    panel.classList.add("open");

    // Highlight the element the finding applies to, so the user can
    // see at a glance which part of the protocol is being discussed.
    clearFocus();
    const element = markerElement ? markerElement.closest("[data-m11-element]") : null;
    if (element) {
      element.classList.add("m11-element-focus");
      activeElement = element;
    }
  }

  // Event delegation — one listener on the tab covers every marker,
  // and keeps working if the inner HTML is ever re-rendered.
  docTab.addEventListener("click", function (event) {
    const marker = event.target.closest(".m11-doc-marker");
    if (!marker) return;
    event.preventDefault();
    const index = parseInt(marker.dataset.m11FindingIndex, 10);
    openForIndex(index, marker);
  });

  // Keyboard activation (Enter / Space) for accessibility. Tabindex=0
  // is set on the marker by the annotator so it's in the focus order.
  docTab.addEventListener("keydown", function (event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    const marker = event.target.closest(".m11-doc-marker");
    if (!marker) return;
    event.preventDefault();
    const index = parseInt(marker.dataset.m11FindingIndex, 10);
    openForIndex(index, marker);
  });

  closeBtn.addEventListener("click", closePanel);

  // Esc closes the panel from anywhere on the page.
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && panel.classList.contains("open")) {
      closePanel();
    }
  });

  // Click outside the panel (while it's open) closes it. We check the
  // marker inclusion too so clicking a DIFFERENT marker while the
  // panel is open re-opens on that one instead of closing.
  document.addEventListener("click", function (event) {
    if (!panel.classList.contains("open")) return;
    if (panel.contains(event.target)) return;
    if (event.target.closest(".m11-doc-marker")) return;
    closePanel();
  });
})();
