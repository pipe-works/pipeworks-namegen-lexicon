(function () {
  const classKeys = [
    ["first_name", "First Name"],
    ["last_name", "Last Name"],
    ["place_name", "Place Name"],
    ["location_name", "Location Name"],
    ["object_item", "Object Item"],
    ["organisation", "Organisation"],
    ["title_epithet", "Title Epithet"],
  ];

  const tabs = Array.from(document.querySelectorAll(".tab"));
  const panels = {
    generate: document.getElementById("panel-generate"),
    favorites: document.getElementById("panel-favorites"),
    help: document.getElementById("panel-help"),
  };

  const queuedSelections = new Map();
  let generatedPreviewEntries = [];
  let generatedComboEntries = [];

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function setActiveTab(tabName) {
    for (const tab of tabs) {
      tab.classList.toggle("active", tab.dataset.tab === tabName);
    }
    for (const [name, panel] of Object.entries(panels)) {
      panel.classList.toggle("active", name === tabName);
    }
  }

  function applyTheme(theme) {
    const toggle = document.getElementById("theme-toggle");
    document.documentElement.dataset.theme = theme;
    toggle.textContent = theme === "dark" ? "Light Theme" : "Dark Theme";
    try {
      window.localStorage.setItem("pipeworks-theme", theme);
    } catch (_error) {
      // Theme persistence is nice to have, not required for app correctness.
    }
  }

  function initThemeToggle() {
    let storedTheme = "dark";
    try {
      storedTheme = window.localStorage.getItem("pipeworks-theme") || "dark";
    } catch (_error) {
      storedTheme = "dark";
    }
    applyTheme(storedTheme);
    document.getElementById("theme-toggle").addEventListener("click", () => {
      const current = document.documentElement.dataset.theme || "dark";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  function getFavoriteDefaults() {
    const rawTags = document.getElementById("favorite-tags").value.trim();
    return {
      tags: rawTags ? rawTags.split(",").map((tag) => tag.trim()).filter(Boolean) : [],
      note_md: document.getElementById("favorite-note").value.trim() || null,
    };
  }

  function readGenerationDefaults() {
    const count = Number(document.getElementById("generation-count").value || "10");
    const seedRaw = document.getElementById("generation-seed").value.trim();
    return {
      generation_count: Number.isFinite(count) ? Math.max(1, Math.min(50, count)) : 10,
      unique_only: document.getElementById("generation-unique-only").checked,
      render_style: document.getElementById("generation-render-style").value,
      output_format: "json",
      seed: seedRaw ? Number(seedRaw) : null,
    };
  }

  async function fetchJson(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || `Request failed: ${response.status}`);
    }
    return data;
  }

  function renderCardGrid() {
    const grid = document.getElementById("generation-card-grid");
    grid.innerHTML = "";
    for (const [classKey, label] of classKeys) {
      const card = document.createElement("article");
      card.className = "class-card";
      card.innerHTML = `
        <h2>${escapeHtml(label)}</h2>
        <label class="field">
          <span>Package</span>
          <select id="package-${classKey}" class="select">
            <option value="">Loading packages...</option>
          </select>
        </label>
        <label class="field">
          <span>Syllables</span>
          <select id="syllable-${classKey}" class="select" disabled>
            <option value="">Select package first</option>
          </select>
        </label>
        <button type="button" id="queue-${classKey}" class="btn btn--primary" disabled>
          Queue Selection
        </button>
        <p id="note-${classKey}" class="muted">Loading package options...</p>
      `;
      grid.appendChild(card);
      document.getElementById(`package-${classKey}`).addEventListener("change", () => {
        loadSyllablesForClass(classKey);
      });
      document.getElementById(`queue-${classKey}`).addEventListener("click", () => {
        queueClassSelection(classKey, label);
      });
    }
  }

  async function loadPackageOptions() {
    const payload = await fetchJson("/api/generation/package-options");
    const classMap = new Map((payload.name_classes || []).map((entry) => [entry.key, entry]));
    for (const [classKey] of classKeys) {
      const packageSelect = document.getElementById(`package-${classKey}`);
      const note = document.getElementById(`note-${classKey}`);
      const entry = classMap.get(classKey);
      packageSelect.innerHTML = "";
      if (!entry || !(entry.packages || []).length) {
        packageSelect.innerHTML = '<option value="">No packages available</option>';
        packageSelect.disabled = true;
        note.textContent = "No prepared packages available for this class yet.";
        continue;
      }
      packageSelect.disabled = false;
      packageSelect.innerHTML = '<option value="">Select package</option>';
      for (const pkg of entry.packages) {
        const option = document.createElement("option");
        option.value = String(pkg.package_id);
        option.textContent = `${pkg.package_name} (id ${pkg.package_id})`;
        option.dataset.packageName = pkg.package_name;
        packageSelect.appendChild(option);
      }
      note.textContent = `Loaded ${entry.packages.length} prepared package option(s).`;
    }
  }

  async function loadSyllablesForClass(classKey) {
    const packageSelect = document.getElementById(`package-${classKey}`);
    const queueButton = document.getElementById(`queue-${classKey}`);
    const syllableSelect = document.getElementById(`syllable-${classKey}`);
    const note = document.getElementById(`note-${classKey}`);
    const packageId = packageSelect.value;
    syllableSelect.innerHTML = "";
    queueButton.disabled = true;

    if (!packageId) {
      syllableSelect.innerHTML = '<option value="">Select package first</option>';
      syllableSelect.disabled = true;
      note.textContent = "Select a package to load syllable options.";
      return;
    }

    const params = new URLSearchParams({ class_key: classKey, package_id: packageId });
    const payload = await fetchJson(`/api/generation/package-syllables?${params.toString()}`);
    const options = payload.syllable_options || [];
    if (!options.length) {
      syllableSelect.innerHTML = '<option value="">No syllables available</option>';
      syllableSelect.disabled = true;
      note.textContent = "Selected package has no syllable options for this class.";
      return;
    }

    syllableSelect.disabled = false;
    syllableSelect.innerHTML = '<option value="">Select syllable mode</option>';
    for (const optionData of options) {
      const option = document.createElement("option");
      option.value = optionData.key;
      option.textContent = optionData.label;
      syllableSelect.appendChild(option);
    }
    syllableSelect.addEventListener(
      "change",
      () => {
        queueButton.disabled = !syllableSelect.value;
      },
      { once: true }
    );
    note.textContent = `Loaded ${options.length} syllable option(s).`;
  }

  function queueClassSelection(classKey, label) {
    const packageSelect = document.getElementById(`package-${classKey}`);
    const syllableSelect = document.getElementById(`syllable-${classKey}`);
    const packageOption = packageSelect.options[packageSelect.selectedIndex];
    const syllableOption = syllableSelect.options[syllableSelect.selectedIndex];
    if (!packageSelect.value || !syllableSelect.value) {
      return;
    }

    queuedSelections.set(classKey, {
      class_key: classKey,
      class_label: label,
      package_id: Number(packageSelect.value),
      package_label: packageOption.dataset.packageName || packageOption.textContent,
      syllable_key: syllableSelect.value,
      syllable_label: syllableOption.textContent,
    });
    renderSelectionSummary();
  }

  function renderSelectionSummary() {
    const summary = document.getElementById("selection-summary");
    if (!queuedSelections.size) {
      summary.className = "selection-summary muted";
      summary.textContent = "No selections queued yet.";
      return;
    }
    summary.className = "selection-summary";
    summary.innerHTML = Array.from(queuedSelections.values())
      .map(
        (item) => `
          <div class="selection-pill">
            <strong>${escapeHtml(item.class_label)}</strong>
            <span>${escapeHtml(item.package_label)}</span>
            <span>${escapeHtml(item.syllable_label)}</span>
          </div>
        `
      )
      .join("");
  }

  function renderPreviewGroups(groups) {
    const container = document.getElementById("preview-results");
    if (!groups.length) {
      container.innerHTML = "";
      return;
    }
    container.innerHTML = groups
      .map(
        (group) => `
          <article class="preview-group">
            <h3>${escapeHtml(group.heading)}</h3>
            <div class="name-chip-list">
              ${group.names.map((name) => `<span class="name-chip">${escapeHtml(name)}</span>`).join("")}
            </div>
          </article>
        `
      )
      .join("");
  }

  function renderComboResults(names) {
    const container = document.getElementById("combo-results");
    if (!names.length) {
      container.innerHTML = "";
      return;
    }
    container.innerHTML = `
      <article class="preview-group">
        <h3>Combined names</h3>
        <div class="name-chip-list">
          ${names.map((name) => `<span class="name-chip">${escapeHtml(name)}</span>`).join("")}
        </div>
      </article>
    `;
  }

  async function generatePreview() {
    const previewStatus = document.getElementById("preview-status");
    const comboStatus = document.getElementById("combo-status");
    if (!queuedSelections.size) {
      previewStatus.className = "err";
      previewStatus.textContent = "Queue at least one selection first.";
      return;
    }

    const defaults = readGenerationDefaults();
    const groups = [];
    const namesByClass = {};
    generatedPreviewEntries = [];
    generatedComboEntries = [];

    previewStatus.className = "muted";
    previewStatus.textContent = "Generating preview...";
    comboStatus.className = "muted";
    comboStatus.textContent = "Building combinations...";

    for (const selection of queuedSelections.values()) {
      const payload = {
        class_key: selection.class_key,
        package_id: selection.package_id,
        syllable_key: selection.syllable_key,
        generation_count: defaults.generation_count,
        unique_only: defaults.unique_only,
        output_format: defaults.output_format,
        render_style: defaults.render_style,
      };
      if (defaults.seed !== null && Number.isFinite(defaults.seed)) {
        payload.seed = defaults.seed;
      }
      const result = await fetchJson("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const names = (result.names || []).map((value) => String(value));
      namesByClass[selection.class_key] = names;
      groups.push({
        heading: `${selection.class_label} · ${selection.package_label} · ${selection.syllable_label}`,
        names,
      });
      for (const name of names) {
        generatedPreviewEntries.push({
          name,
          source: "names_app_preview",
          name_class: selection.class_key,
          package_id: selection.package_id,
          package_name: selection.package_label,
          syllable_key: selection.syllable_key,
          render_style: defaults.render_style,
          output_format: defaults.output_format,
          seed: defaults.seed,
          metadata: { selection },
        });
      }
    }

    renderPreviewGroups(groups);
    previewStatus.className = "ok";
    previewStatus.textContent = `Generated ${generatedPreviewEntries.length} preview name(s).`;

    const firstNames = namesByClass.first_name || [];
    const lastNames = namesByClass.last_name || [];
    const combos = [];
    if (firstNames.length && lastNames.length) {
      for (const first of firstNames) {
        for (const last of lastNames) {
          combos.push(`${first} ${last}`);
          if (combos.length >= 40) {
            break;
          }
        }
        if (combos.length >= 40) {
          break;
        }
      }
    }

    generatedComboEntries = combos.map((name) => ({
      name,
      source: "names_app_combo",
      name_class: "full_name",
      metadata: { derived_from: ["first_name", "last_name"] },
    }));
    renderComboResults(combos);
    comboStatus.className = combos.length ? "ok" : "muted";
    comboStatus.textContent = combos.length
      ? `Built ${combos.length} first + last combination(s).`
      : "Generate at least one First Name and one Last Name preview.";
  }

  async function saveFavorites(entries, emptyMessage) {
    if (!entries.length) {
      window.alert(emptyMessage);
      return;
    }
    const defaults = getFavoriteDefaults();
    await fetchJson("/api/favorites", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        entries,
        tags: defaults.tags,
        note_md: defaults.note_md,
      }),
    });
    await loadFavorites();
  }

  async function loadFavorites() {
    const status = document.getElementById("favorites-status");
    const body = document.getElementById("favorites-table-body");
    status.className = "muted";
    status.textContent = "Loading favorites...";
    const payload = await fetchJson("/api/favorites?limit=100&offset=0");
    const favorites = payload.favorites || [];
    body.innerHTML = "";
    if (!favorites.length) {
      status.textContent = "No favorites saved yet.";
      body.innerHTML = `
        <tr><td colspan="7" class="muted">No favorites saved yet.</td></tr>
      `;
      return;
    }
    status.className = "ok";
    status.textContent = `Loaded ${favorites.length} favorite(s).`;
    for (const favorite of favorites) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${escapeHtml(favorite.name)}</td>
        <td>${escapeHtml(favorite.name_class || "—")}</td>
        <td>${escapeHtml(favorite.package_name || "—")}</td>
        <td>${escapeHtml((favorite.tags || []).join(", ") || "—")}</td>
        <td>${escapeHtml(favorite.source || "—")}</td>
        <td>${escapeHtml(favorite.created_at || "—")}</td>
        <td><button type="button" class="btn btn--secondary btn--sm favorites-delete-btn" data-favorite-id="${favorite.id}">Delete</button></td>
      `;
      body.appendChild(row);
    }
    for (const button of document.querySelectorAll(".favorites-delete-btn")) {
      button.addEventListener("click", async () => {
        await fetchJson("/api/favorites/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ favorite_id: Number(button.dataset.favoriteId) }),
        });
        await loadFavorites();
      });
    }
  }

  async function loadAppConfig() {
    const payload = await fetchJson("/api/app-config");
    const version = document.getElementById("app-version");
    version.textContent = `names · v${payload.app_version}`;
    const status = document.getElementById("upstream-status");
    status.className = "status-pill status-pill--ok";
    status.textContent = "Connected";
  }

  async function init() {
    renderCardGrid();
    tabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        setActiveTab(tab.dataset.tab);
        if (tab.dataset.tab === "favorites") {
          loadFavorites().catch((error) => {
            document.getElementById("favorites-status").textContent = error.message;
          });
        }
      });
    });
    initThemeToggle();
    document.getElementById("clear-selections-btn").addEventListener("click", () => {
      queuedSelections.clear();
      renderSelectionSummary();
    });
    document.getElementById("generate-preview-btn").addEventListener("click", () => {
      generatePreview().catch((error) => {
        document.getElementById("preview-status").className = "err";
        document.getElementById("preview-status").textContent = error.message;
      });
    });
    document.getElementById("favorite-preview-btn").addEventListener("click", () => {
      saveFavorites(generatedPreviewEntries, "Generate preview names first.").catch((error) => {
        window.alert(error.message);
      });
    });
    document.getElementById("favorite-combos-btn").addEventListener("click", () => {
      saveFavorites(generatedComboEntries, "Generate first and last combinations first.").catch(
        (error) => {
          window.alert(error.message);
        }
      );
    });
    document.getElementById("favorites-refresh-btn").addEventListener("click", () => {
      loadFavorites().catch((error) => {
        document.getElementById("favorites-status").textContent = error.message;
      });
    });

    try {
      await loadAppConfig();
      await loadPackageOptions();
      renderSelectionSummary();
    } catch (error) {
      const status = document.getElementById("upstream-status");
      status.className = "status-pill status-pill--err";
      status.textContent = "Upstream unavailable";
      document.getElementById("preview-status").className = "err";
      document.getElementById("preview-status").textContent = error.message;
    }
  }

  init();
})();
