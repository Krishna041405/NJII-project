const API_BASE = "http://127.0.0.1:8000";

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const payload = await response.json();
      if (payload && typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch (error) {
      // Ignore JSON parsing errors and keep the HTTP status message.
    }

    throw new Error(message);
  }

  return response.json();
}

function setStatus(message = "", tone = "info") {
  const banner = document.getElementById("statusBanner");

  if (!message) {
    banner.className = "status-banner";
    banner.textContent = "";
    return;
  }

  banner.className = `status-banner visible ${tone}`;
  banner.textContent = message;
}

function buildSyncStatusMessage(keyword, payload) {
  const parts = [
    `Found ${payload.local_match_count} local matches for "${keyword}".`,
    `Fetched ${payload.fetched_count} live patents.`,
    `Inserted ${payload.inserted_count} new records.`,
  ];

  if (payload.skipped_count) {
    parts.push(`Skipped ${payload.skipped_count} duplicates.`);
  }

  if (!payload.live_import_enabled) {
    parts.push("Live import is disabled until PATENTSVIEW_API_KEY is set to a real API key.");
  } else if (payload.live_import_enabled && payload.fetched_count === 0) {
    parts.push("No live patent matches were returned for that keyword.");
  }

  if (Array.isArray(payload.errors) && payload.errors.length > 0) {
    parts.push(`PatentsView note: ${payload.errors[0]}`);
  }

  return parts.join(" ");
}

function updateResultsHeader(title, meta = "") {
  document.getElementById("resultsHeading").textContent = title;
  document.getElementById("resultsMeta").textContent = meta || "Ready";
}

function setActiveFilter(activeButton) {
  document.querySelectorAll(".filter-chip").forEach(button => {
    button.classList.remove("active");
  });

  if (activeButton) {
    activeButton.classList.add("active");
  }
}

function showDetails(item, type) {
  const panel = document.getElementById("detailsPanel");
  panel.style.display = "block";

  if (type === "inventors") {
    panel.innerHTML = `
      <p class="eyebrow">Inventor Profile</p>
      <h2>${item.first_name} ${item.last_name}</h2>
      <p><strong>Affiliation:</strong> ${item.affiliation || "Not provided"}</p>
      <p><strong>Email:</strong> ${item.email || "Not provided"}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  } else if (type === "patents" || type === "search") {
    panel.innerHTML = `
      <p class="eyebrow">Patent Review</p>
      <h2>${item.title}</h2>
      <p><strong>Patent Number:</strong> ${item.patent_number || "Not available"}</p>
      <p><strong>Publication Number:</strong> ${item.publication_number || "Not available"}</p>
      <p><strong>Technology Domain:</strong> ${item.technology_domain || "General"}</p>
      <p><strong>Filing Date:</strong> ${item.filing_date || "Not available"}</p>
      <p><strong>Assignee:</strong> ${item.assignee || "Not provided"}</p>
      <p><strong>Source:</strong> ${item.source || "Database"}</p>
      <p><strong>Abstract:</strong> ${item.abstract || "No abstract available."}</p>
    `;
  } else if (type === "ranked") {
    panel.innerHTML = `
      <p class="eyebrow">Candidate Review</p>
      <h2>${item.inventor_name}</h2>
      <p><strong>Fit Score:</strong> ${item.fit_score}</p>
      <p><strong>Patent Count:</strong> ${item.patent_count}</p>
      <p><strong>Technology Domains:</strong> ${item.technology_domains.join(", ") || "General"}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  } else if (type === "discovered") {
    panel.innerHTML = `
      <p class="eyebrow">Discovered Inventor</p>
      <h2>${item.first_name} ${item.last_name}</h2>
      <p><strong>Affiliation:</strong> ${item.affiliation || "Not provided"}</p>
      <p><strong>Email:</strong> ${item.email || "Not provided"}</p>
      <p><strong>Matched Patent:</strong> ${item.patent_title}</p>
      <p><strong>Technology Domain:</strong> ${item.technology_domain || "General"}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  }

  panel.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearDetails() {
  const panel = document.getElementById("detailsPanel");
  panel.innerHTML = "";
  panel.style.display = "none";
}

function showTopCandidatesPlaceholder(message) {
  const topCandidatesDiv = document.getElementById("topCandidates");
  topCandidatesDiv.innerHTML = `
    <p class="eyebrow">Top Candidates</p>
    <h2>Candidate shortlist will appear here</h2>
    <p class="panel-helper">${message}</p>
  `;
}

function showEmptyWorkspaceState() {
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = `
    <div class="onboarding-state">
      <p class="eyebrow">Workspace Ready</p>
      <h3>No records yet</h3>
      <p>
        Your backend is connected, but the Supabase tables are currently empty. Start by searching for a keyword,
        syncing patents, or adding inventor and patent records in Supabase.
      </p>
      <div class="onboarding-actions">
        <button class="action-button" onclick="loadPatents()">View Patents</button>
        <button class="action-button" onclick="loadInventors()">View Inventors</button>
        <button class="action-button action-accent" onclick="importUsptoPatents()">Sync NJIT + Internet</button>
      </div>
    </div>
  `;
}

function createCard(item, type) {
  const card = document.createElement("article");
  card.className = "card";

  if (type === "inventors") {
    card.innerHTML = `
      <div class="meta-label">Inventor</div>
      <div class="card-header">
        <h3>${item.first_name} ${item.last_name}</h3>
      </div>
      <div class="card-subtitle">${item.affiliation || "Affiliation not provided"}</div>
      <div class="card-divider"></div>
      <p><strong>Email:</strong> ${item.email || "Not provided"}</p>
      <div class="tag-list">
        <span class="tag">ID ${item.inventor_id}</span>
      </div>
    `;
  } else if (type === "patents") {
    card.innerHTML = `
      <div class="meta-label">Patent</div>
      <div class="card-header">
        <h3>${item.title}</h3>
      </div>
      <div class="card-subtitle">${item.technology_domain || "General"} opportunity</div>
      <div class="card-divider"></div>
      <p><strong>Patent Number:</strong> ${item.patent_number || "Not available"}</p>
      <p><strong>Source:</strong> ${item.source || "Database"}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain || "General"}</span>
      </div>
    `;
  } else if (type === "ranked") {
    let scoreClass = "score-low";

    if (item.fit_score >= 9) {
      scoreClass = "score-high";
    } else if (item.fit_score >= 7) {
      scoreClass = "score-medium";
    }

    card.innerHTML = `
      <div class="meta-label">Candidate</div>
      <div class="card-header">
        <h3>${item.inventor_name}</h3>
        <span class="score-badge ${scoreClass}">Score ${item.fit_score}</span>
      </div>
      <div class="card-subtitle">Patent-based venture fit ranking</div>
      <div class="card-divider"></div>
      <p><strong>Patent Count:</strong> ${item.patent_count}</p>
      <div class="tag-list">
        ${(item.technology_domains || []).map(domain => `<span class="tag">${domain}</span>`).join("") || '<span class="tag">General</span>'}
      </div>
    `;
  } else if (type === "search") {
    card.innerHTML = `
      <div class="meta-label">Search Match</div>
      <div class="card-header">
        <h3>${item.title}</h3>
      </div>
      <div class="card-subtitle">${item.assignee || "Matched patent result"}</div>
      <div class="card-divider"></div>
      <p><strong>Patent Number:</strong> ${item.patent_number || "Not available"}</p>
      <p><strong>Source:</strong> ${item.source || "Database"}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain || "General"}</span>
      </div>
    `;
  } else if (type === "discovered") {
    card.innerHTML = `
      <div class="meta-label">Discovery</div>
      <div class="card-header">
        <h3>${item.first_name} ${item.last_name}</h3>
      </div>
      <div class="card-subtitle">${item.affiliation || "Affiliation not provided"}</div>
      <div class="card-divider"></div>
      <p><strong>Matched Patent:</strong> ${item.patent_title}</p>
      <p><strong>Email:</strong> ${item.email || "Not provided"}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain || "General"}</span>
      </div>
    `;
  }

  card.addEventListener("click", () => showDetails(item, type));
  return card;
}

function displayResults(data, type = "", title = "") {
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = "";

  if (title) {
    const heading = document.createElement("div");
    heading.className = "section-title";
    heading.textContent = title;
    resultsDiv.appendChild(heading);
  }

  if (!data.length) {
    resultsDiv.innerHTML += `
      <div class="empty-state">
        No results found for this view yet. Try a broader keyword, sync new patents, or switch to another dataset.
      </div>
    `;
    return;
  }

  data.forEach(item => {
    resultsDiv.appendChild(createCard(item, type));
  });
}

function setSummaryValue(id, value, footnoteId, footnote) {
  document.getElementById(id).textContent = value;

  if (footnoteId && footnote) {
    document.getElementById(footnoteId).textContent = footnote;
  }
}

async function loadSummary() {
  const [inventorsResult, patentsResult, rankedResult] = await Promise.allSettled([
    fetchJson("/inventors"),
    fetchJson("/patents"),
    fetchJson("/ranked-inventors")
  ]);

  let hadError = false;
  let patents = [];

  if (inventorsResult.status === "fulfilled") {
    setSummaryValue("totalInventors", inventorsResult.value.length, "inventorsFootnote", "Profiles in workspace");
  } else {
    hadError = true;
    console.error("Error loading inventor summary:", inventorsResult.reason);
    setSummaryValue("totalInventors", "--", "inventorsFootnote", "Inventor metrics unavailable");
  }

  if (patentsResult.status === "fulfilled") {
    patents = patentsResult.value;
    setSummaryValue("totalPatents", patents.length, "patentsFootnote", "Tracked opportunities");
  } else {
    hadError = true;
    console.error("Error loading patent summary:", patentsResult.reason);
    setSummaryValue("totalPatents", "--", "patentsFootnote", "Patent metrics unavailable");
  }

  if (rankedResult.status === "fulfilled") {
    const ranked = rankedResult.value;
    const topScore = ranked.length > 0 ? ranked[0].fit_score : 0;
    setSummaryValue("topScore", topScore, "scoreFootnote", "Highest inventor rank");
  } else {
    hadError = true;
    console.error("Error loading ranked summary:", rankedResult.reason);
    setSummaryValue("topScore", "--", "scoreFootnote", "Ranking metrics unavailable");
  }

  if (patentsResult.status === "fulfilled") {
    const aiPatents = patents.filter(
      patent => patent.technology_domain && patent.technology_domain.toLowerCase().includes("ai")
    ).length;
    setSummaryValue("aiPatents", aiPatents, "aiPatentsFootnote", "Strategic portfolio count");
  } else {
    setSummaryValue("aiPatents", "--", "aiPatentsFootnote", "AI patent metric unavailable");
  }

  if (hadError) {
    setStatus("Some dashboard metrics could not be loaded. Check that the backend is running and Supabase data is available.", "error");
    return;
  }

  const inventorCount = inventorsResult.status === "fulfilled" ? inventorsResult.value.length : 0;
  const patentCount = patentsResult.status === "fulfilled" ? patentsResult.value.length : 0;
  const rankedCount = rankedResult.status === "fulfilled" ? rankedResult.value.length : 0;

  if (inventorCount === 0 && patentCount === 0 && rankedCount === 0) {
    showTopCandidatesPlaceholder("Run a search or sync patents to generate ranked candidates.");
    showEmptyWorkspaceState();
    updateResultsHeader("Workspace ready for first data load", "No records in Supabase yet");
    setStatus("Connected successfully. Your Supabase tables are empty, so the workspace is ready for the first import.", "info");
  }
}

async function loadInventors() {
  showTopCandidatesPlaceholder("Load ranked inventors after importing data to populate this shortlist.");
  clearDetails();
  setStatus("Loading inventor profiles...", "info");

  try {
    const data = await fetchJson("/inventors");
    updateResultsHeader("Inventor Directory", `${data.length} inventor profiles`);
    displayResults(data, "inventors", "Inventors");
    setStatus(`Loaded ${data.length} inventor profiles.`, "success");
  } catch (error) {
    console.error("Error loading inventors:", error);
    setStatus("Failed to load inventor profiles.", "error");
  }
}

async function loadPatents() {
  showTopCandidatesPlaceholder("Sync or rank data to surface top candidates here.");
  clearDetails();
  setStatus("Loading patent portfolio...", "info");

  try {
    const data = await fetchJson("/patents");
    updateResultsHeader("Patent Portfolio", `${data.length} patents in workspace`);
    displayResults(data, "patents", "Patents");
    setStatus(`Loaded ${data.length} patent records.`, "success");
  } catch (error) {
    console.error("Error loading patents:", error);
    setStatus("Failed to load patents.", "error");
  }
}

async function loadRankedInventors() {
  clearDetails();
  setStatus("Scoring inventor candidates...", "info");

  try {
    const data = await fetchJson("/ranked-inventors");

    const topCandidatesDiv = document.getElementById("topCandidates");

    if (data.length > 0) {
      let topHtml = `
        <p class="eyebrow">Top Candidates</p>
        <h2>Highest-fit inventor shortlist</h2>
        <ul>
      `;

      data.slice(0, 3).forEach((candidate, index) => {
        topHtml += `<li><strong>${index + 1}. ${candidate.inventor_name}</strong> - Score ${candidate.fit_score}</li>`;
      });

      topHtml += "</ul>";
      topCandidatesDiv.innerHTML = topHtml;
    } else {
      topCandidatesDiv.innerHTML = "";
    }

    updateResultsHeader("Ranked Inventors", `${data.length} scored candidates`);
    displayResults(data, "ranked", "Ranked Inventors");
    setStatus(`Calculated fit scores for ${data.length} inventor candidates.`, "success");
  } catch (error) {
    console.error("Error loading ranked inventors:", error);
    setStatus("Failed to load ranked inventors.", "error");
  }
}

async function searchPatents() {
  showTopCandidatesPlaceholder("Search results are loaded below. Rank candidates after patents are linked to inventors.");
  clearDetails();
  const keyword = document.getElementById("searchInput").value.trim();

  if (!keyword) {
    setStatus("Enter a keyword to start a search.", "error");
    return;
  }

  setStatus(`Searching and syncing patents for "${keyword}"...`, "info");

  try {
    const payload = await fetchJson(`/search?keyword=${encodeURIComponent(keyword)}&auto_sync=true`);
    const results = payload.local_matches || [];

    updateResultsHeader(`Search Results for "${keyword}"`, `${results.length} matched patents`);
    displayResults(results, "search", `Search Results for "${keyword}"`);
    setStatus(buildSyncStatusMessage(keyword, payload), payload.errors?.length ? "info" : "success");
    await loadSummary();
  } catch (error) {
    console.error("Error searching patents:", error);
    setStatus(error.message || `Search failed for "${keyword}".`, "error");
  }
}

async function filterByDomain(domain, button = null) {
  showTopCandidatesPlaceholder(`Showing ${domain} patent results below. Candidate rankings appear after inventor links are available.`);
  clearDetails();
  setActiveFilter(button);
  setStatus(`Filtering patents for ${domain}...`, "info");

  try {
    const data = await fetchJson(`/filter?domain=${encodeURIComponent(domain)}`);
    updateResultsHeader(`${domain} Patent View`, `${data.length} patents`);
    displayResults(data, "patents", `${domain} Patents`);
    setStatus(`Showing ${data.length} patents for ${domain}.`, "success");
  } catch (error) {
    console.error("Error filtering patents:", error);
    setStatus(error.message || `Failed to filter patents for ${domain}.`, "error");
  }
}

async function discoverInventors() {
  showTopCandidatesPlaceholder("Discovered inventors will help populate the candidate shortlist.");
  clearDetails();

  const keyword = document.getElementById("searchInput").value.trim();

  if (!keyword) {
    setStatus("Enter a keyword before discovering inventors.", "error");
    return;
  }

  setStatus(`Syncing patents and discovering inventors for "${keyword}"...`, "info");

  try {
    await fetchJson(`/sync-patents?keyword=${encodeURIComponent(keyword)}`, {
      method: "POST"
    });

    const data = await fetchJson(`/discover-inventors?keyword=${encodeURIComponent(keyword)}`);
    updateResultsHeader(`Inventor Discovery for "${keyword}"`, `${data.length} inventor matches`);
    displayResults(data, "discovered", `Inventors Discovered for "${keyword}"`);
    setStatus(`Discovered ${data.length} inventors for "${keyword}".`, "success");
    await loadSummary();
  } catch (error) {
    console.error("Error discovering inventors:", error);
    setStatus(error.message || `Failed to discover inventors for "${keyword}".`, "error");
  }
}

function resetView() {
  document.getElementById("searchInput").value = "";
  showTopCandidatesPlaceholder("Run a search or sync patents to generate ranked candidates.");
  showEmptyWorkspaceState();
  updateResultsHeader("Start with a search or choose a view", "Workspace reset");
  clearDetails();
  setStatus("Workspace reset. Ready for a new search.", "info");
  setActiveFilter(document.querySelector('.filter-chip[data-domain="All"]'));
  loadSummary();
}

async function importUsptoPatents() {
  const keyword = document.getElementById("searchInput").value.trim();

  if (!keyword) {
    setStatus("Enter a keyword first to sync patents.", "error");
    return;
  }

  setStatus(`Syncing NJIT and internet patents for "${keyword}"...`, "info");

  try {
    const data = await fetchJson(`/sync-patents?keyword=${encodeURIComponent(keyword)}`, {
      method: "POST"
    });

    setStatus(buildSyncStatusMessage(keyword, data), data.errors?.length ? "info" : "success");
    await loadSummary();
    await loadPatents();
  } catch (error) {
    console.error("Error syncing patents:", error);
    setStatus(error.message || "Failed to sync patents.", "error");
  }
}

window.onload = () => {
  resetView();
};
