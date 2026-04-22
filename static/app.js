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
};

// ========== TAILOR PAGE ==========
const jobDesc = document.getElementById('jobDesc');
const resumeFile = document.getElementById('resumeFile');
const fileStatus = document.getElementById('fileStatus');
const tailorBtn = document.getElementById('tailorBtn');
const resultCard = document.getElementById('resultCard');
const scoreValue = document.getElementById('scoreValue');
const tailoredText = document.getElementById('tailoredText');
const downloadLink = document.getElementById('downloadLink');
const goToApplyBtn = document.getElementById('goToApplyBtn');
const tailorStatus = document.getElementById('tailorStatus');

resumeFile.addEventListener('change', () => {
  fileStatus.textContent = resumeFile.files[0] ? resumeFile.files[0].name : 'No file selected';
});

tailorBtn.addEventListener('click', async () => {
  if (!jobDesc.value.trim() || !resumeFile.files[0]) {
    tailorStatus.textContent = 'Please paste a job description and upload a resume.';
    tailorStatus.className = 'status error';
    return;
  }

  tailorStatus.className = 'status';
  tailorStatus.textContent = 'Tailoring... this may take a moment.';
  tailorBtn.disabled = true;
  resultCard.classList.add('hidden');

  const formData = new FormData();
  formData.append('job_description', jobDesc.value);
  formData.append('resume', resumeFile.files[0]);

  try {
    const res = await fetch('/api/tailor', { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Server error');
    const data = await res.json();

    scoreValue.textContent = data.score + '/100';
    tailoredText.textContent = data.preview_text;
    downloadLink.href = data.download_url;
    downloadLink.classList.remove('hidden');
    goToApplyBtn.classList.remove('hidden');
    resultCard.classList.remove('hidden');

    // Save to shared state for apply page
    state.tailoredResumePath = data.resume_path;
    state.jobDescription = jobDesc.value;
    updateResumeStatus();

    tailorStatus.textContent = 'Done.';
    tailorStatus.className = 'status success';
  } catch (err) {
    tailorStatus.textContent = 'Something went wrong: ' + err.message;
    tailorStatus.className = 'status error';
  } finally {
    tailorBtn.disabled = false;
  }
});

goToApplyBtn.addEventListener('click', () => switchPage('apply'));

// ========== APPLY PAGE ==========
const appUrl = document.getElementById('appUrl');
const startAgentBtn = document.getElementById('startAgentBtn');
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

    addLog('Browser launched and navigated to URL', 'success');
    addLog(data.message || 'Awaiting first step...', 'action');
    // Stub: real flow would stream agent actions via SSE or polling
    confirmText.textContent = 'Backend stub — implement agent polling / SSE here.';
    confirmBox.classList.remove('hidden');
  } catch (err) {
    addLog('Error: ' + err.message, 'warning');
    applyStatus.textContent = 'Agent failed to start.';
    applyStatus.className = 'status error';
  }
});

approveBtn.addEventListener('click', async () => {
  addLog('User approved — continuing to next step', 'success');
  confirmBox.classList.add('hidden');
  // TODO: POST /api/apply/continue
});

rejectBtn.addEventListener('click', async () => {
  addLog('User stopped the agent', 'warning');
  confirmBox.classList.add('hidden');
  startAgentBtn.disabled = false;
  applyStatus.textContent = 'Agent stopped by user.';
  // TODO: POST /api/apply/stop
});