const API_BASE = "http://127.0.0.1:8000";

function showSectionTitle(title) {
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = `<div class="section-title">${title}</div>`;
}

function showDetails(item, type) {
  const panel = document.getElementById("detailsPanel");
  panel.style.display = "block";

  if (type === "inventors") {
    panel.innerHTML = `
      <h2>Inventor Details</h2>
      <p><strong>Name:</strong> ${item.first_name} ${item.last_name}</p>
      <p><strong>Affiliation:</strong> ${item.affiliation}</p>
      <p><strong>Email:</strong> ${item.email}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  } 
  
  else if (type === "patents" || type === "search") {
    panel.innerHTML = `
      <h2>Patent Details</h2>
      <p><strong>Title:</strong> ${item.title}</p>
      <p><strong>Patent Number:</strong> ${item.patent_number}</p>
      <p><strong>Filing Date:</strong> ${item.filing_date}</p>
      <p><strong>Technology Domain:</strong> ${item.technology_domain}</p>
      <p><strong>Patent ID:</strong> ${item.patent_id}</p>
    `;
  } 
  
  else if (type === "ranked") {
    panel.innerHTML = `
      <h2>Ranked Inventor Details</h2>
      <p><strong>Name:</strong> ${item.inventor_name}</p>
      <p><strong>Patent Count:</strong> ${item.patent_count}</p>
      <p><strong>Technology Domains:</strong> ${item.technology_domains.join(", ")}</p>
      <p><strong>Fit Score:</strong> ${item.fit_score}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  } 
  
  else if (type === "discovered") {
    panel.innerHTML = `
      <h2>Discovered Inventor Details</h2>
      <p><strong>Name:</strong> ${item.first_name} ${item.last_name}</p>
      <p><strong>Affiliation:</strong> ${item.affiliation}</p>
      <p><strong>Email:</strong> ${item.email}</p>
      <p><strong>Patent:</strong> ${item.patent_title}</p>
      <p><strong>Technology Domain:</strong> ${item.technology_domain}</p>
      <p><strong>Inventor ID:</strong> ${item.inventor_id}</p>
    `;
  }
}

function clearDetails() {
  const panel = document.getElementById("detailsPanel");
  panel.innerHTML = "";
  panel.style.display = "none";
}

function createCard(item, type) {
  const card = document.createElement("div");
  card.className = "card";

  if (type === "inventors") {
    card.innerHTML = `
      <div class="meta-label">Inventor</div>
      <div class="card-header">
        <h3>${item.first_name} ${item.last_name}</h3>
      </div>
      <div class="card-subtitle">${item.affiliation}</div>
      <div class="card-divider"></div>
      <p><strong>Email:</strong> ${item.email}</p>
      <div class="tag-list">
        <span class="tag">ID: ${item.inventor_id}</span>
      </div>
    `;
  }

  else if (type === "patents") {
    card.innerHTML = `
      <div class="meta-label">Patent</div>
      <div class="card-header">
        <h3>${item.title}</h3>
      </div>
      <div class="card-subtitle">${item.technology_domain}</div>
      <div class="card-divider"></div>
      <p><strong>Patent Number:</strong> ${item.patent_number}</p>
      <p><strong>Filing Date:</strong> ${item.filing_date}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain}</span>
      </div>
    `;
  }

  else if (type === "ranked") {
    let scoreClass = "score-low";

    if (item.fit_score >= 9) {
      scoreClass = "score-high";
    } else if (item.fit_score >= 7) {
      scoreClass = "score-medium";
    }

    card.innerHTML = `
      <div class="meta-label">Top Candidate</div>
      <div class="card-header">
        <h3>${item.inventor_name}</h3>
        <span class="score-badge ${scoreClass}">Score: ${item.fit_score}</span>
      </div>
      <div class="card-subtitle">Patent-based inventor ranking</div>
      <div class="card-divider"></div>
      <p><strong>Patent Count:</strong> ${item.patent_count}</p>
      <div class="tag-list">
        ${item.technology_domains.map(domain => `<span class="tag">${domain}</span>`).join("")}
      </div>
    `;
  }

  else if (type === "search") {
    card.innerHTML = `
      <div class="meta-label">Search Result</div>
      <div class="card-header">
        <h3>${item.title}</h3>
      </div>
      <div class="card-subtitle">Matched patent result</div>
      <div class="card-divider"></div>
      <p><strong>Patent Number:</strong> ${item.patent_number}</p>
      <p><strong>Filing Date:</strong> ${item.filing_date}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain}</span>
      </div>
    `;
  }

  else if (type === "discovered") {
    card.innerHTML = `
      <div class="meta-label">Discovered Inventor</div>
      <div class="card-header">
        <h3>${item.first_name} ${item.last_name}</h3>
      </div>
      <div class="card-subtitle">${item.affiliation}</div>
      <div class="card-divider"></div>
      <p><strong>Email:</strong> ${item.email}</p>
      <p><strong>Patent:</strong> ${item.patent_title}</p>
      <div class="tag-list">
        <span class="tag">${item.technology_domain}</span>
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

  if (data.length === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No results found.";
    resultsDiv.appendChild(empty);
    return;
  }

  data.forEach(item => {
    const card = createCard(item, type);
    resultsDiv.appendChild(card);
  });
}

async function loadSummary() {
  try {
    const [inventorsRes, patentsRes, rankedRes] = await Promise.all([
      fetch(`${API_BASE}/inventors`),
      fetch(`${API_BASE}/patents`),
      fetch(`${API_BASE}/ranked-inventors`)
    ]);

    const inventors = await inventorsRes.json();
    const patents = await patentsRes.json();
    const ranked = await rankedRes.json();

    const totalInventors = inventors.length;
    const totalPatents = patents.length;
    const topScore = ranked.length > 0 ? ranked[0].fit_score : 0;
    const aiPatents = patents.filter(
      patent => patent.technology_domain && patent.technology_domain.toLowerCase().includes("ai")
    ).length;

    document.getElementById("totalInventors").textContent = totalInventors;
    document.getElementById("totalPatents").textContent = totalPatents;
    document.getElementById("topScore").textContent = topScore;
    document.getElementById("aiPatents").textContent = aiPatents;
  } catch (error) {
    console.error("Error loading summary:", error);
  }
}

async function loadInventors() {
  document.getElementById("topCandidates").innerHTML = "";
  clearDetails();
  const response = await fetch(`${API_BASE}/inventors`);
  const data = await response.json();
  displayResults(data, "inventors", "Inventors");
}

async function loadPatents() {
  document.getElementById("topCandidates").innerHTML = "";
  clearDetails();
  const response = await fetch(`${API_BASE}/patents`);
  const data = await response.json();
  displayResults(data, "patents", "Patents");
}

async function loadRankedInventors() {
  clearDetails();
  const response = await fetch(`${API_BASE}/ranked-inventors`);
  const data = await response.json();

  const topCandidatesDiv = document.getElementById("topCandidates");

  if (data.length > 0) {
    let topHtml = "<h2>Top Candidates</h2><ul>";

    data.slice(0, 3).forEach((candidate, index) => {
      topHtml += `<li><strong>${index + 1}. ${candidate.inventor_name}</strong> — Score: ${candidate.fit_score}</li>`;
    });

    topHtml += "</ul>";
    topCandidatesDiv.innerHTML = topHtml;
  } else {
    topCandidatesDiv.innerHTML = "";
  }

  displayResults(data, "ranked", "Ranked Inventors");
}

async function searchPatents() {
  document.getElementById("topCandidates").innerHTML = "";
  clearDetails();
  const keyword = document.getElementById("searchInput").value;
  const response = await fetch(`${API_BASE}/search?keyword=${encodeURIComponent(keyword)}`);
  const data = await response.json();
  displayResults(data, "search", `Search Results for "${keyword}"`);
}

async function filterByDomain(domain) {
  document.getElementById("topCandidates").innerHTML = "";
  clearDetails();
  const response = await fetch(`${API_BASE}/filter?domain=${encodeURIComponent(domain)}`);
  const data = await response.json();
  displayResults(data, "patents", `${domain} Patents`);
}

async function discoverInventors() {
  document.getElementById("topCandidates").innerHTML = "";
  clearDetails();

  const keyword = document.getElementById("searchInput").value;

  if (!keyword) {
    alert("Please enter a keyword first.");
    return;
  }

  const response = await fetch(`${API_BASE}/discover-inventors?keyword=${encodeURIComponent(keyword)}`);
  const data = await response.json();
  displayResults(data, "discovered", `Inventors Discovered for "${keyword}"`);
}

function resetView() {
  document.getElementById("searchInput").value = "";
  document.getElementById("topCandidates").innerHTML = "";
  document.getElementById("results").innerHTML = "";
  clearDetails();
  loadSummary();
}

async function importUsptoPatents() {
  const keyword = document.getElementById("searchInput").value.trim();

  if (!keyword) {
    alert("Please enter a keyword first to import patents.");
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/ingest-uspto?keyword=${encodeURIComponent(keyword)}`, {
      method: "POST"
    });

    const data = await response.json();

    alert(data.message);

    loadSummary();

    loadPatents();
  } catch (error) {
    console.error("Error importing USPTO patents:", error);
    alert("Failed to import USPTO patents.");
  }
}

window.onload = loadSummary;

