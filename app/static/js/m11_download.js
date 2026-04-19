/*
 * M11 validation findings download.
 *
 * Reads the findings JSON and the source filename from the
 * #m11-download-controls element's data- attributes. CSV / JSON /
 * Markdown are generated client-side and offered via Blob download.
 * XLSX POSTs the findings to /validate/m11-docx/download/xlsx which
 * streams an openpyxl-generated workbook back.
 *
 * All four produce filenames of the form
 *   <source-basename>-m11-findings-<YYYY-MM-DD>.<ext>
 * so reports are easy to find later.
 */
(function () {
  "use strict";

  const controls = document.getElementById("m11-download-controls");
  if (!controls) return;

  let findings;
  try {
    findings = JSON.parse(controls.dataset.findings || "[]");
  } catch (err) {
    console.error("Could not parse M11 findings JSON:", err);
    return;
  }
  const sourceName = controls.dataset.sourceFilename || "protocol";

  function today() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  function baseName() {
    // Strip any extension so "foo.docx" becomes "foo".
    return sourceName.replace(/\.[^./\\]+$/, "");
  }

  function filenameFor(ext) {
    return `${baseName()}-m11-findings-${today()}.${ext}`;
  }

  function triggerDownload(blob, ext) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filenameFor(ext);
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  }

  // --- CSV -----------------------------------------------------------

  function csvField(value) {
    if (value === null || value === undefined) return "";
    const s = String(value);
    // Escape per RFC 4180: wrap in quotes if it contains comma, quote, or
    // newline; double any embedded quotes.
    if (/[",\r\n]/.test(s)) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  }

  function toCsv(findings) {
    const header = [
      "rule_id",
      "severity",
      "status",
      "element",
      "section",
      "message",
      "expected",
      "actual",
    ];
    const rows = [header.map(csvField).join(",")];
    findings.forEach((f) => {
      rows.push(
        [
          f.rule_id,
          f.severity,
          f.status,
          f.element_name,
          f.section_title,
          f.message,
          f.expected,
          f.actual,
        ]
          .map(csvField)
          .join(","),
      );
    });
    return rows.join("\r\n") + "\r\n";
  }

  // --- Markdown ------------------------------------------------------

  function mdCell(value) {
    // Escape pipes and newlines so the table doesn't break.
    if (value === null || value === undefined) return "";
    return String(value).replace(/\|/g, "\\|").replace(/\n/g, " ");
  }

  function toMarkdown(findings) {
    const header = [
      "Rule",
      "Severity",
      "Status",
      "Element",
      "Section",
      "Message",
      "Expected",
      "Actual",
    ];
    const lines = [];
    lines.push(`# M11 Validation Findings`);
    lines.push("");
    lines.push(`**Source:** ${sourceName}`);
    lines.push(`**Generated:** ${today()}`);
    lines.push(`**Findings:** ${findings.length}`);
    lines.push("");
    if (findings.length === 0) {
      lines.push("_No findings._");
      return lines.join("\n") + "\n";
    }
    lines.push(`| ${header.join(" | ")} |`);
    lines.push(`| ${header.map(() => "---").join(" | ")} |`);
    findings.forEach((f) => {
      lines.push(
        `| ${[
          f.rule_id,
          f.severity,
          f.status,
          f.element_name,
          f.section_title,
          f.message,
          f.expected,
          f.actual,
        ]
          .map(mdCell)
          .join(" | ")} |`,
      );
    });
    return lines.join("\n") + "\n";
  }

  // --- handlers ------------------------------------------------------

  function downloadCsv() {
    const blob = new Blob([toCsv(findings)], {
      type: "text/csv;charset=utf-8",
    });
    triggerDownload(blob, "csv");
  }

  function downloadJson() {
    // Pretty-print for readability; the field order matches what the
    // server serialises, so diffing two reports is straightforward.
    const blob = new Blob([JSON.stringify(findings, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    triggerDownload(blob, "json");
  }

  function downloadMarkdown() {
    const blob = new Blob([toMarkdown(findings)], {
      type: "text/markdown;charset=utf-8",
    });
    triggerDownload(blob, "md");
  }

  async function downloadXlsx() {
    // Server round-trip: openpyxl generates the .xlsx from the same
    // JSON the client already has, streaming it back. The filename we
    // want is appended as a query-string; the server honours it if
    // present, otherwise falls back to a server-side default.
    const url =
      "/validate/m11-docx/download/xlsx?filename=" +
      encodeURIComponent(filenameFor("xlsx"));
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          findings: findings,
          source_filename: sourceName,
        }),
      });
      if (!response.ok) {
        console.error("XLSX download failed:", response.status);
        return;
      }
      const blob = await response.blob();
      triggerDownload(blob, "xlsx");
    } catch (err) {
      console.error("XLSX download error:", err);
    }
  }

  const handlers = {
    csv: downloadCsv,
    json: downloadJson,
    md: downloadMarkdown,
    xlsx: downloadXlsx,
  };

  controls.addEventListener("click", (event) => {
    const btn = event.target.closest("[data-m11-download]");
    if (!btn) return;
    const format = btn.dataset.m11Download;
    const handler = handlers[format];
    if (handler) {
      handler();
    }
  });
})();
