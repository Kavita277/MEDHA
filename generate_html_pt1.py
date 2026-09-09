import os

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MEDHA AI Testing Dashboard</title>
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-bg: #f8f9fa;
            --card-bg: #ffffff;
            --text-main: #333333;
            --text-muted: #6c757d;
            --primary-color: #0d6efd;
            --success-color: #198754;
            --warning-color: #ffc107;
            --danger-color: #dc3545;
            --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
            --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            --border-radius: 12px;
        }

        [data-theme="dark"] {
            --primary-bg: #121212;
            --card-bg: #1e1e1e;
            --text-main: #f8f9fa;
            --text-muted: #adb5bd;
            --shadow-sm: 0 0.125rem 0.25rem rgba(0,0,0,0.5);
            --shadow-md: 0 0.5rem 1rem rgba(0,0,0,0.5);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--primary-bg);
            color: var(--text-main);
            transition: all 0.3s ease;
        }

        /* Navbar */
        .navbar {
            background-color: var(--card-bg) !important;
            box-shadow: var(--shadow-sm);
        }
        
        .navbar-brand {
            font-weight: 700;
            color: var(--primary-color) !important;
        }

        /* Cards */
        .card {
            background-color: var(--card-bg);
            border: none;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-sm);
            margin-bottom: 24px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .card:hover {
            box-shadow: var(--shadow-md);
        }

        .card-header {
            background-color: transparent;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            font-weight: 600;
            padding: 16px 20px;
        }
        
        [data-theme="dark"] .card-header {
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .card-body {
            padding: 20px;
        }

        /* Inputs */
        .form-control, .form-select {
            background-color: var(--primary-bg);
            border: 1px solid rgba(0,0,0,0.1);
            color: var(--text-main);
            border-radius: 8px;
        }
        
        [data-theme="dark"] .form-control, [data-theme="dark"] .form-select {
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .form-control:focus, .form-select:focus {
            box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
            background-color: var(--primary-bg);
            color: var(--text-main);
        }
        
        [data-theme="dark"] .table { color: var(--text-main); }
        [data-theme="dark"] th { color: var(--text-muted); }

        /* Buttons */
        .btn {
            border-radius: 8px;
            font-weight: 500;
            padding: 8px 16px;
        }
        
        .btn-run-all {
            padding: 16px 32px;
            font-size: 1.2rem;
            font-weight: 600;
            border-radius: 50px;
            box-shadow: var(--shadow-md);
        }

        /* Animations */
        .fade-in {
            animation: fadeIn 0.5s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Results Display */
        .result-box {
            background-color: var(--primary-bg);
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            border: 1px solid rgba(0,0,0,0.05);
        }
        
        [data-theme="dark"] .result-box {
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .metric-value {
            font-size: 1.25rem;
            font-weight: 700;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-muted);
        }

        /* Gauge */
        .gauge-container {
            position: relative;
            width: 200px;
            height: 100px;
            margin: 0 auto;
        }
        
        /* JSON Viewer */
        #jsonViewer {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 16px;
            border-radius: 8px;
            font-family: monospace;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
        }

        .range-value {
            display: inline-block;
            width: 30px;
            text-align: right;
            font-weight: bold;
        }
        
        /* Toasts container */
        .toast-container {
            z-index: 1056;
        }
    </style>
</head>
<body>

    <!-- Sticky Header -->
    <nav class="navbar navbar-expand-lg sticky-top">
        <div class="container-fluid px-4">
            <a class="navbar-brand" href="#"><i class="bi bi-heart-pulse-fill me-2"></i>MEDHA AI</a>
            <div class="d-flex align-items-center gap-3">
                <button class="btn btn-outline-secondary btn-sm" id="btnThemeToggle"><i class="bi bi-moon-stars"></i></button>
                <button class="btn btn-outline-primary btn-sm" id="btnRefresh" onclick="location.reload()"><i class="bi bi-arrow-clockwise me-1"></i>Refresh</button>
                <button class="btn btn-outline-danger btn-sm" id="btnClear" onclick="document.querySelectorAll('form').forEach(f=>f.reset())"><i class="bi bi-trash me-1"></i>Clear Forms</button>
            </div>
        </div>
    </nav>

    <!-- Toasts -->
    <div class="toast-container position-fixed bottom-0 end-0 p-3">
        <!-- Toasts injected dynamically -->
    </div>

    <div class="container-fluid py-4 px-4">
        
        <!-- SECTION 1: Patient Information -->
        <div class="row fade-in">
            <div class="col-12">
                <div class="card">
                    <div class="card-header"><i class="bi bi-person-badge me-2"></i>Patient Information</div>
                    <div class="card-body">
                        <form id="patientForm" class="row g-3">
                            <div class="col-md-2">
                                <label class="form-label">Patient ID</label>
                                <input type="text" class="form-control" id="patId" value="P001" required>
                            </div>
                            <div class="col-md-3">
                                <label class="form-label">Name</label>
                                <input type="text" class="form-control" id="patName" value="John Doe" required>
                            </div>
                            <div class="col-md-1">
                                <label class="form-label">Age</label>
                                <input type="number" class="form-control" id="patAge" value="30" required>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Gender</label>
                                <select class="form-select" id="patGender">
                                    <option value="Male">Male</option>
                                    <option value="Female">Female</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Phone</label>
                                <input type="text" class="form-control" id="patPhone" value="1234567890">
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">District</label>
                                <input type="text" class="form-control" id="patDistrict" value="Central">
                            </div>
                            <div class="col-md-2">
                                <label class="form-label">Case ID</label>
                                <input type="text" class="form-control" id="patCaseId" value="C-999">
                            </div>
                            <div class="col-12 text-end">
                                <button type="submit" class="btn btn-primary" id="btnCreatePatient">
                                    <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                    <span class="btn-text">Create Patient</span>
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECTION 2: Text & Voice -->
        <div class="row fade-in" style="animation-delay: 0.1s;">
            <!-- Text Engine -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header"><i class="bi bi-chat-text me-2"></i>Text Engine</div>
                    <div class="card-body d-flex flex-column">
                        <textarea class="form-control flex-grow-1 mb-3" id="textInput" rows="4" placeholder="Describe what the victim said...">He threatened me yesterday.</textarea>
                        <div class="text-end mb-3">
                            <button class="btn btn-primary" id="btnAnalyzeText">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                <span class="btn-text">Analyze Text</span>
                            </button>
                        </div>
                        <div class="result-box d-none" id="textResult">
                            <div class="row text-center">
                                <div class="col"><div class="metric-label">Risk Score</div><div class="metric-value text-primary" id="txtRisk">-</div></div>
                                <div class="col"><div class="metric-label">Confidence</div><div class="metric-value" id="txtConf">-</div></div>
                                <div class="col"><div class="metric-label">Time (ms)</div><div class="metric-value" id="txtTime">-</div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Voice Engine -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header"><i class="bi bi-mic me-2"></i>Voice Engine</div>
                    <div class="card-body d-flex flex-column">
                        <div class="mb-3">
                            <label class="form-label">Upload WAV File</label>
                            <div class="input-group">
                                <input class="form-control" type="text" id="voicePath" placeholder="Audio path..." value="d:/Projects/SIH/tests/payloads/sample.wav">
                                <button class="btn btn-outline-danger" type="button" id="btnRecord">
                                    <i class="bi bi-record-circle" id="recordIcon"></i> <span id="recordText">Record</span>
                                </button>
                            </div>
                            <small class="text-muted d-none" id="recordingStatus">Recording... Speak now.</small>
                        </div>
                        <div class="text-end mb-3">
                            <button class="btn btn-primary" id="btnAnalyzeVoice">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                <span class="btn-text">Analyze Voice</span>
                            </button>
                        </div>
                        <div class="result-box d-none" id="voiceResult">
                            <div class="row text-center">
                                <div class="col"><div class="metric-label">Distress</div><div class="metric-value text-primary" id="vocRisk">-</div></div>
                                <div class="col"><div class="metric-label">Confidence</div><div class="metric-value" id="vocConf">-</div></div>
                                <div class="col"><div class="metric-label">Time (ms)</div><div class="metric-value" id="vocTime">-</div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECTION 3: Behaviour & Structured Risk -->
        <div class="row mt-4 fade-in" style="animation-delay: 0.2s;">
            <!-- Behaviour Engine -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header"><i class="bi bi-activity me-2"></i>Behaviour Engine</div>
                    <div class="card-body">
                        <div class="row g-2">
                            <div class="col-6">
                                <label class="form-label">Isolation <span class="range-value text-primary" id="valIso">5</span></label>
                                <input type="range" class="form-range" id="behIso" min="0" max="10" step="1" value="5">
                            </div>
                            <div class="col-6">
                                <label class="form-label">Social Withdrawal <span class="range-value text-primary" id="valLat">3</span></label>
                                <input type="range" class="form-range" id="behLat" min="0" max="10" step="1" value="3">
                            </div>
                            <div class="col-6">
                                <label class="form-label">Missed Sessions <span class="range-value text-primary" id="valMiss">1</span></label>
                                <input type="range" class="form-range" id="behMiss" min="0" max="10" step="1" value="1">
                            </div>
                            <div class="col-6">
                                <label class="form-label">Behaviour Change <span class="range-value text-primary" id="valDur">6</span></label>
                                <input type="range" class="form-range" id="behDur" min="0" max="10" step="1" value="6">
                            </div>
                            <div class="col-6">
                                <label class="form-label">Activity Level <span class="range-value text-primary" id="valAct">4</span></label>
                                <input type="range" class="form-range" id="behAct" min="0" max="10" step="1" value="4">
                            </div>
                            <div class="col-6">
                                <label class="form-label">Response Delay <span class="range-value text-primary" id="valSkip">2</span></label>
                                <input type="range" class="form-range" id="behSkip" min="0" max="10" step="1" value="2">
                            </div>
                        </div>
                        <div class="text-end mt-3 mb-3">
                            <button class="btn btn-primary" id="btnAnalyzeBehaviour">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                <span class="btn-text">Analyze Behaviour</span>
                            </button>
                        </div>
                        <div class="result-box d-none" id="behResult">
                            <div class="row text-center">
                                <div class="col"><div class="metric-label">Behaviour Score</div><div class="metric-value text-primary" id="behScore">-</div></div>
                                <div class="col"><div class="metric-label">Risk Score</div><div class="metric-value text-primary" id="behRisk">-</div></div>
                                <div class="col"><div class="metric-label">Confidence</div><div class="metric-value" id="behConf">-</div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Structured Risk -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header"><i class="bi bi-clipboard-data me-2"></i>Structured Risk Engine</div>
                    <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                        <form id="structuredForm" class="row g-2">
                            <div class="col-md-4"><label class="form-label">Mood</label><input type="number" class="form-control form-control-sm" id="strMood" value="3"></div>
                            <div class="col-md-4"><label class="form-label">Stress</label><input type="number" class="form-control form-control-sm" id="strStress" value="4"></div>
                            <div class="col-md-4"><label class="form-label">Sleep</label><input type="number" class="form-control form-control-sm" id="strSleep" value="2"></div>
                            <div class="col-md-4"><label class="form-label">Functioning</label><input type="number" class="form-control form-control-sm" id="strFunc" value="3"></div>
                            <div class="col-md-4"><label class="form-label">Safety</label><input type="number" class="form-control form-control-sm" id="strSafety" value="1"></div>
                            <div class="col-md-4"><label class="form-label">Social Support</label><input type="number" class="form-control form-control-sm" id="strSocial" value="1"></div>
                            <div class="col-md-4"><label class="form-label">Wellbeing</label><input type="number" class="form-control form-control-sm" id="strWellbeing" value="2"></div>
                        </form>
                        <div class="text-end mt-3 mb-3">
                            <button class="btn btn-primary" id="btnAnalyzeStructured">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                <span class="btn-text">Predict Structured Risk</span>
                            </button>
                        </div>
                        <div class="result-box d-none" id="strResult">
                            <div class="row text-center">
                                <div class="col"><div class="metric-label">Structured Risk</div><div class="metric-value text-primary" id="strRisk">-</div></div>
                                <div class="col"><div class="metric-label">Confidence</div><div class="metric-value" id="strConf">-</div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECTION 4: Temporal GRU -->
        <div class="row mt-4 fade-in" style="animation-delay: 0.3s;">
            <div class="col-12">
                <div class="card">
                    <div class="card-header"><i class="bi bi-clock-history me-2"></i>Temporal GRU Engine</div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-bordered table-sm text-center align-middle" id="temporalTable">
                                <thead class="table-light">
                                    <tr>
                                        <th>Time</th>
                                        <th>DDS</th>
                                        <th>Mood</th>
                                        <th>Stress</th>
                                        <th>Sleep</th>
                                        <th>Functioning</th>
                                        <th>Safety</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <!-- 7 rows will be generated by JS -->
                                </tbody>
                            </table>
                        </div>
                        <div class="text-end">
                            <button class="btn btn-primary" id="btnAnalyzeTemporal">
                                <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                <span class="btn-text">Predict Future Escalation</span>
                            </button>
                        </div>
                        <div class="result-box d-none mt-3 w-50 ms-auto" id="tmpResult">
                            <div class="row text-center">
                                <div class="col"><div class="metric-label">Escalation Probability</div><div class="metric-value text-danger" id="tmpRisk">-</div></div>
                                <div class="col"><div class="metric-label">Temporal Score</div><div class="metric-value text-primary" id="tmpScore">-</div></div>
                                <div class="col"><div class="metric-label">Confidence</div><div class="metric-value" id="tmpConf">-</div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- SECTION 5: Fusion Orchestrator -->
        <div class="row mt-4 fade-in text-center" style="animation-delay: 0.4s;">
            <div class="col-12 py-4">
                <button class="btn btn-success btn-run-all" id="btnRunFusion">
                    <i class="bi bi-lightning-charge-fill me-2"></i>Run Complete AI Prediction
                </button>
                <div class="mt-2 text-muted small" id="fusionStatusText"></div>
            </div>
        </div>

        <!-- SECTION 6: Results Dashboard -->
        <div id="resultsDashboard" class="d-none">
            <h3 class="mb-4 mt-4 fw-bold"><i class="bi bi-bar-chart-fill me-2"></i>Results Dashboard</h3>
            
            <div class="row">
                <!-- DDS Gauge -->
                <div class="col-md-4">
                    <div class="card h-100 text-center fade-in">
                        <div class="card-body d-flex flex-column justify-content-center align-items-center">
                            <h5 class="card-title text-muted mb-4">DDS Score</h5>
                            <div class="position-relative" style="width: 150px; height: 150px;">
                                <canvas id="ddsChart"></canvas>
                                <div class="position-absolute top-50 start-50 translate-middle">
                                    <h2 class="mb-0 fw-bold" id="resDdsVal">0</h2>
                                </div>
                            </div>
                            <div class="mt-4">
                                <h5><span class="badge bg-secondary px-4 py-2" id="resRiskBadge">UNKNOWN</span></h5>
                            </div>
                            <div class="text-muted mt-2 small">Confidence: <span id="resConf">0.00</span></div>
                        </div>
                    </div>
                </div>
                
                <!-- Recommendations -->
                <div class="col-md-8">
                    <div class="card h-100 fade-in">
                        <div class="card-header bg-transparent"><i class="bi bi-shield-check me-2"></i>Recommendations</div>
                        <div class="card-body">
                            <div class="row gap-2 px-2" id="resRecs">
                                <!-- Generated Badges -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Engine Scores -->
            <div class="row mt-4">
                <div class="col-md-12">
                    <h5 class="mb-3 text-muted">Engine Scores</h5>
                </div>
                <!-- Generated by JS -->
                <div class="col-md text-center fade-in" id="cardText">
                    <div class="card p-3 shadow-sm border-0"><div class="metric-label">Text</div><div class="metric-value text-primary fs-4">0%</div><small class="text-muted">Contribution: 0.0</small></div>
                </div>
                <div class="col-md text-center fade-in" id="cardVoice">
                    <div class="card p-3 shadow-sm border-0"><div class="metric-label">Voice</div><div class="metric-value text-primary fs-4">0%</div><small class="text-muted">Contribution: 0.0</small></div>
                </div>
                <div class="col-md text-center fade-in" id="cardBeh">
                    <div class="card p-3 shadow-sm border-0"><div class="metric-label">Behaviour</div><div class="metric-value text-primary fs-4">0%</div><small class="text-muted">Contribution: 0.0</small></div>
                </div>
                <div class="col-md text-center fade-in" id="cardStr">
                    <div class="card p-3 shadow-sm border-0"><div class="metric-label">Structured</div><div class="metric-value text-primary fs-4">0%</div><small class="text-muted">Contribution: 0.0</small></div>
                </div>
                <div class="col-md text-center fade-in" id="cardTmp">
                    <div class="card p-3 shadow-sm border-0"><div class="metric-label">Temporal</div><div class="metric-value text-primary fs-4">0%</div><small class="text-muted">Contribution: 0.0</small></div>
                </div>
            </div>

            <!-- Timeline -->
            <div class="row mt-4 fade-in">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header"><i class="bi bi-graph-up me-2"></i>Timeline Graph</div>
                        <div class="card-body">
                            <canvas id="timelineChart" height="80"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- JSON Viewer -->
            <div class="row mt-4 fade-in">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span><i class="bi bi-code-square me-2"></i>Complete JSON Response</span>
                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" data-bs-target="#jsonCollapse">Toggle View</button>
                        </div>
                        <div class="collapse show" id="jsonCollapse">
                            <div class="card-body p-0">
                                <pre id="jsonViewer" class="m-0 border-0 rounded-0"></pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>
        
        <!-- SECTION 7: Patient History -->
        <div class="row mt-5 pt-4 border-top">
            <div class="col-12">
                <h3 class="mb-4 fw-bold"><i class="bi bi-clock-history me-2"></i>Longitudinal Patient History</h3>
            </div>
            
            <div class="col-12 mb-4">
                <div class="card">
                    <div class="card-body">
                        <div class="row align-items-end">
                            <div class="col-md-4">
                                <label class="form-label">Search History by Patient ID</label>
                                <input type="text" class="form-control" id="searchPatientId" placeholder="e.g. P001">
                            </div>
                            <div class="col-md-2">
                                <button class="btn btn-primary w-100" id="btnLoadHistory">
                                    <span class="spinner-border spinner-border-sm d-none" role="status" aria-hidden="true"></span>
                                    <span class="btn-text">Load History</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="historyDashboard" class="col-12 d-none">
                <!-- Trend Summary -->
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card h-100 bg-primary text-white border-0 shadow-sm text-center p-3">
                            <h6 class="text-white-50">Current DDS</h6>
                            <h2 class="fw-bold mb-0" id="histCurrentDds">-</h2>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card h-100 bg-info text-white border-0 shadow-sm text-center p-3">
                            <h6 class="text-white-50">Average DDS</h6>
                            <h2 class="fw-bold mb-0" id="histAvgDds">-</h2>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card h-100 bg-warning text-dark border-0 shadow-sm text-center p-3">
                            <h6 class="text-dark-50">Highest DDS</h6>
                            <h2 class="fw-bold mb-0" id="histHighDds">-</h2>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card h-100 border-0 shadow-sm text-center p-3" id="histTrendCard">
                            <h6 class="text-muted">Overall Trend</h6>
                            <h2 class="fw-bold mb-0" id="histTrendStatus">-</h2>
                        </div>
                    </div>
                </div>

                <!-- DDS Trend Chart (Historical) -->
                <div class="card mb-4">
                    <div class="card-header"><i class="bi bi-graph-up me-2"></i>Historical DDS Trend</div>
                    <div class="card-body">
                        <canvas id="historicalDdsChart" height="80"></canvas>
                    </div>
                </div>

                <!-- Chronological Timeline -->
                <div class="card">
                    <div class="card-header"><i class="bi bi-list-nested me-2"></i>Chronological Timeline (Interactions & Predictions)</div>
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover table-striped mb-0 align-middle">
                                <thead class="table-light">
                                    <tr>
                                        <th>Date & Time</th>
                                        <th>Event Type</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody id="timelineTableBody">
                                    <!-- Timeline rows injected here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>
        
    </div>
"""

with open("d:/Projects/SIH/templates/index_html_pt1.txt", "w", encoding="utf-8") as f:
    f.write(html_content)
