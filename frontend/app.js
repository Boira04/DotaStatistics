const API_URL = "http://127.0.0.1:8000";
let globalRolesData = {}; // Guardarem aquí les dades per no fer la petició cada cop
let roleChartInstance = null; // Guardem la instància del gràfic per poder destruir-lo i recrear-lo

// --- AUTHENTICATION ---
async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById("loginUser").value;
    const password = document.getElementById("loginPass").value;

    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", data.user.username);
            window.location.href = "dashboard.html";
        } else {
            showAlert(data.detail || "Login failed");
        }
    } catch (error) { showAlert("Backend is offline"); }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById("regUser").value;
    const email = document.getElementById("regEmail").value;
    const full_name = document.getElementById("regName").value;
    const password = document.getElementById("regPass").value;

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, full_name, password })
        });
        if (response.ok) {
            alert("Registered! Please login.");
            document.getElementById("tab-login").click();
        } else {
            const data = await response.json();
            showAlert(data.detail || "Registration failed");
        }
    } catch (error) { showAlert("Connection error"); }
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "index.html";
}

function checkAuth() {
    if (!localStorage.getItem("token")) window.location.href = "index.html";
    const userDisplay = document.getElementById("usernameDisplay");
    if(userDisplay) userDisplay.textContent = localStorage.getItem("username");
}

function showAlert(msg) {
    const el = document.getElementById("alertMsg");
    if(el) { el.innerText = msg; el.style.display = "block"; }
    else alert(msg);
}

// --- DATA FETCHING ---
async function fetchAuth(endpoint) {
    const token = localStorage.getItem("token");
    const response = await fetch(`${API_URL}${endpoint}`, {
        headers: { "Authorization": `Bearer ${token}` }
    });
    if (response.status === 401) logout();
    return response.json();
}

// --- MAIN LOADER ---
async function loadDashboardData() {
    console.log("🚀 Loading Dashboard Data...");
    try {
        // ... (Map, Table, Scatter, Roles, Dominance es mantenen igual) ...
        
        // 1. Map
        const mapData = await fetchAuth("/analytics/map/distribution");
        initMap(mapData);

        // 2. Table
        const densityData = await fetchAuth("/analytics/density/rankings?limit=10");
        const tableBody = document.getElementById("densityTableBody");
        tableBody.innerHTML = "";
        densityData.forEach((row, index) => {
            tableBody.innerHTML += `<tr>
                <td class="text-muted">${index + 1}</td>
                <td><span class="table-country-badge">${row.country}</span></td>
                <td class="text-info">${row.players}</td>
                <td>${(row.population / 1000000).toFixed(2)} M</td>
                <td class="text-warning">${row.density_per_million.toFixed(2)}</td>
            </tr>`;
        });

        // 3. Scatter Plots
        renderScatterChart("wealthChart", "/analytics/correlation/wealth", "GDP ($)", "gdp_per_capita", "#ff6384");
        renderScatterChart("internetChart", "/analytics/correlation/internet", "Internet Access (%)", "internet_access_percent", "#36a2eb");

        // 4. Roles
        globalRolesData = await fetchAuth("/analytics/regions/roles");
        const regionSelector = document.getElementById("regionRoleSelector");
        regionSelector.innerHTML = "";
        const regions = Object.keys(globalRolesData);
        regions.forEach(region => {
            const option = document.createElement("option");
            option.value = region;
            option.text = region;
            if(region === "Europe") option.selected = true;
            regionSelector.appendChild(option);
        });
        const initialRegion = regions.includes("Europe") ? "Europe" : regions[0];
        updateRoleChart(initialRegion);
        regionSelector.addEventListener("change", (e) => updateRoleChart(e.target.value));

        // 5. Dominance
        const domData = await fetchAuth("/analytics/regions/dominance");
        renderBarChart("dominanceChart", domData);

        // -----------------------------------------------------
        // 6. MARKET GAPS (NOU CODI VISUAL) 🚀
        // -----------------------------------------------------
        const gapsData = await fetchAuth("/analytics/insights/market-gaps");
        const gapsContainer = document.getElementById("marketGapsContainer");
        gapsContainer.innerHTML = "";
        
        gapsData.forEach(gap => {
            gapsContainer.innerHTML += `
                <div class="gap-card">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="mb-0 text-white">${gap.country}</h5>
                        <span class="badge bg-success text-dark">HIGH POTENTIAL</span>
                    </div>
                    
                    <div class="row mt-3">
                        <div class="col-6">
                            <div class="gap-stat-label">Market Size (Pop)</div>
                            <div class="gap-stat-value text-light">${(gap.population/1000000).toFixed(1)} M</div>
                        </div>
                        <div class="col-6 text-end">
                            <div class="gap-stat-label">Current Talent</div>
                            <div class="gap-stat-value text-danger">0 Active Players</div>
                        </div>
                    </div>
                    
                    <div class="mt-2 pt-2 border-top border-secondary">
                        <small class="text-muted">Region: ${gap.region}</small>
                    </div>
                </div>
            `;
        });

    } catch (error) {
        console.error("Error loading dashboard:", error);
    }
}

// --- SEARCH ---
async function searchCountryStats() {
    const input = document.getElementById("countryInput").value;
    const resultDiv = document.getElementById("countryResult");
    const errorDiv = document.getElementById("countryError");
    
    if (!input) return;

    try {
        const data = await fetchAuth(`/analytics/country/${input}/youth-correlation`);
        if (data.detail) throw new Error("Not found");

        document.getElementById("resCountryName").innerText = `${data.country} (${data.country_code})`;
        document.getElementById("resPop").innerText = (data.demographics.total_population / 1000000).toFixed(2) + " M";
        document.getElementById("resYouth").innerText = data.demographics.young_population_percent + "%";
        document.getElementById("resPlayers").innerText = data.pro_players.total_count;
        document.getElementById("resDensity").innerText = data.correlation_insight.interpretation.split(" ")[0] + " Density"; 
        document.getElementById("resInsight").innerText = `"${data.correlation_insight.player_youth_ratio}"`;

        resultDiv.classList.remove("d-none");
        errorDiv.classList.add("d-none");
    } catch (error) {
        resultDiv.classList.add("d-none");
        errorDiv.classList.remove("d-none");
    }
}

// --- CHART HELPERS ---

function updateRoleChart(regionName) {
    const regionData = globalRolesData[regionName].roles; // { "Carry": 10, "Support": 5 ...}
    const canvas = document.getElementById("roleChart");
    
    // Destroy previous instance if exists
    if (roleChartInstance) {
        roleChartInstance.destroy();
    }

    // Create new chart
    roleChartInstance = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: Object.keys(regionData),
            datasets: [{
                data: Object.values(regionData),
                backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff'], // Consistent colors
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'right', labels: { color: '#f0f6fc', font: {size: 11} } },
                title: { display: false }
            },
            cutout: '60%'
        }
    });
}

function initMap(data) {
    // Si el mapa ja està inicialitzat (per evitar errors al recarregar), l'esborrem primer
    const container = L.DomUtil.get('map');
    if(container != null){ container._leaflet_id = null; }

    const map = L.map('map').setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO'
    }).addTo(map);

    data.forEach(p => {
        if(p.coordinates && p.coordinates.length === 2) {
            L.circleMarker(p.coordinates, {
                radius: 3,
                fillColor: "#ff4d4d", // Vermell brillant
                color: "transparent",
                weight: 0,
                fillOpacity: 0.9
            }).bindPopup(`<b>${p.name}</b><br>${p.country}`).addTo(map);
        }
    });
}

async function renderScatterChart(canvasId, endpoint, xLabel, xKey, color) {
    const data = await fetchAuth(endpoint);
    const scatterPoints = data.map(item => ({
        x: item[xKey],
        y: item.players_per_million,
        country: item.country
    }));

    new Chart(document.getElementById(canvasId), {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Countries',
                data: scatterPoints,
                backgroundColor: color,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    backgroundColor: '#161b22',
                    titleColor: '#fff',
                    bodyColor: '#ccc',
                    callbacks: {
                        label: function(ctx) {
                            return `${ctx.raw.country}: ${ctx.raw.y.toFixed(2)} density`;
                        }
                    }
                },
                legend: { display: false }
            },
            scales: {
                x: { 
                    title: { display: true, text: xLabel, color: '#8b949e' }, 
                    grid: { color: '#30363d' },
                    ticks: { color: '#8b949e' }
                },
                y: { 
                    title: { display: true, text: 'Players / Million', color: '#8b949e' }, 
                    grid: { color: '#30363d' },
                    ticks: { color: '#8b949e' }
                }
            }
        }
    });
}

function renderBarChart(canvasId, data) {
    const labels = data.slice(0, 10).map(d => d._id);
    const values = data.slice(0, 10).map(d => d.total_players);

    new Chart(document.getElementById(canvasId), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Total Pro Players',
                data: values,
                backgroundColor: '#eebb00', // Gold color
                borderRadius: 3
            }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: '#30363d' }, ticks: { color: '#8b949e' } },
                y: { grid: { display: false }, ticks: { color: '#f0f6fc' } }
            }
        }
    });
}