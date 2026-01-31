const API_URL = "http://127.0.0.1:8000";

// Simple client-side language detection
function detectLanguage(code) {
    if (!code || code.trim().length < 20) return null;

    const patterns = {
        python: [
            /\bdef\s+\w+\s*\(/,
            /\bimport\s+\w+/,
            /\bfrom\s+\w+\s+import/,
            /\bprint\s*\(/,
            /\bif\s+.*:\s*$/m,
            /\belif\s+/,
            /\bfor\s+\w+\s+in\s+/
        ],
        javascript: [
            /\bfunction\s+\w+\s*\(/,
            /\bconst\s+\w+\s*=/,
            /\blet\s+\w+\s*=/,
            /\bconsole\.log\s*\(/,
            /=>\s*{/,
            /\bvar\s+\w+\s*=/,
            /\bdocument\./
        ],
        java: [
            /\bpublic\s+class\s+/,
            /\bprivate\s+\w+\s+\w+/,
            /\bSystem\.out\.print/,
            /\bpublic\s+static\s+void\s+main/,
            /\bString\[\]\s+args/
        ],
        c: [
            /\b#include\s*<\w+\.h>/,
            /\bint\s+main\s*\(/,
            /\bprintf\s*\(/,
            /\bscanf\s*\(/,
            /\breturn\s+0;/
        ],
        cpp: [
            /\b#include\s*<iostream>/,
            /\bstd::/,
            /\bcout\s*<</,
            /\bcin\s*>>/,
            /\bnamespace\s+std/
        ],
        go: [
            /\bfunc\s+\w+\s*\(/,
            /\bpackage\s+main/,
            /\bfmt\.Print/,
            /\bfunc\s+main\s*\(\s*\)/
        ],
        typescript: [
            /\binterface\s+\w+/,
            /:\s*\w+\s*=/,
            /\btype\s+\w+\s*=/,
            /\bexport\s+interface/
        ],
        r: [
            /\blibrary\s*\(/,
            /<-/,
            /\bfunction\s*\(/,
            /\bc\s*\(/
        ]
    };

    const scores = {};
    let maxScore = 0;

    for (const [lang, regexList] of Object.entries(patterns)) {
        scores[lang] = regexList.filter(regex => regex.test(code)).length;
        if (scores[lang] > maxScore) {
            maxScore = scores[lang];
        }
    }

    // Only return a language if we have at least 2 pattern matches
    if (maxScore < 2) return null;

    const detectedLang = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);
    return detectedLang;
}

let mismatchCheckTimeout = null;
function checkLanguageMismatch() {
    clearTimeout(mismatchCheckTimeout);
    mismatchCheckTimeout = setTimeout(() => {
        const code = document.getElementById('codeInput').value;
        const selectedLang = document.getElementById('languageSelect').value;
        const badge = document.getElementById('mismatchBadge');

        const detectedLang = detectLanguage(code);

        // Only show badge if we confidently detected a different language
        if (detectedLang && detectedLang !== selectedLang && detectedLang !== 'html' && detectedLang !== 'css') {
            badge.classList.remove('hidden');
            badge.title = `Code looks like ${detectedLang}`;
        } else {
            badge.classList.add('hidden');
        }
    }, 500); // Debounce for 500ms
}

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = [
        document.getElementById('reviewTab'),
        document.getElementById('refactoredTab'),
        document.getElementById('testsTab'),
        document.getElementById('docsTab')
    ];

    tabs.forEach(btn => {
        if (btn.dataset.tab === tabName) {
            btn.classList.add('border-brand-500', 'text-white');
            btn.classList.remove('border-transparent', 'text-gray-500');
        } else {
            btn.classList.remove('border-brand-500', 'text-white');
            btn.classList.add('border-transparent', 'text-gray-500');
        }
    });

    contents.forEach(content => content.classList.add('hidden'));
    document.getElementById(`${tabName}Tab`).classList.remove('hidden');
}

let currentMode = 'pro';

function setMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('bg-brand-600', 'text-white', 'shadow-sm');
            btn.classList.remove('text-gray-400', 'hover:text-white');
        } else {
            btn.classList.remove('bg-brand-600', 'text-white', 'shadow-sm');
            btn.classList.add('text-gray-400', 'hover:text-white');
        }
    });
}

async function copyToClipboard(elementId = 'codeOutput') {
    const code = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(code);
    const btn = document.querySelector(`button[onclick="copyToClipboard('${elementId}')"]`) || document.querySelector(`button[onclick="copyToClipboard()"]`);
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check text-green-400"></i>';
    setTimeout(() => { btn.innerHTML = originalHTML; }, 2000);
}

async function runCode() {
    const sourceCode = document.getElementById('codeInput').value;
    const language = document.getElementById('languageSelect').value;
    const inputs = document.getElementById('consoleInput').value;
    const outputEl = document.getElementById('consoleOutput');

    if (!sourceCode.trim()) {
        outputEl.innerText = "Error: No code to execute.";
        outputEl.classList.remove('text-green-400');
        outputEl.classList.add('text-red-400');
        return;
    }

    outputEl.innerText = "Running...";
    outputEl.classList.remove('text-red-400');
    outputEl.classList.add('text-green-400');

    try {
        const response = await fetch(`${API_URL}/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_code: sourceCode,
                language: language,
                inputs: inputs
            })
        });

        if (!response.ok) {
            throw new Error('Execution failed');
        }

        const data = await response.json();

        if (data.error) {
            outputEl.innerText = `Error:\n${data.error}`;
            outputEl.classList.remove('text-green-400');
            outputEl.classList.add('text-red-400');
        } else {
            outputEl.innerText = data.output || "(no output)";
            outputEl.classList.remove('text-red-400');
            outputEl.classList.add('text-green-400');
        }

    } catch (error) {
        console.error("Error:", error);
        outputEl.innerText = `Failed to execute code: ${error.message}`;
        outputEl.classList.remove('text-green-400');
        outputEl.classList.add('text-red-400');
    }
}

function clearConsole() {
    document.getElementById('consoleOutput').innerText = "Ready to execute...";
    document.getElementById('consoleOutput').classList.remove('text-red-400');
    document.getElementById('consoleOutput').classList.add('text-green-400');
}
async function analyzeCode() {
    const sourceCode = document.getElementById('codeInput').value;
    const language = document.getElementById('languageSelect').value;
    const btn = document.getElementById('analyzeBtn');
    const btnText = document.getElementById('btnText');

    if (!sourceCode.trim()) {
        alert("Please enter some code first.");
        return;
    }

    // Set Loading State
    btn.disabled = true;
    btnText.innerText = "Analyzing...";
    btn.classList.add('opacity-75');

    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_code: sourceCode,
                language: language,
                teaching_mode: currentMode
            })
        });

        if (!response.ok) {
            throw new Error('Analysis failed');
        }

        const data = await response.json();
        renderResults(data);

    } catch (error) {
        console.error("Error:", error);
        if (error.message === 'Analysis failed' || error.name === 'TypeError') {
            // It might be a network error if 'Analysis failed' was thrown manually, 
            // but TypeError usually means code bug.
            // Let's be more specific.
            if (error.message === 'Failed to fetch') {
                alert("Failed to connect to backend. Make sure Uvicorn is running on port 8000.");
            } else {
                alert(`An error occurred: ${error.message}`);
            }
        } else {
            alert("Failed to connect to backend. Make sure Uvicorn is running on port 8000.");
        }
    } finally {
        btn.disabled = false;
        btnText.innerText = "Refine Code";
        btn.classList.remove('opacity-75');
    }
}

function renderResults(data) {
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsContainer').classList.remove('hidden');

    // Language Mismatch Warning
    const warningEl = document.getElementById('langWarning');
    const warningText = document.getElementById('langWarningText');
    const selectedLang = document.getElementById('languageSelect').value;

    if (data.language_mismatch) {
        warningEl.classList.remove('hidden');
        warningText.innerText = `You selected ${selectedLang}, but the code looks like ${data.detected_language || 'something else'}.`;
    } else {
        warningEl.classList.add('hidden');
    }

    // Explanation
    document.getElementById('explanationBox').innerText = data.explanation;

    // Scores (We can keep qualityBadge if needed, but we focus on stats grid now)

    // Stats
    document.getElementById('complexityVal').innerText = data.estimated_time;
    document.getElementById('memoryVal').innerText = data.memory_estimate;
    document.getElementById('confidenceVal').innerText = Math.round(data.confidence_score_optimization);

    // Tips
    const tipsContainer = document.getElementById('tipsContainer');
    const tipsList = document.getElementById('tipsList');
    if (data.learning_tips && data.learning_tips.length > 0) {
        tipsContainer.classList.remove('hidden');
        tipsList.innerHTML = data.learning_tips.map(tip => `
            <li class="flex items-start gap-2">
                <i class="fa-solid fa-angle-right text-brand-400 mt-1 text-[10px]"></i>
                <span>${tip}</span>
            </li>
        `).join('');
    } else {
        tipsContainer.classList.add('hidden');
    }

    // Issues List
    const issuesList = document.getElementById('issuesList');
    issuesList.innerHTML = '';

    // ... existing filtering logic ...
    const filterIssues = (list) => list.filter(item =>
        !item.toLowerCase().includes("no issues") &&
        !item.toLowerCase().includes("none found") &&
        !item.toLowerCase().includes("no security vulnerabilities")
    );

    const allIssues = [
        ...filterIssues(data.bugs).map(b => ({ type: 'BUG', text: b, color: 'text-red-400', icon: 'fa-bug' })),
        ...filterIssues(data.security_vulnerabilities).map(s => ({ type: 'SEC', text: s, color: 'text-orange-400', icon: 'fa-shield-halved' })),
        ...filterIssues(data.performance_issues).map(p => ({ type: 'PERF', text: p, color: 'text-blue-400', icon: 'fa-gauge-high' })),
        ...filterIssues(data.best_practice_violations).map(v => ({ type: 'STYLE', text: v, color: 'text-gray-400', icon: 'fa-code' }))
    ];

    document.getElementById('issuesCount').innerText = allIssues.length;

    if (allIssues.length === 0) {
        issuesList.innerHTML = '<li class="text-sm text-green-400 flex items-center gap-2"><i class="fa-solid fa-check-circle"></i> No major issues found!</li>';
    } else {
        allIssues.forEach(issue => {
            const li = document.createElement('li');
            li.className = 'bg-dark-card/40 rounded-lg p-3 text-sm flex gap-3 items-start border border-white/5 hover:border-brand-500/30 hover:bg-dark-card/60 transition-all group';

            // Highlight "Line X:"
            const textWithHighlight = issue.text.replace(/^(Line \d+:?)/i, '<span class="font-mono font-bold text-brand-500 bg-brand-500/10 px-1 rounded mr-1">$1</span>');

            li.innerHTML = `
                <div class="mt-0.5 ${issue.color}"><i class="fa-solid ${issue.icon}"></i></div>
                <div class="text-gray-300 leading-snug">${textWithHighlight}</div>
            `;
            issuesList.appendChild(li);
        });
    }

    // Refactored Code
    document.getElementById('codeOutput').innerText = data.refactored_code;
    document.getElementById('testsOutput').innerText = data.generated_tests;
    document.getElementById('docsOutput').innerText = data.generated_docs;

    document.getElementById('testsOutput').innerText = data.generated_tests;
    document.getElementById('docsOutput').innerText = data.generated_docs;

    // Update Quality Score Circle
    updateQualityScore(data.quality_score);

    // Render Charts
    renderQualityChart(data.quality_metrics);

    // Store data for split view
    window.lastAnalysisData = {
        original: document.getElementById('codeInput').value,
        refactored: data.refactored_code
    };
}

function updateQualityScore(score) {
    const container = document.getElementById('qualityScoreContainer');
    const circle = document.getElementById('qualityScoreCircle');
    const text = document.getElementById('qualityScoreText');
    const label = document.getElementById('qualityScoreLabel');

    // Show the container
    container.classList.remove('hidden');

    // Update text
    text.innerText = score;

    // Calculate circle progress (circumference = 2 * PI * r = 2 * 3.14159 * 28 ≈ 176)
    const circumference = 176;
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDashoffset = offset;

    // Update color and label based on score
    if (score >= 80) {
        circle.setAttribute('stroke', '#4ade80'); // green
        label.innerText = 'Excellent';
        label.className = 'text-xs font-semibold text-green-400';
    } else if (score >= 60) {
        circle.setAttribute('stroke', '#fbbf24'); // yellow
        label.innerText = 'Good';
        label.className = 'text-xs font-semibold text-yellow-400';
    } else if (score >= 40) {
        circle.setAttribute('stroke', '#fb923c'); // orange
        label.innerText = 'Fair';
        label.className = 'text-xs font-semibold text-orange-400';
    } else {
        circle.setAttribute('stroke', '#f87171'); // red
        label.innerText = 'Needs Work';
        label.className = 'text-xs font-semibold text-red-400';
    }
}

let qualityChartInstance = null;

function renderQualityChart(metrics) {
    const chartCanvas = document.getElementById('qualityChart');
    if (!chartCanvas) {
        console.warn("Quality chart canvas not found.");
        return;
    }
    const ctx = chartCanvas.getContext('2d');

    if (qualityChartInstance) {
        qualityChartInstance.destroy();
    }

    // default metrics if missing
    if (!metrics || Object.keys(metrics).length === 0) {
        metrics = { maintainability: 0, security: 0, performance: 0, readability: 0 };
    }

    qualityChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Maintainability', 'Security', 'Performance', 'Readability'],
            datasets: [{
                label: 'Code Quality',
                data: [
                    metrics.maintainability || 0,
                    metrics.security || 0,
                    metrics.performance || 0,
                    metrics.readability || 0
                ],
                backgroundColor: 'rgba(72, 69, 255, 0.2)', // brand-500 with opacity
                borderColor: '#4845ff', // brand-500
                pointBackgroundColor: '#fff',
                pointBorderColor: '#4845ff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#4845ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: {
                        color: '#9ca3af', // gray-400
                        font: { size: 10, family: "'JetBrains Mono', monospace" }
                    },
                    ticks: { display: false, backdropColor: 'transparent' },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

function toggleSplitView() {
    const mainContent = document.getElementById('mainContentArea');
    const splitView = document.getElementById('splitViewContainer');
    const btn = document.getElementById('splitViewBtn');

    if (splitView.classList.contains('hidden')) {
        // Switch to Split View
        mainContent.classList.add('hidden');
        splitView.classList.remove('hidden');
        btn.classList.add('text-brand-400', 'bg-white/5');

        // Populate content
        if (window.lastAnalysisData) {
            document.getElementById('splitOriginal').innerText = window.lastAnalysisData.original;
            document.getElementById('splitRefactored').innerText = window.lastAnalysisData.refactored;
        }
    } else {
        // Switch back to Tabs
        splitView.classList.add('hidden');
        mainContent.classList.remove('hidden');
        btn.classList.remove('text-brand-400', 'bg-white/5');
    }
}
