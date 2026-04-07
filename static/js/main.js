document.addEventListener('DOMContentLoaded', () => {

    // --- Navigation Logic ---
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active states
            navItems.forEach(n => n.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            // Add active to clicked target
            btn.classList.add('active');
            const target = btn.getAttribute('data-target');
            document.getElementById(target).classList.add('active');

            // Refresh Dashboard if clicked
            if (target === 'dashboard') {
                loadDashboardData();
            }
        });
    });

    // --- Initial Load ---
    loadDashboardData();

    // Chart variables to prevent memory leaks during redraws
    let pieChartInstance = null;
    let barChartInstance = null;

    // --- Dashboard Data Loading ---
    async function loadDashboardData() {
        try {
            const res = await fetch('/dashboard-data');
            if (!res.ok) {
                // Not an error per se, could just be empty DB
                return;
            }
            const data = await res.json();
            
            // Stats
            document.getElementById('totalRecords').textContent = data.total_students;
            document.getElementById('avgScore').textContent = `${data.avg_score}%`;

            // Draw Charts
            drawPieChart(data.category_distribution);
            drawBarChart(data.avg_marks);

            // Render Table
            renderLeaderboard(data.top_performers);
        } catch (e) {
            console.error('Error loading dashboard data:', e);
        }
    }

    function drawPieChart(distribution) {
        const ctx = document.getElementById('categoryPieChart').getContext('2d');
        if (pieChartInstance) pieChartInstance.destroy();

        // Defaults
        Chart.defaults.color = 'rgba(255, 255, 255, 0.7)';
        Chart.defaults.font.family = "'Inter', sans-serif";

        pieChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['High', 'Average', 'Low'],
                datasets: [{
                    data: [distribution.High || 0, distribution.Average || 0, distribution.Low || 0],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)', // Green
                        'rgba(245, 158, 11, 0.8)', // Yellow
                        'rgba(239, 68, 68, 0.8)'   // Red
                    ],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    function drawBarChart(marks) {
        const ctx = document.getElementById('avgSubjectBarChart').getContext('2d');
        if (barChartInstance) barChartInstance.destroy();

        barChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Math', 'Science', 'English'],
                datasets: [{
                    label: 'Aggregate Average Score',
                    data: [marks.Math, marks.Science, marks.English],
                    backgroundColor: [
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(236, 72, 153, 0.7)',
                        'rgba(56, 189, 248, 0.7)'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    function renderLeaderboard(performers) {
        const tbody = document.getElementById('leaderboardBody');
        tbody.innerHTML = '';

        if (!performers || performers.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No records available</td></tr>`;
            return;
        }

        performers.forEach((p, idx) => {
            const tr = document.createElement('tr');
            if(idx === 0) tr.classList.add('highlight-row'); // top 1 highlight
            
            tr.innerHTML = `
                <td>${p.name}</td>
                <td><strong>${p.predicted_score}</strong></td>
                <td><span class="badge ${p.performance_category}">${p.performance_category}</span></td>
                <td>${p.weakest_subject}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // --- Single Prediction UI ---
    const predictionForm = document.getElementById('predictionForm');
    
    predictionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btnText = document.querySelector('#submitBtn .btn-text');
        const loader = document.getElementById('singleLoader');
        const errBox = document.getElementById('singleErrorBox');
        
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        errBox.classList.add('hidden');
        document.getElementById('submitBtn').disabled = true;

        const payload = {
            name: document.getElementById('studentName').value,
            math: document.getElementById('math').value,
            science: document.getElementById('science').value,
            english: document.getElementById('english').value,
            attendance: document.getElementById('attendance').value,
            studyHours: document.getElementById('studyHours').value
        };

        try {
            const res = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server Error');

            // Show result
            const resBox = document.getElementById('singleResultBox');
            resBox.classList.remove('hidden');
            
            document.getElementById('resName').textContent = data.name;
            document.getElementById('resScore').textContent = data.predicted_score;
            
            const badge = document.getElementById('resBadge');
            badge.textContent = data.performance;
            badge.className = `badge ${data.performance} mt-1`;

            const sugList = document.getElementById('resSuggestionsList');
            sugList.innerHTML = '';
            data.suggestions.forEach(s => {
                const li = document.createElement('li');
                li.textContent = s;
                sugList.appendChild(li);
            });
            
            // optionally refresh dashboard in background
            loadDashboardData();

        } catch (e) {
            errBox.textContent = e.message;
            errBox.classList.remove('hidden');
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            document.getElementById('submitBtn').disabled = false;
        }
    });

    // --- Bulk Upload UI ---
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('csvFile');
    const dropZone = document.getElementById('dropZone');
    const uploadBtn = document.getElementById('uploadBtn');
    const selectedFileName = document.getElementById('selectedFileName');

    // Drag & Drop logic
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if(files.length > 0) {
            // Check if it's a CSV
            if(files[0].name.endsWith('.csv')) {
                fileInput.files = files;
                updateFileDisplay();
            } else {
                alert("Please drop a valid .csv file");
            }
        }
    });

    fileInput.addEventListener('change', updateFileDisplay);

    function updateFileDisplay() {
        if (fileInput.files.length > 0) {
            selectedFileName.textContent = "Selected: " + fileInput.files[0].name;
            uploadBtn.disabled = false;
            uploadBtn.style.opacity = '1';
            uploadBtn.style.cursor = 'pointer';
        } else {
            selectedFileName.textContent = '';
            uploadBtn.disabled = true;
            uploadBtn.style.opacity = '0.5';
            uploadBtn.style.cursor = 'not-allowed';
        }
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const btnText = document.querySelector('#uploadBtn .btn-text');
        const loader = document.getElementById('uploadLoader');
        const feedback = document.getElementById('uploadFeedback');
        
        if (fileInput.files.length === 0) return;

        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        feedback.classList.add('hidden');
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Server Error');

            feedback.textContent = data.message;
            feedback.className = 'success-msg mt-2';
            feedback.classList.remove('hidden');

            const resultsContainer = document.getElementById('uploadResultsContainer');
            const resultsBody = document.getElementById('uploadResultsBody');
            
            if (data.results && data.results.length > 0) {
                resultsBody.innerHTML = '';
                data.results.forEach(p => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${p.name}</td>
                        <td><strong>${p.predicted_score}</strong></td>
                        <td><span class="badge ${p.performance}">${p.performance}</span></td>
                        <td>${p.weakest_subject}</td>
                    `;
                    resultsBody.appendChild(tr);
                });
                resultsContainer.classList.remove('hidden');
            }

            loadDashboardData(); // Refetch db states
        } catch (e) {
            feedback.textContent = e.message;
            feedback.className = 'error-msg mt-2';
            feedback.classList.remove('hidden');
            document.getElementById('uploadResultsContainer').classList.add('hidden');
        } finally {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            uploadForm.reset();
            updateFileDisplay();
        }
    });

});
