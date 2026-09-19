(function () {
  "use strict";

  var list = document.getElementById("process-list");
  var addButton = document.getElementById("add-process");
  var count = document.getElementById("process-count");
  var form = document.getElementById("simulation-form");
  var algorithm = document.getElementById("algorithm");
  var quantumField = document.getElementById("quantum-field");
  var algorithmNote = document.getElementById("algorithm-note-text");
  var formStatus = document.getElementById("form-status");

  if (!list) return;

  var notes = {
    fcfs: "FCFS is non-preemptive: the oldest ready process gets the CPU first.",
    sjf: "SJF is non-preemptive: the shortest burst in the ready queue gets the next dispatch.",
    priority: "Priority scheduling selects the most urgent ready process. Lower values are treated as higher priority.",
    round_robin: "Round Robin rotates through ready processes. Each process receives the CPU for one quantum."
  };

  function rows() {
    return Array.prototype.slice.call(list.querySelectorAll("[data-process-row]"));
  }

  function updateCount() {
    var total = rows().length;
    if (count) count.textContent = total;
    var empty = document.getElementById("empty-processes");
    if (empty) empty.classList.toggle("hidden", total > 0);
  }

  function buildRow(index, values) {
    values = values || {};
    var row = document.createElement("div");
    row.className = "process-row";
    row.setAttribute("data-process-row", "");
    row.innerHTML =
      '<span class="process-number">P' + index + '</span>' +
      '<div class="field-group">' +
        '<label class="field-label" for="process-id-' + index + '">ID</label>' +
        '<input class="field-control" id="process-id-' + index + '" name="process_id[]" value="' + escapeHtml(values.id || "P" + index) + '" required data-process-field="id" data-testid="input-process-id-' + index + '">' +
      '</div>' +
      '<div class="field-group">' +
        '<label class="field-label" for="arrival-time-' + index + '">Arrival</label>' +
        '<input class="field-control" id="arrival-time-' + index + '" name="arrival_time[]" type="number" min="0" step="1" value="' + escapeHtml(values.arrival || 0) + '" required data-process-field="arrival" data-testid="input-arrival-time-' + index + '">' +
      '</div>' +
      '<div class="field-group">' +
        '<label class="field-label" for="burst-time-' + index + '">Burst</label>' +
        '<input class="field-control" id="burst-time-' + index + '" name="burst_time[]" type="number" min="1" step="1" value="' + escapeHtml(values.burst || 1) + '" required data-process-field="burst" data-testid="input-burst-time-' + index + '">' +
      '</div>' +
      '<div class="field-group">' +
        '<label class="field-label" for="priority-' + index + '">Priority</label>' +
        '<input class="field-control" id="priority-' + index + '" name="priority[]" type="number" min="0" step="1" value="' + escapeHtml(values.priority || 1) + '" required data-process-field="priority" data-testid="input-priority-' + index + '">' +
      '</div>' +
      '<button class="remove-process" type="button" aria-label="Remove process P' + index + '" data-remove-process data-testid="button-remove-process-' + index + '">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M5 12h14"/></svg>' +
      '</button>';
    return row;
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[character];
    });
  }

  function renumberRows() {
    rows().forEach(function (row, position) {
      var index = position + 1;
      var marker = row.querySelector(".process-number");
      var remove = row.querySelector("[data-remove-process]");
      if (marker) marker.textContent = "P" + index;
      if (remove) {
        remove.setAttribute("aria-label", "Remove process P" + index);
        remove.setAttribute("data-testid", "button-remove-process-" + index);
      }
      row.querySelectorAll("label, input").forEach(function (element) {
        var field = element.getAttribute("data-process-field");
        var base = field === "id" ? "process-id" : field === "arrival" ? "arrival-time" : field === "burst" ? "burst-time" : "priority";
        if (element.tagName.toLowerCase() === "label") element.setAttribute("for", base + "-" + index);
        if (element.tagName.toLowerCase() === "input") {
          element.id = base + "-" + index;
          element.setAttribute("data-testid", "input-" + base + "-" + index);
        }
      });
    });
  }

  function updatePolicy() {
    if (!algorithm) return;
    var value = algorithm.value;
    if (quantumField) quantumField.classList.toggle("hidden", value !== "round_robin");
    if (algorithmNote) algorithmNote.textContent = notes[value] || notes.fcfs;
  }

  addButton && addButton.addEventListener("click", function () {
    var next = rows().length + 1;
    list.appendChild(buildRow(next));
    renumberRows();
    updateCount();
    var newest = rows()[rows().length - 1];
    var firstInput = newest && newest.querySelector("input");
    if (firstInput) firstInput.focus();
  });

  list.addEventListener("click", function (event) {
    var removeButton = event.target.closest("[data-remove-process]");
    if (!removeButton) return;
    var row = removeButton.closest("[data-process-row]");
    if (row) {
      row.style.opacity = "0";
      row.style.transform = "translateX(8px)";
      window.setTimeout(function () {
        row.remove();
        renumberRows();
        updateCount();
      }, 180);
    }
  });

  algorithm && algorithm.addEventListener("change", updatePolicy);

  function clearInvalidState() {
    list.querySelectorAll("[aria-invalid='true']").forEach(function (input) {
      input.removeAttribute("aria-invalid");
    });
  }

  form && form.addEventListener("submit", function (event) {
    clearInvalidState();
    var processRows = rows();
    var invalid = [];
    if (!processRows.length) {
      event.preventDefault();
      if (formStatus) formStatus.textContent = "Add at least one process before running.";
      if (addButton) addButton.focus();
      return;
    }
    processRows.forEach(function (row) {
      row.querySelectorAll("input[required]").forEach(function (input) {
        var value = input.value.trim();
        var number = input.type === "number" ? Number(value) : 0;
        var invalidNumber = input.type === "number" && (!Number.isFinite(number) || number < Number(input.min || 0));
        if (!value || invalidNumber || (input.dataset.processField === "burst" && number < 1)) {
          input.setAttribute("aria-invalid", "true");
          invalid.push(input);
        }
      });
    });
    if (algorithm && algorithm.value === "round_robin") {
      var quantum = document.getElementById("quantum");
      if (quantum && (!quantum.value || Number(quantum.value) < 1)) {
        quantum.setAttribute("aria-invalid", "true");
        invalid.push(quantum);
      }
    }
    if (invalid.length) {
      event.preventDefault();
      if (formStatus) formStatus.textContent = "Resolve the highlighted fields before dispatch.";
      invalid[0].focus();
    } else if (formStatus) {
      formStatus.textContent = "Dispatching workload…";
    }
  });

  form && form.addEventListener("reset", function () {
    window.setTimeout(function () {
      list.querySelectorAll("[data-process-row]").forEach(function (row) { row.remove(); });
      updateCount();
      clearInvalidState();
      if (formStatus) formStatus.textContent = "";
      updatePolicy();
    }, 0);
  });

  updateCount();
  updatePolicy();
}());