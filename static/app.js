
// Page starting
console.log("JS script is running...");



// ========== TAB SWITCHING ==========
const tabs = document.querySelectorAll('.tab');
const pages = document.querySelectorAll('.page');

function switchPage(pageName) {
  tabs.forEach(t => t.classList.toggle('active', t.dataset.page === pageName));
  pages.forEach(p => p.classList.toggle('active', p.id === `page-${pageName}`));
}

tabs.forEach(t => t.addEventListener('click', () => switchPage(t.dataset.page)));

// ========== SHARED STATE ==========
const state = {
  tailoredResumePath: null,
  jobDescription: null,
  browserSessionId: null,
};
// ========== TAILOR PAGE ==========
const jobDesc = document.getElementById('jobDesc');
const resumeFile = document.getElementById('resumeFile');
const fileStatus = document.getElementById('fileStatus');
const tailorBtn = document.getElementById('tailorBtn');
const tailorStatus = document.getElementById('tailorStatus');
const resultCard = document.getElementById('resultCard');
const scoreValue = document.getElementById('scoreValue');
const downloadLink = document.getElementById('downloadLink');
const goToApplyBtn = document.getElementById('goToApplyBtn');
const previewContainer = document.getElementById('docx-preview-container');
const modelSummary = document.getElementById('modelSummary');
const changesCount = document.getElementById('changesCount');

resumeFile.addEventListener('change', () => {
  fileStatus.textContent = resumeFile.files[0] ? resumeFile.files[0].name : 'No file selected';
});

tailorBtn.addEventListener('click', async () => {
  // Validation
  if (!jobDesc.value.trim() || !resumeFile.files[0]) {
    tailorStatus.textContent = 'Please paste a job description and upload a resume.';
    tailorStatus.className = 'status error';
    return;
  }

  const formData = new FormData();
  formData.append('job_description', jobDesc.value);
  formData.append('resume', resumeFile.files[0]);

  tailorBtn.disabled = true;
  tailorStatus.textContent = 'Tailoring...';
  tailorStatus.className = 'status';
  resultCard.classList.add('hidden');  // Hide previous result while working

  try {
    const res = await fetch('/api/tailor', { method: 'POST', body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Server error (${res.status})`);
    }
    const data = await res.json();
    console.log("Tailor Response: ", data);

    // Update result card contents
    scoreValue.textContent = (data.score ?? 0) + '/100';
    modelSummary.textContent = data.model_summary || 'No summary returned.';
    changesCount.textContent = data.changes_count != null
      ? `(${data.changes_count} paragraphs)`
      : '';
    downloadLink.href = data.download_url;

    // Reveal the card BEFORE rendering preview so the container has a size
    resultCard.classList.remove('hidden');

    // Render the tailored .docx into the preview container
    await renderDocxPreview(data.preview_url);

    // Save state for the apply page
    state.sessionId = data.session_id;
    state.tailoredResumePath = data.download_url;
    state.jobDescription = jobDesc.value;
    updateResumeStatus();

    tailorStatus.textContent = 'Done. Review the preview below.';
    tailorStatus.className = 'status success';
  } catch (err) {
    console.log(err);
    tailorStatus.textContent = 'Something went wrong: ' + err.message;
    tailorStatus.className = 'status error';
  } finally {
    tailorBtn.disabled = false;
  }
});

async function renderDocxPreview(url) {
  if (typeof docx === 'undefined') {
    throw new Error('docx-preview library not loaded');
  }

  previewContainer.innerHTML = '<p>Loading preview...</p>';

  const res = await fetch(url);
  if (!res.ok) throw new Error('Could not load preview');
  const blob = await res.blob();

  previewContainer.innerHTML = '';
  await docx.renderAsync(blob, previewContainer, null, {
    className: 'docx-preview',
    inWrapper: true,
    ignoreWidth: false,
    ignoreHeight: false,
    breakPages: true,
  });
}





// ---------------------------

goToApplyBtn.addEventListener('click', () => switchPage('apply'));

// ========== APPLY PAGE ==========
const appUrl = document.getElementById('appUrl');
const startAgentBtn = document.getElementById('startAgentBtn');
const beginBtn = document.getElementById('beginBtn');
const resumeDot = document.getElementById('resumeDot');
const resumeReadyText = document.getElementById('resumeReadyText');
const agentLog = document.getElementById('agentLog');
const logEntries = document.getElementById('logEntries');
const confirmBox = document.getElementById('confirmBox');
const confirmText = document.getElementById('confirmText');
const approveBtn = document.getElementById('approveBtn');
const rejectBtn = document.getElementById('rejectBtn');
const applyStatus = document.getElementById('applyStatus');

function updateResumeStatus() {
  if (state.tailoredResumePath) {
    resumeDot.classList.add('ready');
    resumeReadyText.textContent = 'Tailored resume ready ✓';
    startAgentBtn.disabled = !appUrl.value;
  } else {
    resumeDot.classList.remove('ready');
    resumeReadyText.textContent = 'No tailored resume yet — tailor one first';
    startAgentBtn.disabled = true;
  }
}

appUrl.addEventListener('input', updateResumeStatus);

function addLog(message, type = '') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const time = new Date().toLocaleTimeString();
  entry.innerHTML = `<span class="time">[${time}]</span>${message}`;
  logEntries.appendChild(entry);
  logEntries.scrollTop = logEntries.scrollHeight;
}

startAgentBtn.addEventListener('click', async () => {
  if (!state.tailoredResumePath || !appUrl.value) return;

  agentLog.classList.remove('hidden');
  logEntries.innerHTML = '';
  addLog('Starting agent...', 'action');
  startAgentBtn.disabled = true;
  applyStatus.className = 'status';
  applyStatus.textContent = 'Agent is working...';

  try {
    const res = await fetch('/api/apply/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: appUrl.value,
        resume_path: state.tailoredResumePath,
        job_description: state.jobDescription,
      }),
    });
    const data = await res.json();

    // track browser id
    state.browserSessionId = data.session_id;

    addLog('Browser launched and navigated to URL', 'success');
    addLog(data.message || 'Awaiting first step...', 'action');

    beginBtn.classList.remove('hidden');

    // Stub: real flow would stream agent actions via SSE or polling
    
  } catch (err) {
    addLog('Error: ' + err.message, 'warning');
    applyStatus.textContent = 'Agent failed to start.';
    applyStatus.className = 'status error';
  }
});


// ------
// Begin applying with agent button
// -----
beginBtn.addEventListener('click', async () => {
  if (!state.sessionId) return;

  beginBtn.disabled = true;
  addLog('Beginning agent on current page...', 'action');

  try {
    const res = await fetch('/api/apply/begin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    const data = await res.json();

    addLog('Page data received', 'success');
    console.log('Page HTML length:', data.html?.length);
    // Next step: render what the agent saw, show confirm box, etc.

    confirmText.textContent = 'Backend stub — implement agent polling / SSE here.';
    confirmBox.classList.remove('hidden');
  } catch (err) {
    addLog('Begin failed: ' + err.message, 'warning');
    beginBtn.disabled = false;
  }
});


// ------
// Continue applying with agent button
// -----
approveBtn.addEventListener('click', async () => {
  addLog('User approved — continuing to next step', 'success');
  confirmBox.classList.add('hidden');
  // TODO: POST /api/apply/continue
});


// ------
// Stop applying with agent button
// -----
rejectBtn.addEventListener('click', async () => {
  addLog('User stopped the agent', 'warning');
  confirmBox.classList.add('hidden');
  startAgentBtn.disabled = false;
  applyStatus.textContent = 'Agent stopped by user.';
  // TODO: POST /api/apply/stop
});