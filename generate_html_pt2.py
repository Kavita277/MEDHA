import os

html_content = """
    <!-- Bootstrap Bundle with Popper -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <script>
        // API Base
        const API_BASE = "/api";

        // State
        let ddsHistory = [];
        let labelsHistory = [];
        let timelineChart = null;
        let ddsChart = null;
        
        // Theme Toggle
        const btnTheme = document.getElementById('btnThemeToggle');
        btnTheme.addEventListener('click', () => {
            const body = document.body;
            if(body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                btnTheme.innerHTML = '<i class="bi bi-moon-stars"></i>';
            } else {
                body.setAttribute('data-theme', 'dark');
                btnTheme.innerHTML = '<i class="bi bi-sun"></i>';
            }
        });

        // Range listeners
        ['Iso','Lat','Skip','Dur','Miss', 'Act'].forEach(k => {
            const el = document.getElementById('beh'+k);
            if(el) {
                el.addEventListener('input', (e) => {
                    document.getElementById('val'+k).innerText = e.target.value;
                });
            }
        });

        // Initialize Temporal Table
        const tbody = document.querySelector('#temporalTable tbody');
        for(let i=1; i<=7; i++) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>T-${7-i}</td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*60 + 20)}"></td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*5)}"></td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*5)}"></td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*5)}"></td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*5)}"></td>
                <td><input type="number" class="form-control form-control-sm tmp-val" value="${Math.floor(Math.random()*5)}"></td>
            `;
            tbody.appendChild(tr);
        }

        // Helper to extract Temporal features (assuming model expects 7 timesteps x 72 features, we just repeat the 6 editable ones 12 times to make 72)
        function getTemporalFeatures() {
            const rows = document.querySelectorAll('#temporalTable tbody tr');
            const features = [];
            rows.forEach(r => {
                const inputs = r.querySelectorAll('input');
                const vals = Array.from(inputs).map(i => parseFloat(i.value) || 0);
                // expand to 72 features for the backend mock
                const expanded = [];
                for(let i=0; i<12; i++) {
                    expanded.push(...vals);
                }
                features.push(expanded);
            });
            return features;
        }

        // Toast Helper
        function showToast(title, msg, type='primary') {
            const container = document.querySelector('.toast-container');
            const id = 'toast' + Date.now();
            const bgClass = type === 'error' ? 'bg-danger text-white' : (type==='success'?'bg-success text-white':'bg-primary text-white');
            const toastHtml = `
                <div id="${id}" class="toast align-items-center ${bgClass} border-0 mb-2" role="alert" aria-live="assertive" aria-atomic="true">
                  <div class="d-flex">
                    <div class="toast-body">
                      <strong>${title}</strong><br>${msg}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                  </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', toastHtml);
            const toastEl = new bootstrap.Toast(document.getElementById(id), {delay: 5000});
            toastEl.show();
        }

        // Button State Helper
        function setLoading(btnId, isLoading) {
            const btn = document.getElementById(btnId);
            const spinner = btn.querySelector('.spinner-border');
            const text = btn.querySelector('.btn-text');
            if (isLoading) {
                btn.disabled = true;
                spinner.classList.remove('d-none');
                text.dataset.original = text.innerText;
                text.innerText = ' Running AI Engine...';
            } else {
                btn.disabled = false;
                spinner.classList.add('d-none');
                text.innerText = text.dataset.original;
            }
        }

        // Fetch Wrapper
        async function apiPost(endpoint, payload, btnId) {
            if(btnId) setLoading(btnId, true);
            try {
                const response = await fetch(API_BASE + endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                    const errText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errText}`);
                }
                
                const data = await response.json();
                if(btnId) setLoading(btnId, false);
                return data;
            } catch (err) {
                if(btnId) setLoading(btnId, false);
                showToast('API Error', err.message, 'error');
                console.error(err);
                throw err;
            }
        }

        // 1. Patient Create
        document.getElementById('patientForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                patient_id: document.getElementById('patId').value,
                name: document.getElementById('patName').value,
                age: parseInt(document.getElementById('patAge').value),
                gender: document.getElementById('patGender').value,
                phone: document.getElementById('patPhone').value,
                district: document.getElementById('patDistrict').value,
                case_id: document.getElementById('patCaseId').value
            };
            try {
                await apiPost('/patients', payload, 'btnCreatePatient');
                showToast('Success', 'Patient Created Successfully!', 'success');
            } catch (e) {}
        });

        // 2. Text Engine
        document.getElementById('btnAnalyzeText').addEventListener('click', async () => {
            const text = document.getElementById('textInput').value || "Default input";
            try {
                const res = await apiPost('/analyze/text', { text: text }, 'btnAnalyzeText');
                document.getElementById('textResult').classList.remove('d-none');
                document.getElementById('txtRisk').innerText = res.risk_score.toFixed(3);
                document.getElementById('txtConf').innerText = res.confidence.toFixed(3);
                document.getElementById('txtTime').innerText = res.processing_time_ms.toFixed(1);
            } catch (e) {}
        });

          // 3. Voice Engine Audio Recording Logic (Real WAV Encoder)
          let audioContext;
          let mediaStreamSource;
          let processor;
          let pcmData = [];
          let audioStream;

          function encodeWAV(samples, sampleRate) {
              const buffer = new ArrayBuffer(44 + samples.length * 2);
              const view = new DataView(buffer);
              
              const writeString = (view, offset, string) => {
                  for (let i = 0; i < string.length; i++) {
                      view.setUint8(offset + i, string.charCodeAt(i));
                  }
              };
              
              writeString(view, 0, 'RIFF');
              view.setUint32(4, 36 + samples.length * 2, true);
              writeString(view, 8, 'WAVE');
              writeString(view, 12, 'fmt ');
              view.setUint32(16, 16, true);
              view.setUint16(20, 1, true);
              view.setUint16(22, 1, true);
              view.setUint32(24, sampleRate, true);
              view.setUint32(28, sampleRate * 2, true);
              view.setUint16(32, 2, true);
              view.setUint16(34, 16, true);
              writeString(view, 36, 'data');
              view.setUint32(40, samples.length * 2, true);
              
              let offset = 44;
              for (let i = 0; i < samples.length; i++, offset += 2) {
                  let s = Math.max(-1, Math.min(1, samples[i]));
                  view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
              }
              
              return new Blob([view], { type: 'audio/wav' });
          }

          document.getElementById('btnRecord').addEventListener('click', async () => {
              const btn = document.getElementById('btnRecord');
              const icon = document.getElementById('recordIcon');
              const text = document.getElementById('recordText');
              const status = document.getElementById('recordingStatus');
              
              if (processor) {
                  // Stop recording
                  processor.disconnect();
                  mediaStreamSource.disconnect();
                  audioStream.getTracks().forEach(track => track.stop());
                  
                  btn.classList.replace('btn-danger', 'btn-outline-danger');
                  icon.classList.replace('bi-stop-circle', 'bi-record-circle');
                  text.innerText = 'Record';
                  status.innerText = 'Uploading...';
                  
                  // Flatten PCM data
                  let totalLength = pcmData.reduce((acc, val) => acc + val.length, 0);
                  let samples = new Float32Array(totalLength);
                  let offset = 0;
                  for (let i = 0; i < pcmData.length; i++) {
                      samples.set(pcmData[i], offset);
                      offset += pcmData[i].length;
                  }
                  
                  const wavBlob = encodeWAV(samples, audioContext.sampleRate);
                  const formData = new FormData();
                  formData.append('file', wavBlob, 'recording.wav');
                  
                  try {
                      const response = await fetch('/api/upload/audio', {
                          method: 'POST',
                          body: formData
                      });
                      if (!response.ok) throw new Error('Upload failed');
                      const data = await response.json();
                      document.getElementById('voicePath').value = data.audio_path;
                      status.innerText = 'Audio saved!';
                      setTimeout(() => status.classList.add('d-none'), 2000);
                  } catch (error) {
                      console.error(error);
                      status.innerText = 'Upload failed.';
                  }
                  
                  processor = null;
              } else {
                  // Start recording
                  try {
                      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                      audioContext = new (window.AudioContext || window.webkitAudioContext)();
                      mediaStreamSource = audioContext.createMediaStreamSource(audioStream);
                      processor = audioContext.createScriptProcessor(4096, 1, 1);
                      pcmData = [];
                      
                      processor.onaudioprocess = function(e) {
                          pcmData.push(new Float32Array(e.inputBuffer.getChannelData(0)));
                      };
                      
                      mediaStreamSource.connect(processor);
                      processor.connect(audioContext.destination);
                      
                      btn.classList.replace('btn-outline-danger', 'btn-danger');
                      icon.classList.replace('bi-record-circle', 'bi-stop-circle');
                      text.innerText = 'Stop';
                      status.classList.remove('d-none');
                      status.innerText = 'Recording... Speak now.';
                  } catch (err) {
                      alert('Microphone access denied or not available.');
                  }
              }
          });

          document.getElementById('btnAnalyzeVoice').addEventListener('click', async () => {
            const path = document.getElementById('voicePath').value;
            try {
                const res = await apiPost('/analyze/voice', { audio_path: path }, 'btnAnalyzeVoice');
                document.getElementById('voiceResult').classList.remove('d-none');
                document.getElementById('vocRisk').innerText = res.risk_score.toFixed(3);
                document.getElementById('vocConf').innerText = res.confidence.toFixed(3);
                document.getElementById('vocTime').innerText = res.processing_time_ms.toFixed(1);
            } catch (e) {}
        });

        // 4. Behaviour Engine
        document.getElementById('btnAnalyzeBehaviour').addEventListener('click', async () => {
            const payload = {
                patient_id: document.getElementById('patId').value,
                payload: {
                    features: {
                        social_isolation: parseFloat(document.getElementById('behIso').value),
                        response_latency: parseFloat(document.getElementById('behLat').value),
                        session_skip_rate: parseFloat(document.getElementById('behSkip').value),
                        duration_z_score: parseFloat(document.getElementById('behDur').value),
                        missed_sessions: parseFloat(document.getElementById('behMiss').value)
                    }
                }
            };
            try {
                const res = await apiPost('/analyze/behaviour', payload, 'btnAnalyzeBehaviour');
                document.getElementById('behResult').classList.remove('d-none');
                document.getElementById('behRisk').innerText = res.risk_score.toFixed(3);
                document.getElementById('behScore').innerText = (res.prediction.behavioral_risk_score || res.risk_score).toFixed(3);
                document.getElementById('behConf').innerText = res.confidence.toFixed(3);
            } catch (e) {}
        });

        // 5. Structured Engine
        document.getElementById('btnAnalyzeStructured').addEventListener('click', async () => {
            const payload = {
                data: {
                    "Mood": parseFloat(document.getElementById('strMood').value),
                    "Stress": parseFloat(document.getElementById('strStress').value),
                    "Sleep": parseFloat(document.getElementById('strSleep').value),
                    "Functioning": parseFloat(document.getElementById('strFunc').value),
                    "Safety": parseFloat(document.getElementById('strSafety').value),
                    "Social_Support_Checkin": parseFloat(document.getElementById('strSocial').value),
                    "Self_Reported_Wellbeing": parseFloat(document.getElementById('strWellbeing').value)
                }
            };
            try {
                const res = await apiPost('/analyze/structured', payload, 'btnAnalyzeStructured');
                document.getElementById('strResult').classList.remove('d-none');
                document.getElementById('strRisk').innerText = res.risk_score.toFixed(3);
                document.getElementById('strConf').innerText = res.confidence.toFixed(3);
            } catch (e) {}
        });

        // 6. Temporal Engine
        document.getElementById('btnAnalyzeTemporal').addEventListener('click', async () => {
            try {
                const res = await apiPost('/analyze/temporal', { features: getTemporalFeatures() }, 'btnAnalyzeTemporal');
                document.getElementById('tmpResult').classList.remove('d-none');
                document.getElementById('tmpRisk').innerText = res.risk_score.toFixed(3);
                document.getElementById('tmpScore').innerText = res.risk_score.toFixed(3);
                document.getElementById('tmpConf').innerText = res.confidence.toFixed(3);
            } catch(e) {}
        });

        // 7. Fusion Engine
        document.getElementById('btnRunFusion').addEventListener('click', async () => {
            document.getElementById('fusionStatusText').innerText = 'Collecting data and running AI...';
            
            const payload = {
                text: document.getElementById('textInput').value || "Help me.",
                audio_path: document.getElementById('voicePath').value,
                patient_id: document.getElementById('patId').value,
                behaviour_payload: {
                    features: {
                        social_isolation: parseFloat(document.getElementById('behIso').value),
                        response_latency: parseFloat(document.getElementById('behLat').value),
                        session_skip_rate: parseFloat(document.getElementById('behSkip').value),
                        duration_z_score: parseFloat(document.getElementById('behDur').value),
                        missed_sessions: parseFloat(document.getElementById('behMiss').value)
                    }
                },
                structured_data: {
                    "Mood": parseFloat(document.getElementById('strMood').value),
                    "Stress": parseFloat(document.getElementById('strStress').value),
                    "Sleep": parseFloat(document.getElementById('strSleep').value),
                    "Functioning": parseFloat(document.getElementById('strFunc').value),
                    "Safety": parseFloat(document.getElementById('strSafety').value),
                    "Social_Support_Checkin": parseFloat(document.getElementById('strSocial').value),
                    "Self_Reported_Wellbeing": parseFloat(document.getElementById('strWellbeing').value)
                },
                temporal_features: getTemporalFeatures()
            };

            try {
                const res = await apiPost('/fusion/predict', payload, 'btnRunFusion');
                document.getElementById('fusionStatusText').innerText = '';
                showToast('Prediction Complete', `DDS Score: ${res.dds}`, 'success');
                
                // Show dashboard
                document.getElementById('resultsDashboard').classList.remove('d-none');
                
                // Update JSON
                // syntax highlighting style block
                const jsonStr = JSON.stringify(res, null, 2);
                document.getElementById('jsonViewer').innerHTML = syntaxHighlight(jsonStr);
                
                updateResults(res);
                updateTimeline(res.dds);

            } catch(e) {
                document.getElementById('fusionStatusText').innerText = 'Error occurred.';
            }
        });

        // Syntax Highlighter
        function syntaxHighlight(json) {
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+\\-]?\\d+)?)/g, function (match) {
                var cls = 'text-warning';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'text-primary';
                    } else {
                        cls = 'text-success';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'text-info';
                } else if (/null/.test(match)) {
                    cls = 'text-danger';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }

        function getRiskColor(level) {
            if(level === 'LOW') return '#198754';
            if(level === 'MEDIUM') return '#ffc107';
            return '#dc3545';
        }

        function getRiskBgClass(level) {
            if(level === 'LOW') return 'bg-success';
            if(level === 'MEDIUM') return 'bg-warning text-dark';
            return 'bg-danger';
        }

        function updateResults(res) {
            // Gauge value
            document.getElementById('resDdsVal').innerText = res.dds;
            
            // Badge
            const badge = document.getElementById('resRiskBadge');
            badge.innerText = res.risk_level;
            badge.className = `badge px-4 py-2 ${getRiskBgClass(res.risk_level)}`;

            document.getElementById('resConf').innerText = res.confidence;

            // Gauge Chart
            updateGaugeChart(res.dds, getRiskColor(res.risk_level));

            // Engine cards
            const engines = ['text', 'voice', 'behaviour', 'structured', 'temporal'];
            engines.forEach(eng => {
                const el = document.getElementById('card' + eng.charAt(0).toUpperCase() + eng.slice(1,3));
                if(el && res.engine_contributions[eng] !== undefined) {
                    el.innerHTML = `
                        <div class="card p-3 shadow-sm border-0" style="border-bottom: 4px solid var(--primary-color) !important;">
                            <div class="metric-label text-capitalize">${eng} Engine</div>
                            <div class="metric-value fs-3" style="color: ${getRiskColor(res.risk_level)}">${(res.engine_scores[eng]*100).toFixed(1)}</div>
                            <small class="text-muted">Contribution: ${res.engine_contributions[eng]}</small>
                        </div>
                    `;
                }
            });

            // Recs
            const recsContainer = document.getElementById('resRecs');
            recsContainer.innerHTML = '';
            res.recommendations.forEach(r => {
                recsContainer.innerHTML += `<div class="p-3 mb-2 bg-light border rounded text-dark fw-bold w-100 shadow-sm"><i class="bi bi-arrow-right-circle-fill text-primary me-2"></i>${r}</div>`;
            });
        }

        function updateGaugeChart(val, color) {
            const ctx = document.getElementById('ddsChart');
            if (ddsChart) ddsChart.destroy();
            
            ddsChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    datasets: [{
                        data: [val, 100-val],
                        backgroundColor: [color, '#e9ecef'],
                        borderWidth: 0,
                        circumference: 180,
                        rotation: 270
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '80%',
                    plugins: { tooltip: { enabled: false } },
                    animation: { animateRotate: true }
                }
            });
        }

        function updateTimeline(newVal) {
            ddsHistory.push(newVal);
            labelsHistory.push(new Date().toLocaleTimeString());
            
            if(ddsHistory.length > 10) {
                ddsHistory.shift();
                labelsHistory.shift();
            }

            const ctx = document.getElementById('timelineChart');
            if(timelineChart) {
                timelineChart.update();
            } else {
                timelineChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labelsHistory,
                        datasets: [{
                            label: 'DDS Score',
                            data: ddsHistory,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { min: 0, max: 100 }
                        }
                    }
                });
            }
        }
        
        // --- HISTORY DASHBOARD LOGIC ---
        let historicalChartObj = null;

        document.getElementById('btnLoadHistory').addEventListener('click', async () => {
            const patId = document.getElementById('searchPatientId').value;
            if(!patId) return;
            
            setLoading('btnLoadHistory', true);
            try {
                // Fetch trend
                const trendRes = await fetch(`${API_BASE}/patients/${patId}/trend`);
                if(!trendRes.ok) throw new Error("Trend fetch failed");
                const trendData = await trendRes.json();
                
                // Fetch timeline
                const timeRes = await fetch(`${API_BASE}/patients/${patId}/timeline`);
                if(!timeRes.ok) throw new Error("Timeline fetch failed");
                const timeData = await timeRes.json();
                
                document.getElementById('historyDashboard').classList.remove('d-none');
                
                // Update Trend Cards
                document.getElementById('histCurrentDds').innerText = trendData.current_dds || 0;
                document.getElementById('histAvgDds').innerText = trendData.average_dds || 0;
                document.getElementById('histHighDds').innerText = trendData.highest_dds || 0;
                
                const trCard = document.getElementById('histTrendCard');
                const trStatus = document.getElementById('histTrendStatus');
                trStatus.innerText = trendData.trend;
                trCard.className = 'card h-100 border-0 shadow-sm text-center p-3 text-white ';
                if(trendData.trend === 'Increasing') trCard.classList.add('bg-danger');
                else if(trendData.trend === 'Decreasing') trCard.classList.add('bg-success');
                else trCard.classList.add('bg-secondary');
                
                // Update Historical Chart
                updateHistoricalChart(trendData.last_7_predictions);
                
                // Update Timeline Table
                const tbody = document.getElementById('timelineTableBody');
                tbody.innerHTML = '';
                timeData.events.forEach(ev => {
                    const d = new Date(ev.timestamp).toLocaleString();
                    let badge = '';
                    let details = '';
                    if(ev.type === 'RiskPrediction') {
                        badge = `<span class="badge bg-primary">AI Prediction</span>`;
                        details = `DDS: <strong>${ev.data.dds}</strong> | Risk: <span class="badge ${getRiskBgClass(ev.data.risk_level)}">${ev.data.risk_level}</span>`;
                        if(ev.data.recommendation && ev.data.recommendation.length > 0) {
                            details += `<br><small class="text-muted">Recs: ${ev.data.recommendation.join(', ')}</small>`;
                        }
                    } else if (ev.type === 'Interaction') {
                        badge = `<span class="badge bg-info text-dark">Interaction (${ev.data.interaction_type})</span>`;
                        details = `${ev.data.summary}`;
                    } else if (ev.type === 'Session') {
                        badge = `<span class="badge bg-secondary">Session</span>`;
                        details = `Session ID: ${ev.data.session_id} - ${ev.data.status}`;
                    } else if (ev.type === 'Answer') {
                        badge = `<span class="badge bg-light text-dark border">Answer</span>`;
                        details = `Q: ${ev.data.question_id} -> ${ev.data.answer_text}`;
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td class="text-nowrap">${d}</td>
                            <td>${badge}</td>
                            <td>${details}</td>
                        </tr>
                    `;
                });
                
            } catch(e) {
                showToast('History Error', e.message, 'error');
            }
            setLoading('btnLoadHistory', false);
        });

        function updateHistoricalChart(predictions) {
            const ctx = document.getElementById('historicalDdsChart');
            const labels = predictions.map(p => p.date.split(' ')[0]);
            const data = predictions.map(p => p.dds);
            
            if(historicalChartObj) {
                historicalChartObj.destroy();
            }
            
            historicalChartObj = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Historical DDS',
                        data: data,
                        backgroundColor: data.map(v => v > 65 ? '#dc3545' : (v > 35 ? '#ffc107' : '#198754')),
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { min: 0, max: 100 }
                    }
                }
            });
        }
    </script>
</body>
</html>
"""

with open("d:/Projects/SIH/templates/index_html_pt2.txt", "w", encoding="utf-8") as f:
    f.write(html_content)

# Concatenate both
with open("d:/Projects/SIH/templates/index.html", "w", encoding="utf-8") as f:
    f.write(open("d:/Projects/SIH/templates/index_html_pt1.txt", "r", encoding="utf-8").read())
    f.write(open("d:/Projects/SIH/templates/index_html_pt2.txt", "r", encoding="utf-8").read())

