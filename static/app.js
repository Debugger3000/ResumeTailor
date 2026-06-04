
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
// const goToApplyBtn = document.getElementById('goToApplyBtn');
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

  
  const originalBtnContent = tailorBtn.innerHTML;
  tailorBtn.disabled = true;
  tailorBtn.innerHTML = '<span class="spinner"></span><span>Tailoring Resume...</span>';
  tailorBtn.classList.add('loading');

  // tailorStatus.textContent = 'Tailoring...';
  // tailorStatus.className = 'status';
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
    // updateResumeStatus();

    tailorStatus.textContent = 'Done. Review the preview below.';
    tailorStatus.className = 'status success';
  } catch (err) {
    console.log(err);
    tailorStatus.textContent = 'Something went wrong: ' + err.message;
    tailorStatus.className = 'status error';
  } finally {
    tailorBtn.disabled = false;
    tailorBtn.innerHTML = originalBtnContent;
    tailorBtn.classList.remove('loading');
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

// goToApplyBtn.addEventListener('click', () => switchPage('apply'));

// ========== APPLY PAGE ==========
const appUrl = document.getElementById('appUrl');
const startAgentBtn = document.getElementById('startAgentBtn');
const scanPageBtn = document.getElementById('scanPageBtn');
const beginBtn = document.getElementById('beginBtn');
const resumeDot = document.getElementById('resumeDot');
// const resumeReadyText = document.getElementById('resumeReadyText');
const agentLog = document.getElementById('agentLog');
const logEntries = document.getElementById('logEntries');
const confirmBox = document.getElementById('confirmBox');
const confirmText = document.getElementById('confirmText');
// const approveBtn = document.getElementById('approveBtn');
// const rejectBtn = document.getElementById('rejectBtn');
const applyStatus = document.getElementById('applyStatus');

// function updateResumeStatus() {
//   if (state.tailoredResumePath) {
//     resumeDot.classList.add('ready');
//     resumeReadyText.textContent = 'Tailored resume ready ✓';
//     startAgentBtn.disabled = !appUrl.value;
//   }
  
//   else {
//     resumeDot.classList.remove('ready');
//     resumeReadyText.textContent = 'No tailored resume yet — tailor one first';
//     startAgentBtn.disabled = true;
//   }
// }

// appUrl.addEventListener('input', updateResumeStatus);

function addLog(message, type = '') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const time = new Date().toLocaleTimeString();
  entry.innerHTML = `<span class="time">[${time}]</span>${message}`;
  logEntries.appendChild(entry);
  logEntries.scrollTop = logEntries.scrollHeight;
}

startAgentBtn.addEventListener('click', async () => {
  if (!appUrl.value) return;

  agentLog.classList.remove('hidden');
  logEntries.innerHTML = '';
  addLog('Launching browswer...', 'action');
  // startAgentBtn.disabled = true;
  applyStatus.className = 'status';
  applyStatus.textContent = 'Browser activating...';

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
    scanPageBtn.classList.remove('hidden');
    applyStatus.textContent = 'Browser running...';
    //startAgentBtn.classList.add('hidden'); // make sure start browser button is hidden after...
    
  } catch (err) {
    addLog('Error: ' + err.message, 'warning');
    applyStatus.textContent = 'Agent failed to start.';
    applyStatus.className = 'status error';
  }
});


scanPageBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/apply/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();

    // // track browser id
    // state.browserSessionId = data.session_id;

    // addLog('Browser launched and navigated to URL', 'success');
    // addLog(data.message || 'Awaiting first step...', 'action');

    // beginBtn.classList.remove('hidden');
    // applyStatus.textContent = 'Browser running...';
    //startAgentBtn.classList.add('hidden'); // make sure start browser button is hidden after...
    
  } catch (err) {
    addLog('Scan Page Error: ' + err.message, 'warning');
  }

});


// ------
// Begin applying with agent button
// -----
beginBtn.addEventListener('click', async () => {
  console.log("Begin button clcked....");
  if (!state.browserSessionId) return;

  console.log("Begin button clcked....222222222222");

  // Save original button content and show loading state
  const originalBtnContent = beginBtn.innerHTML;
  beginBtn.disabled = true;
  beginBtn.innerHTML = '<span class="spinner"></span><span>Filling forms...</span>';
  beginBtn.classList.add('loading');

  addLog('Agent filling forms on current page...', 'action');

  try {
    const res = await fetch('/api/apply/fillform', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
    const data = await res.json();

    addLog('Page forms have been filled', 'success');
    addLog(`Time Elapsed: ${data.time_elapsed}`, 'action');
    console.log('Retruned data after fill forms:', data);

    // show model summary of results
    // fields: filled, skipped, errors
    const agentSummary = results(data.summary);
    addLog(`Form Fields: ${agentSummary}`, 'action');

    // confirmText.textContent = agentSummary;
    // confirmBox.classList.remove('hidden');
  } catch (err) {
    addLog('Begin failed: ' + err.message, 'warning');
  } finally {
    // Restore button (use finally so it always runs, even on error)
    beginBtn.disabled = false;
    beginBtn.innerHTML = originalBtnContent;
    beginBtn.classList.remove('loading');
  }
});


// ------
// Continue applying with agent button
// -----
// approveBtn.addEventListener('click', async () => {
//   addLog('User approved — continuing to next step', 'success');
//   confirmBox.classList.add('hidden');

// });


// ------
// Stop applying with agent button
// -----
// rejectBtn.addEventListener('click', async () => {
//   addLog('User stopped the agent', 'warning');
//   confirmBox.classList.add('hidden');
//   startAgentBtn.disabled = false;
//   applyStatus.textContent = 'Agent stopped by user.';

// });



// results = {"filled": 0, "skipped": 0, "errors": []}


function results(summary){
    const resultString = `
      Filled: ${summary.filled}\n
      Skipped: ${summary.skipped}\n
      Errors: ${summary.errors.length}
    `
    return resultString;
}


// ------------------------------------------------------------------------------------
// Config page
// write config page here

// ------------------------------------------------------------------------------------
// CONFIG PAGE
// ------------------------------------------------------------------------------------

const skillsStatus = document.getElementById('skillsStatus');
// const saveConfigBtn = document.getElementById('saveConfigBtn');
const configStatus = document.getElementById('configStatus');


// Skills elements
const skillSearch = document.getElementById('skillSearch');
const skillCategoryFilter = document.getElementById('skillCategoryFilter');
const skillDropdown = document.getElementById('skillDropdown');
const userSkillsBadges = document.getElementById('userSkillsBadges');

// Cached catalog of available skills (fetched once on page load)
let skillCatalog = [];

// User's skills as last loaded from server (baseline for comparison)
let originalUserSkills = [];
// User's currently selected skills (just names for now)
let userSkills = [];

// Const skills category list (matches what the seed file uses)
const SKILL_CATEGORIES = [
  'Language',
  'Frontend',
  'Backend',
  'Mobile',
  'Database',
  'Cloud',
  'DevOps',
  'Architecture',
  'Networking',
  'Tools',
];





// Populate the category filter <select>
function populateCategoryFilter() {
  for (const cat of SKILL_CATEGORIES) {
    const opt = document.createElement('option');
    opt.value = cat;
    opt.textContent = cat;
    skillCategoryFilter.appendChild(opt);
  }
}


// Load Skills Data
// Skills catalog for skills dropdown list
async function loadSkillCatalog() {
  try {
    const res = await fetch('/api/data/skills/catalog');
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    skillCatalog = await res.json();
    console.log('Skill catalog loaded:', skillCatalog);
    skillsStatus.textContent = `${skillCatalog.length} skills available.`;
  } catch (err) {
    console.log(err);
    skillsStatus.textContent = 'Failed to load skill catalog: ' + err.message;
    skillsStatus.className = 'status error';
  }
}

async function loadUserSkills() {
  try {
    const res = await fetch('/api/data/skills');
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const rows = await res.json();

    // API returns full skill rows; we only need the names client-side
    const names = rows.map(r => r.name);

    originalUserSkills = [...names];      // immutable baseline
    userSkills = [...names];              // working copy

    console.log('User skills loaded:', userSkills);
    renderBadges();
    updateSaveButton();
  } catch (err) {
    console.log(err);
  }
}


// Filter the catalog by search term + category, return matching skills
function getFilteredSkills() {
  const term = skillSearch.value.trim().toLowerCase();
  const cat = skillCategoryFilter.value;

  // No search and no category? hide the dropdown
  if (!term && !cat) return null;

  return skillCatalog.filter(s => {
    const matchesTerm = !term || s.name.toLowerCase().includes(term);
    const matchesCat = !cat || s.category === cat;
    return matchesTerm && matchesCat;
  });
}

// Render the dropdown of matching skills
function renderDropdown() {
  const matches = getFilteredSkills();

  if (matches === null) {
    skillDropdown.classList.add('hidden');
    skillDropdown.innerHTML = '';
    return;
  }

  skillDropdown.classList.remove('hidden');

  if (matches.length === 0) {
    skillDropdown.innerHTML = '<div class="skill-dropdown-empty">No skills match.</div>';
    return;
  }

  skillDropdown.innerHTML = '';
  for (const skill of matches) {
    const item = document.createElement('div');
    const alreadyAdded = userSkills.includes(skill.name);
    item.className = 'skill-dropdown-item' + (alreadyAdded ? ' disabled' : '');
    item.innerHTML = `
      <span>${skill.name}</span>
      <span class="skill-cat">${skill.category || ''}</span>
    `;
    if (!alreadyAdded) {
      item.addEventListener('click', () => addUserSkill(skill.name));
    }
    skillDropdown.appendChild(item);
  }
}

// Render the user's selected skills as badges
function renderBadges() {
  userSkillsBadges.innerHTML = '';

  if (userSkills.length === 0) {
    userSkillsBadges.innerHTML = '<span class="skills-badges-empty">No skills added yet.</span>';
    return;
  }

  for (const name of userSkills) {
    const badge = document.createElement('span');
    badge.className = 'skill-badge';
    badge.innerHTML = `${name}<span class="remove" data-skill="${name}">×</span>`;
    userSkillsBadges.appendChild(badge);
  }

  // Wire up remove buttons
  userSkillsBadges.querySelectorAll('.remove').forEach(el => {
    el.addEventListener('click', () => removeUserSkill(el.dataset.skill));
  });
}

function addUserSkill(name) {
  if (userSkills.includes(name)) return;
  userSkills.push(name);
  renderBadges();
  renderDropdown();
  updateSaveButton();
}

function removeUserSkill(name) {
  userSkills = userSkills.filter(s => s !== name);
  renderBadges();
  renderDropdown();
  updateSaveButton();
}

// Wire up search/filter inputs
skillSearch.addEventListener('input', renderDropdown);
skillCategoryFilter.addEventListener('change', renderDropdown);

// Hide dropdown when clicking outside the skills section
document.addEventListener('click', (e) => {
  const section = document.getElementById('skillsSection');
  if (section && !section.contains(e.target)) {
    skillDropdown.classList.add('hidden');
  }
});

// Re-show dropdown when focusing search again (if it has content)
skillSearch.addEventListener('focus', renderDropdown);



const saveSkillsBtn = document.getElementById('saveSkillsBtn');

function skillsChanged() {
  if (userSkills.length !== originalUserSkills.length) return true;
  // Order-independent comparison via sorted join
  const a = [...userSkills].sort().join('|');
  const b = [...originalUserSkills].sort().join('|');
  return a !== b;
}

function updateSaveButton() {
  saveSkillsBtn.disabled = !skillsChanged();
}

saveSkillsBtn.addEventListener('click', async () => {
  if (!skillsChanged()) return;

  const original = saveSkillsBtn.innerHTML;
  saveSkillsBtn.disabled = true;
  saveSkillsBtn.innerHTML = '<span class="spinner"></span><span>Saving...</span>';

  try {
    const res = await fetch('/api/data/skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skills: userSkills }),
    });
    if (!res.ok) throw new Error(`Server error (${res.status})`);

    // Sync baseline to current — button greys out again
    originalUserSkills = [...userSkills];
    updateSaveButton();
    // skillsStatus.textContent = `Skills Saved.`;
    configStatus.textContent = `Skills Saved.`;
  } catch (err) {
    console.log('Save failed:', err);
  } finally {
    saveSkillsBtn.innerHTML = original;
    updateSaveButton(); // re-evaluate disabled state
  }
});

// Model form field first

// User data form

// Init
populateCategoryFilter();
renderBadges();
loadSkillCatalog();
loadUserSkills();

// Model form field first

// Skills form list

// User data form

// ------------------------------------------------------------------------------------
// PROFILE
// ------------------------------------------------------------------------------------

const profileSection = document.getElementById('profileSection');
const profileEditBtn = document.getElementById('profileEditBtn');
const profileSaveBtn = document.getElementById('profileSaveBtn');
const profileCancelBtn = document.getElementById('profileCancelBtn');

// Last-loaded profile (used to revert on cancel)
let originalProfile = {};

// All boolean field names — used to format Yes/No in view mode
const PROFILE_BOOL_FIELDS = new Set([
  'requires_sponsorship_now',
  'requires_sponsorship_future',
  'willing_to_relocate',
  'open_to_travel',
  'is_18_or_older',
  'can_provide_work_documents',
  'non_compete_active',
  'previously_employed_here',
]);

async function loadProfile() {
  try {
    const res = await fetch('/api/data/profile');
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const data = await res.json();
    originalProfile = data || {};
    renderProfile(originalProfile);
  } catch (err) {
    console.log('Failed to load profile:', err);
  }
}

// Push values into both the spans (view) and inputs (edit)
function renderProfile(data) {
  const valueEls = profileSection.querySelectorAll('.profile-field-value');
  const inputEls = profileSection.querySelectorAll('.profile-field-input');

  valueEls.forEach(el => {
    const key = el.dataset.field;
    const raw = data[key];

    if (raw === null || raw === undefined || raw === '') {
      el.textContent = '';
      el.classList.add('empty');
    } else if (PROFILE_BOOL_FIELDS.has(key)) {
      el.textContent = Number(raw) === 1 ? 'Yes' : 'No';
      el.classList.remove('empty');
    } else {
      el.textContent = raw;
      el.classList.remove('empty');
    }
  });

  inputEls.forEach(el => {
    const key = el.dataset.field;
    const raw = data[key];
    if (PROFILE_BOOL_FIELDS.has(key)) {
      el.value = String(Number(raw) || 0);
    } else {
      el.value = raw ?? '';
    }
  });
}

// Read current input values back into a flat object
function collectProfileForm() {
  const out = {};
  profileSection.querySelectorAll('.profile-field-input').forEach(el => {
    const key = el.dataset.field;
    let val = el.value;
    if (PROFILE_BOOL_FIELDS.has(key)) {
      val = Number(val) === 1 ? 1 : 0;
    } else {
      val = val.trim();
    }
    out[key] = val;
  });
  return out;
}

function setProfileMode(mode) {
  // mode: 'view' or 'edit'
  profileSection.classList.toggle('profile-view-mode', mode === 'view');
  profileSection.classList.toggle('profile-edit-mode', mode === 'edit');
  profileEditBtn.classList.toggle('hidden', mode === 'edit');
}

profileEditBtn.addEventListener('click', () => {
  setProfileMode('edit');
});

profileCancelBtn.addEventListener('click', () => {
  // Revert inputs to last loaded values
  renderProfile(originalProfile);
  setProfileMode('view');
});

profileSaveBtn.addEventListener('click', async () => {
  const payload = collectProfileForm();

  const original = profileSaveBtn.innerHTML;
  profileSaveBtn.disabled = true;
  profileSaveBtn.innerHTML = '<span class="spinner"></span><span>Saving...</span>';

  try {
    const res = await fetch('/api/data/profile', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`Server error (${res.status})`);

    originalProfile = payload;
    renderProfile(originalProfile);
    setProfileMode('view');
    // console.log('Profile saved.');
    configStatus.textContent = `Profile Saved.`;
  } catch (err) {
    console.log('Profile save failed:', err);
  } finally {
    profileSaveBtn.innerHTML = original;
    profileSaveBtn.disabled = false;
  }
});

// Init in view mode
setProfileMode('view');
loadProfile();




// ============================================================
// MODEL CONFIG — Local tab (Ollama)
// ============================================================

// ============================================================
// MODEL CATALOG
// Every entry mirrors the server schema:
//   { provider, model_name, host, api_key_env, category, desc }
// `host` is the default; user can override.
// `api_key_env` is the conventional env var name for that provider.
// ============================================================

const MODEL_CATALOG = [
  // ============== OLLAMA (local) ==============
  // host defaults to local daemon, no api key needed
  { provider: 'ollama', model_name: 'llama3.2',          host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.2 — small, fast, great default' },
  { provider: 'ollama', model_name: 'llama3.2:1b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.2 1B' },
  { provider: 'ollama', model_name: 'llama3.2:3b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.2 3B' },
  { provider: 'ollama', model_name: 'llama3.1',          host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.1 — workhorse, tool-calling' },
  { provider: 'ollama', model_name: 'llama3.1:8b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.1 8B' },
  { provider: 'ollama', model_name: 'llama3.1:70b',      host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.1 70B' },
  { provider: 'ollama', model_name: 'llama3.1:405b',     host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Meta Llama 3.1 405B' },
  { provider: 'ollama', model_name: 'llama3.3:70b',      host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Llama 3.3 70B — ~405B quality at 70B' },
  { provider: 'ollama', model_name: 'llama4',            host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Llama 4 — MoE, multimodal' },
  { provider: 'ollama', model_name: 'qwen2.5',           host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen2.5 — strong all-rounder, 128K ctx' },
  { provider: 'ollama', model_name: 'qwen2.5:7b',        host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen2.5 7B' },
  { provider: 'ollama', model_name: 'qwen2.5:14b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen2.5 14B' },
  { provider: 'ollama', model_name: 'qwen2.5:32b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen2.5 32B' },
  { provider: 'ollama', model_name: 'qwen2.5:72b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen2.5 72B' },
  { provider: 'ollama', model_name: 'qwen3',             host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen3 — tools + thinking modes' },
  { provider: 'ollama', model_name: 'qwen3:8b',          host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen3 8B' },
  { provider: 'ollama', model_name: 'qwen3:32b',         host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen3 32B' },
  { provider: 'ollama', model_name: 'qwen3.6:27b',       host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Qwen3.6 27B — newest Qwen dense' },
  { provider: 'ollama', model_name: 'gemma3',            host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Gemma 3 — vision, single-GPU friendly' },
  { provider: 'ollama', model_name: 'gemma3:4b',         host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Gemma 3 4B' },
  { provider: 'ollama', model_name: 'gemma3:12b',        host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Gemma 3 12B' },
  { provider: 'ollama', model_name: 'gemma3:27b',        host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Gemma 3 27B' },
  { provider: 'ollama', model_name: 'gemma4',            host: 'http://localhost:11434', api_key_env: null, category: 'Local',   desc: 'Gemma 4 — Google, vision + tools' },

  // ============== GOOGLE ==============
  { provider: 'google',    model_name: 'gemini-2.5-flash',        host: 'https://generativelanguage.googleapis.com', api_key_env: 'GOOGLE_API_KEY', category: 'Cloud', desc: 'Gemini 2.5 Flash — fast' },
];

// ============== ANTHROPIC ==============
//   { provider: 'anthropic', model_name: 'claude-opus-4-7',         host: 'https://api.anthropic.com', api_key_env: 'ANTHROPIC_API_KEY', category: 'Cloud · Anthropic', desc: 'Claude Opus 4.7 — most capable' },
//   { provider: 'anthropic', model_name: 'claude-sonnet-4-6',       host: 'https://api.anthropic.com', api_key_env: 'ANTHROPIC_API_KEY', category: 'Cloud · Anthropic', desc: 'Claude Sonnet 4.6 — balanced' },
//   { provider: 'anthropic', model_name: 'claude-haiku-4-5',        host: 'https://api.anthropic.com', api_key_env: 'ANTHROPIC_API_KEY', category: 'Cloud · Anthropic', desc: 'Claude Haiku 4.5 — fast & cheap' },
// // ============== OPENAI ==============
//   { provider: 'openai',    model_name: 'gpt-5',                   host: 'https://api.openai.com',    api_key_env: 'OPENAI_API_KEY',    category: 'Cloud · OpenAI',    desc: 'GPT-5 — flagship' },
//   { provider: 'openai',    model_name: 'gpt-5-mini',              host: 'https://api.openai.com',    api_key_env: 'OPENAI_API_KEY',    category: 'Cloud · OpenAI',    desc: 'GPT-5 Mini — fast & cheap' },
//   { provider: 'openai',    model_name: 'gpt-4o',                  host: 'https://api.openai.com',    api_key_env: 'OPENAI_API_KEY',    category: 'Cloud · OpenAI',    desc: 'GPT-4o — multimodal' },



const PROVIDER_NEEDS_KEY = (provider) => provider !== 'ollama';
// let currentModelConfig = null;   // module-level cache of the saved row
let isDirty = false;
let currentModelTypeSelected = 'cloud'; // Either a cloud or local model is selected...

let modelConfigs = [];   // cached saved configs — up to two rows: one local, one cloud

function maskKey(key) {
  // Swap every char for 'x' so the real key never lingers in client memory.
  return key ? 'x'.repeat(key.length) : null;
}

function configKind(cfg) {
  // 'local' for Ollama / locally-hosted, 'cloud' otherwise.
  if (cfg.provider_category) {
    return cfg.provider_category.toLowerCase().startsWith('local') ? 'local' : 'cloud';
  }
  return (cfg.host || '').includes('localhost') ? 'local' : 'cloud';
}

function getConfigByKind(kind) {
  return modelConfigs.find(c => configKind(c) === kind) || null;
}


function markDirty() {
  isDirty = true;
  validateAndToggleSave();
}

function markPristine() {
  isDirty = false;
  validateAndToggleSave();
}

// ---------- Helpers ----------
function findCatalogEntry(modelName) {
  return MODEL_CATALOG.find(m => m.model_name === modelName);
}

function getActiveTab() {
  const active = document.querySelector('.model-tab.active');
  return active ? active.dataset.tab : 'local';
}

function getCurrentEntry() {
  // Returns { provider, model_name, host, api_key_env } for whatever's selected,
  // resolving custom inputs against the active tab.
  const tab    = getActiveTab();
  const select = document.getElementById('modelSelect');
  const value  = select.value;

  // Custom-entered model name
  if (value === '__custom__') {
    const customName = document.getElementById('customModelInput').value.trim();
    return {
      provider: tab === 'local' ? 'ollama' : null,   // user must pick provider on cloud tab
      model_name: customName,
      host: tab === 'local' ? 'http://localhost:11434' : null,
      api_key_env: null,
    };
  }

  return findCatalogEntry(value) || null;
}

// ---------- Validation ----------
const MODEL_ID_RE = /^[a-zA-Z0-9._\-\/]+(?::[a-zA-Z0-9._\-]+)?$/;

function validateAndToggleSave() {
  const saveBtn = document.getElementById('saveModelBtn');
  const entry   = getCurrentEntry();

  // Not dirty = nothing to save
  if (!isDirty) {
    saveBtn.disabled = true;
    return;
  }

  if (!entry || !entry.model_name || !MODEL_ID_RE.test(entry.model_name)) {
    saveBtn.disabled = true;
    return;
  }

  // Cloud providers need an API key in the input
  if (PROVIDER_NEEDS_KEY(entry.provider)) {
    const apiKey = document.getElementById('apiKeyInput')?.value.trim();
    if (!apiKey) {
      saveBtn.disabled = true;
      return;
    }
  }

  saveBtn.disabled = false;
}

// Post model info
// --------------------------------------
// ---------- Save ----------
async function saveModelConfig() {
  const saveBtn = document.getElementById('saveModelBtn');
  const status  = document.getElementById('modelStatusConfig');
  const entry   = getCurrentEntry();

  if (!entry) return;

  // Allow user-overridden host (port-only or full URL)
  const hostInput = document.getElementById('ollamaHost');
  const host = hostInput?.value.trim() || entry.host;
  const modelApiKey = document.getElementById('apiKeyInput');
  const apiKey = modelApiKey?.value.trim();
  const providerCategory = entry.category.toLowerCase();


  const payload = {
    provider:    entry.provider,
    provider_category: providerCategory,
    model_name:  entry.model_name,
    host:        host,
    api_key_env: apiKey,   // env var NAME, not the key itself
  };

  console.log(`Payload for model save config POST Pre- before: ${payload}`);
  console.log(`Payload for model save config POST Pre- before: ${payload}`);

  // For cloud, the actual API key gets sent alongside (server stores it in env / vault,
  // and writes the env-var name to the DB)
  // if (PROVIDER_NEEDS_KEY(entry.provider)) {
  //   payload.api_key = document.getElementById('apiKeyInput').value.trim();
  // }

  saveBtn.disabled = true;
  status.textContent = 'Saving…';
  status.className = 'status';

  try {
    console.log(`Payload for model save config POST: ${payload}`);
    const res = await fetch('/api/data/model', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);

    status.textContent = `Saved: ${entry.model_name}`;
    status.className = 'status success';
    markPristine();

    const kind = getActiveTab();

    // Keep the local cache in sync so the toggle knows this side now exists
    const savedCfg = {
      provider:          entry.provider,
      provider_category: providerCategory,
      model_name:        entry.model_name,
      host:              host,
      api_key_env:       maskKey(apiKey),
    };
    const idx = modelConfigs.findIndex(c => configKind(c) === kind);
    if (idx >= 0) modelConfigs[idx] = savedCfg;   // replace existing side
    else          modelConfigs.push(savedCfg);    // add the new side

    currentModelTypeSelected = kind;

    syncModelToggle();


    // send another request to restart model connection / server
    await restart_model_server();

  } catch (err) {
    status.textContent = `Save failed: ${err.message}`;
    status.className = 'status error';
  } finally {
    validateAndToggleSave();
  }
}

async function restart_model_server() {
  // Flip pill to "restarting" immediately — also pause polling so a stale
  // "stopped" response doesn't briefly flicker in while the server restarts
  stopModelStatusPolling();

  const entry = getCurrentEntry();
  renderModelStatus({
    restarting: true,
    provider:   entry?.provider,
    model_name: entry?.model_name,
  });

  try {
    const res = await fetch('/api/data/model/updated', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_category: currentModelTypeSelected })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) throw new Error(data.error || `HTTP ${res.status}`);

    console.log('Successful new model config restart');

    // Server returned fresh status in the response — use it directly
    //renderModelStatus(data);

  } catch (err) {
    console.log(`Issues restarting new model config: ${err}`);
    renderModelStatus({
      running: false,
      error: `Restart failed: ${err.message}`,
    });
  } finally {
    // Resume polling to keep status fresh
    startModelStatusPolling(5000);
  }
}

function populateModelSelect(tab = 'cloud') {
  const select = document.getElementById('modelSelect');

  // Filter catalog by the active tab
  const filtered = MODEL_CATALOG.filter(m =>
    tab === 'local' ? m.provider === 'ollama' : m.provider !== 'ollama'
  );

  // Group by category
  const groups = {};
  for (const m of filtered) (groups[m.category] ||= []).push(m);

  // Wipe existing dynamic options (keep placeholder + custom)
  select.querySelectorAll('optgroup, option:not([value=""]):not([value="__custom__"])').forEach(n => n.remove());
  const customOpt = select.querySelector('option[value="__custom__"]');

  for (const [cat, items] of Object.entries(groups)) {
    const og = document.createElement('optgroup');
    og.label = cat;
    for (const m of items) {
      const opt = document.createElement('option');
      opt.value = m.model_name;
      opt.textContent = `${m.model_name}  —  ${m.desc}`;
      opt.dataset.desc = m.desc;
      og.appendChild(opt);
    }
    select.insertBefore(og, customOpt);
  }

  // Reset select to placeholder when switching tabs
  select.value = '';
}


function initModelTabs() {
  document.querySelectorAll('.model-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      document.querySelectorAll('.model-tab').forEach(b => b.classList.toggle('active', b === btn));
      document.querySelectorAll('.model-tab-panel').forEach(p => {
        p.classList.toggle('hidden', p.id !== `modelTab-${target}`);
      });

      const apiKeyRow = document.getElementById('apiKeyRow');
      if (apiKeyRow) apiKeyRow.classList.toggle('hidden', target === 'local');

      hydrateTab(target);   // restore saved config for this tab from the cache
    });
  });
}

// function initModelTabs() {
//   document.querySelectorAll('.model-tab').forEach(btn => {
//     btn.addEventListener('click', () => {
//       const target = btn.dataset.tab;
//       document.querySelectorAll('.model-tab').forEach(b => b.classList.toggle('active', b === btn));
//       document.querySelectorAll('.model-tab-panel').forEach(p => {
//         p.classList.toggle('hidden', p.id !== `modelTab-${target}`);
//       });

//       // Refresh dropdown for the active tab
//       populateModelSelect(target);

//       // Show/hide API key row based on tab
//       const apiKeyRow = document.getElementById('apiKeyRow');
//       if (apiKeyRow) apiKeyRow.classList.toggle('hidden', target === 'local');

//       // Reset description + custom
//       document.getElementById('modelDescription').textContent = '';
//       document.getElementById('customModelRow').classList.add('hidden');
//       markDirty();
//     });
//   });
// }

function initModelConfig() {
  populateModelSelect('local');
  initModelTabs();

  const select       = document.getElementById('modelSelect');
  const customRow    = document.getElementById('customModelRow');
  const customInput  = document.getElementById('customModelInput');
  const description  = document.getElementById('modelDescription');
  const saveBtn      = document.getElementById('saveModelBtn');
  const hostInput    = document.getElementById('ollamaHost');
  const apiKeyInput  = document.getElementById('apiKeyInput');

  select.addEventListener('change', () => {
    const isCustom = select.value === '__custom__';
    customRow.classList.toggle('hidden', !isCustom);

    const opt = select.selectedOptions[0];
    description.textContent = (!isCustom && opt?.dataset.desc) ? opt.dataset.desc : '';

    // Auto-fill host from catalog entry so user sees the default
    const entry = findCatalogEntry(select.value);
    if (entry && hostInput) hostInput.value = entry.host;

    markDirty();
  });

  customInput.addEventListener('input', markDirty);
  hostInput?.addEventListener('input',  markDirty);
  apiKeyInput?.addEventListener('input', markDirty);
  saveBtn.addEventListener('click', saveModelConfig);
}


// async function loadModelConfig() {
//   try {
//     const res  = await fetch('/api/data/model', { method: 'GET' });
//     const data = await res.json().catch(() => ({}));

//     console.log(`Saved Model details: ${data}`);
//     console.log(`Saved Model details: ${data.provider}`);
//     if (!res.ok) {
//       console.warn('Failed to load model config:', data.error || res.status);
//       return null;
//     }

//        // null if nothing saved yet
//     hydrateModelConfig(data);
//     return data;
//   } catch (err) {
//     console.error('loadModelConfig error:', err);
//     return null;
//   }
// }

async function loadModelConfig() {
  try {
    const res  = await fetch('/api/data/model', { method: 'GET' });
    const data = await res.json().catch(() => ([]));

    if (!res.ok) {
      console.warn('Failed to load model config:', data.error || res.status);
      return null;
    }

    // Endpoint now returns an array of rows (0–2). Tolerate a {configs:[...]} wrapper too.
    const rows = Array.isArray(data) ? data : (data.configs || []);

    

    // Cache them, masking the API key so plaintext never sits in client memory.
    modelConfigs = rows.map(cfg => ({
      ...cfg,
      api_key_env: maskKey(cfg.api_key_env),
    }));

    console.log(`Returned models config'd: ${modelConfigs}`);

    hydrateModelConfig();
    return modelConfigs;
  } catch (err) {
    console.error('loadModelConfig error:', err);
    return null;
  }
}

function hydrateTab(tab) {
  const cfg = getConfigByKind(tab);

  // For cloud, set provider dropdown first so the right models filter in.
  if (tab === 'cloud' && cfg) {
    const providerSelect = document.getElementById('cloudProviderSelect');
    if (providerSelect) providerSelect.value = cfg.provider;
  }
  populateModelSelect(tab);

  const select      = document.getElementById('modelSelect');
  const description = document.getElementById('modelDescription');
  const customRow   = document.getElementById('customModelRow');
  const customInput = document.getElementById('customModelInput');
  const apiKeyInput = document.getElementById('apiKeyInput');
  const hostInput   = document.getElementById('ollamaHost');

  // Nothing saved for this tab → reset to placeholder.
  if (!cfg) {
    select.value = '';
    description.textContent = '';
    customRow.classList.add('hidden');
    if (apiKeyInput) { apiKeyInput.value = ''; apiKeyInput.placeholder = 'Enter API key'; }
    markPristine();
    return;
  }

  // Select the saved model, or fall back to the custom input.
  const optionExists = [...select.options].some(o => o.value === cfg.model_name);
  if (optionExists) {
    select.value = cfg.model_name;
    description.textContent = select.selectedOptions[0]?.dataset.desc || '';
    customRow.classList.add('hidden');
  } else {
    select.value = '__custom__';
    customRow.classList.remove('hidden');
    customInput.value = cfg.model_name;
    description.textContent = '';
  }

  // Host (local only).
  if (tab === 'local' && cfg.host && hostInput) {
    hostInput.value = cfg.host;
  }

  // API key — already masked; surface as a placeholder hint only.
  if (tab === 'cloud' && apiKeyInput) {
    apiKeyInput.value = '';
    apiKeyInput.placeholder = cfg.api_key_env ? `Saved: ${cfg.api_key_env}` : 'Enter API key';
  }

  markPristine();
}


function hydrateModelConfig() {
  const targetTab = 'cloud';            // load the cloud side on startup
  currentModelTypeSelected = targetTab;

  // Activate the cloud tab
  document.querySelectorAll('.model-tab').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === targetTab);
  });
  document.querySelectorAll('.model-tab-panel').forEach(p => {
    p.classList.toggle('hidden', p.id !== `modelTab-${targetTab}`);
  });

  const apiKeyRow = document.getElementById('apiKeyRow');
  if (apiKeyRow) apiKeyRow.classList.toggle('hidden', targetTab === 'local');

  hydrateTab(targetTab);   // fills the fields from the cached cloud config
  syncModelToggle();
}

// load model config data / form setup on load
document.addEventListener('DOMContentLoaded', async () => {
  initModelConfig();
  await loadModelConfig();   // hydrate from saved row
  initModelToggle();
});


// Toggle Cloud or Local 
// ---------------
function initModelToggle() {
  const toggle = document.getElementById('modelToggle');
  if (!toggle) return;

  toggle.querySelectorAll('.model-toggle-option').forEach(btn => {
    btn.addEventListener('click', async () => {
      const kind = btn.dataset.kind;                 // 'cloud' | 'local'
      if (kind === currentModelTypeSelected) return; // already active
      if (!getConfigByKind(kind)) return;            // nothing saved for that side

      currentModelTypeSelected = kind;
      syncModelToggle();              // instant visual feedback
      await restart_model_server();   // bring the now-active config online
    });
  });

  syncModelToggle();
}

// Reflect currentModelTypeSelected + which configs exist into the toggle
function syncModelToggle() {
  const toggle = document.getElementById('modelToggle');
  if (!toggle) return;

  toggle.dataset.active = currentModelTypeSelected;   // drives the slider

  toggle.querySelectorAll('.model-toggle-option').forEach(btn => {
    const kind = btn.dataset.kind;
    btn.classList.toggle('active', kind === currentModelTypeSelected);
    btn.disabled = !getConfigByKind(kind);            // grey out unsaved sides
  });
}








// User experience
// --------------------------------------------------
// ============================================================
// EXPERIENCE
// ============================================================

const experienceList   = document.getElementById('experienceList');
const experienceAddBtn = document.getElementById('experienceAddBtn');
const experienceStatus = document.getElementById('experienceStatus');

let experienceEntries = [];   // cached list from server

const BOOL_EXP_FIELDS = new Set(['is_current']);

// ---------- Fetch ----------
async function loadExperience() {
  try {
    const res = await fetch('/api/data/experience');
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const data = await res.json();
    experienceEntries = Array.isArray(data) ? data : (data.experience || []);
    renderExperienceList();
  } catch (err) {
    console.log('Failed to load experience:', err);
    experienceStatus.textContent = 'Failed to load experience.';
  }
}

// ---------- Render ----------
function renderExperienceList() {
  experienceList.innerHTML = '';

  if (!experienceEntries.length) {
    experienceStatus.textContent = 'No experience added yet.';
    return;
  }
  experienceStatus.textContent = `${experienceEntries.length} entr${experienceEntries.length === 1 ? 'y' : 'ies'}.`;

  // Sort by sort_order, then current jobs first, then by start_date desc
  const sorted = [...experienceEntries].sort((a, b) => {
    if ((a.sort_order || 0) !== (b.sort_order || 0)) {
      return (a.sort_order || 0) - (b.sort_order || 0);
    }
    if (a.is_current !== b.is_current) return b.is_current - a.is_current;
    return (b.start_date || '').localeCompare(a.start_date || '');
  });

  for (const entry of sorted) {
    experienceList.appendChild(renderExperienceCard(entry));
  }
}

function renderExperienceCard(entry) {
  const tpl = document.getElementById('experienceCardTemplate').content.cloneNode(true);
  const card = tpl.querySelector('.experience-card');

  card.querySelector('.experience-card-title').textContent   = entry.title || '(Untitled role)';
  card.querySelector('.experience-card-company').textContent = entry.company || '';

  const dateRange = formatDateRange(entry.start_date, entry.end_date, entry.is_current);
  const meta = [dateRange, entry.location].filter(Boolean).join('  •  ');
  card.querySelector('.experience-card-meta').textContent = meta;

  card.querySelector('.experience-card-summary').textContent = entry.summary || '';

  // Tech stack chips
  const stackEl = card.querySelector('.experience-card-stack');
  const stack = parseTechStack(entry.tech_stack);
  for (const tech of stack) {
    const chip = document.createElement('span');
    chip.className = 'tech-chip';
    chip.textContent = tech;
    stackEl.appendChild(chip);
  }

  // Edit button → swap card for editor
  card.querySelector('.experience-edit-btn').addEventListener('click', () => {
    const editor = buildEditor(entry, card);
    card.replaceWith(editor);
  });

  return card;
}

function formatDateRange(start, end, isCurrent) {
  const fmt = (s) => {
    if (!s) return '';
    // YYYY-MM → "Jan 2024"
    const [y, m] = s.split('-');
    if (!y) return s;
    if (!m) return y;
    const date = new Date(Number(y), Number(m) - 1, 1);
    return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };
  const startStr = fmt(start);
  const endStr   = Number(isCurrent) === 1 ? 'Present' : fmt(end);
  if (!startStr && !endStr) return '';
  return `${startStr || '?'} → ${endStr || '?'}`;
}

function parseTechStack(raw) {
  if (!raw) return [];
  // Stored as JSON array text, but tolerate comma-separated input from earlier saves
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) return parsed.filter(Boolean);
  } catch { /* not JSON, fall through */ }
  return String(raw).split(',').map(s => s.trim()).filter(Boolean);
}

// ---------- Editor ----------
function buildEditor(entry, replaceCard /* nullable */) {
  const tpl    = document.getElementById('experienceEditorTemplate').content.cloneNode(true);
  const editor = tpl.querySelector('.experience-editor');
  const isNew  = !entry || !entry.id;

  // Populate inputs
  editor.querySelectorAll('.profile-field-input').forEach(el => {
    const key = el.dataset.field;
    let val = entry?.[key];
    if (BOOL_EXP_FIELDS.has(key)) {
      el.value = String(Number(val) || 0);
    } else if (key === 'tech_stack') {
      // Display as comma-separated for editing
      el.value = parseTechStack(val).join(', ');
    } else {
      el.value = val ?? '';
    }
  });

  const saveBtn   = editor.querySelector('.experience-save-btn');
  const cancelBtn = editor.querySelector('.experience-cancel-btn');
  const deleteBtn = editor.querySelector('.experience-delete-btn');

  if (!isNew) deleteBtn.classList.remove('hidden');

  saveBtn.addEventListener('click', async () => {
    const payload = collectExperienceForm(editor);
    if (!isNew) payload.id = entry.id;

    const original = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span><span>Saving...</span>';

    try {
      const method = isNew ? 'POST' : 'PATCH';
      const url    = isNew ? '/api/data/experience' : `/api/data/experience/${entry.id}`;
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const saved = await res.json().catch(() => ({}));

      // Update cache
      if (isNew) {
        experienceEntries.push({ ...payload, id: saved.id ?? Date.now() });
      } else {
        experienceEntries = experienceEntries.map(e => e.id === entry.id ? { ...e, ...payload } : e);
      }

      renderExperienceList();
      configStatus.textContent = 'Experience saved.';
    } catch (err) {
      console.log('Experience save failed:', err);
      saveBtn.innerHTML = original;
      saveBtn.disabled = false;
    }
  });

  cancelBtn.addEventListener('click', () => {
    if (isNew) {
      editor.remove();
    } else {
      // Replace editor with original card
      editor.replaceWith(renderExperienceCard(entry));
    }
  });

  deleteBtn.addEventListener('click', async () => {
    if (!confirm(`Delete this experience entry (${entry.title || 'untitled'} @ ${entry.company || '—'})?`)) return;

    try {
      const res = await fetch(`/api/data/experience/${entry.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Server error (${res.status})`);

      experienceEntries = experienceEntries.filter(e => e.id !== entry.id);
      renderExperienceList();
      configStatus.textContent = 'Experience deleted.';
    } catch (err) {
      console.log('Experience delete failed:', err);
    }
  });

  return editor;
}

function collectExperienceForm(editor) {
  const out = {};
  editor.querySelectorAll('.profile-field-input').forEach(el => {
    const key = el.dataset.field;
    let val = el.value;

    if (BOOL_EXP_FIELDS.has(key)) {
      val = Number(val) === 1 ? 1 : 0;
    } else if (key === 'tech_stack') {
      // Store as JSON array text to match the table comment
      const arr = String(val).split(',').map(s => s.trim()).filter(Boolean);
      val = JSON.stringify(arr);
    } else {
      val = val.trim();
    }
    out[key] = val;
  });

  // If is_current=1, blank out end_date
  if (out.is_current === 1) out.end_date = '';

  return out;
}

// ---------- Add new entry ----------
experienceAddBtn.addEventListener('click', () => {
  // Don't allow multiple add-editors at once
  if (experienceList.querySelector('.experience-editor')) return;

  const editor = buildEditor(null, null);
  experienceList.prepend(editor);
});

// ---------- Init ----------
loadExperience();


//  ---------------------------------
//  Education
// ----------------------------------

const educationList   = document.getElementById('educationList');
const educationAddBtn = document.getElementById('educationAddBtn');
const educationStatus = document.getElementById('educationStatus');

let educationEntries = [];

const BOOL_EDU_FIELDS = new Set(['currently_enrolled']);

// ---------- Fetch ----------
async function loadEducation() {
  try {
    const res = await fetch('/api/data/education');
    if (!res.ok) throw new Error(`Server error (${res.status})`);
    const data = await res.json();
    educationEntries = Array.isArray(data) ? data : (data.education || []);
    renderEducationList();
  } catch (err) {
    console.log('Failed to load education:', err);
    educationStatus.textContent = 'Failed to load education.';
  }
}

// ---------- Render ----------
function renderEducationList() {
  educationList.innerHTML = '';

  if (!educationEntries.length) {
    educationStatus.textContent = 'No education added yet.';
    return;
  }
  educationStatus.textContent = `${educationEntries.length} entr${educationEntries.length === 1 ? 'y' : 'ies'}.`;

  const sorted = [...educationEntries].sort((a, b) => {
    if ((a.sort_order || 0) !== (b.sort_order || 0)) {
      return (a.sort_order || 0) - (b.sort_order || 0);
    }
    if (a.currently_enrolled !== b.currently_enrolled) return b.currently_enrolled - a.currently_enrolled;
    return (b.start_date || '').localeCompare(a.start_date || '');
  });

  for (const entry of sorted) {
    educationList.appendChild(renderEducationCard(entry));
  }
}

function renderEducationCard(entry) {
  const tpl = document.getElementById('educationCardTemplate').content.cloneNode(true);
  const card = tpl.querySelector('.education-card');

  card.querySelector('.education-card-title').textContent = entry.school || '(Unnamed school)';

  const subtitle = [entry.degree_type, entry.program].filter(Boolean).join(', ');
  card.querySelector('.education-card-subtitle').textContent = subtitle;

  const dateRange = formatEduDateRange(entry.start_date, entry.end_date, entry.currently_enrolled);
  const gpa = entry.gpa ? `GPA ${entry.gpa}` : '';
  card.querySelector('.education-card-meta').textContent = [dateRange, gpa].filter(Boolean).join('  •  ');

  card.querySelector('.education-card-summary').textContent = entry.summary || '';

  card.querySelector('.education-edit-btn').addEventListener('click', () => {
    const editor = buildEducationEditor(entry, card);
    card.replaceWith(editor);
  });

  return card;
}

function formatEduDateRange(start, end, isEnrolled) {
  const yr = (s) => (s ? String(s).split('-')[0] : '');   // tolerate "YYYY" or "YYYY-MM"
  const startStr = yr(start);
  let endStr;
  if (Number(isEnrolled) === 1) {
    endStr = end ? `Expected ${yr(end)}` : 'Present';
  } else {
    endStr = yr(end);
  }
  if (!startStr && !endStr) return '';
  return `${startStr || '?'} → ${endStr || '?'}`;
}

// ---------- Editor ----------
function buildEducationEditor(entry, replaceCard /* nullable */) {
  const tpl    = document.getElementById('educationEditorTemplate').content.cloneNode(true);
  const editor = tpl.querySelector('.education-editor');
  const isNew  = !entry || !entry.id;

  editor.querySelectorAll('.profile-field-input').forEach(el => {
    const key = el.dataset.field;
    let val = entry?.[key];
    if (BOOL_EDU_FIELDS.has(key)) {
      el.value = String(Number(val) || 0);
    } else {
      el.value = val ?? '';
    }
  });

  const saveBtn   = editor.querySelector('.education-save-btn');
  const cancelBtn = editor.querySelector('.education-cancel-btn');
  const deleteBtn = editor.querySelector('.education-delete-btn');

  if (!isNew) deleteBtn.classList.remove('hidden');

  saveBtn.addEventListener('click', async () => {
    const payload = collectEducationForm(editor);
    if (!isNew) payload.id = entry.id;

    const original = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner"></span><span>Saving...</span>';

    try {
      const method = isNew ? 'POST' : 'PATCH';
      const url    = isNew ? '/api/data/education' : `/api/data/education/${entry.id}`;
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const saved = await res.json().catch(() => ({}));

      if (isNew) {
        educationEntries.push({ ...payload, id: saved.id ?? Date.now() });
      } else {
        educationEntries = educationEntries.map(e => e.id === entry.id ? { ...e, ...payload } : e);
      }

      renderEducationList();
      configStatus.textContent = 'Education saved.';
    } catch (err) {
      console.log('Education save failed:', err);
      saveBtn.innerHTML = original;
      saveBtn.disabled = false;
    }
  });

  cancelBtn.addEventListener('click', () => {
    if (isNew) {
      editor.remove();
    } else {
      editor.replaceWith(renderEducationCard(entry));
    }
  });

  deleteBtn.addEventListener('click', async () => {
    if (!confirm(`Delete this education entry (${entry.program || entry.degree_type || 'untitled'} @ ${entry.school || '—'})?`)) return;

    try {
      const res = await fetch(`/api/data/education/${entry.id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error(`Server error (${res.status})`);

      educationEntries = educationEntries.filter(e => e.id !== entry.id);
      renderEducationList();
      configStatus.textContent = 'Education deleted.';
    } catch (err) {
      console.log('Education delete failed:', err);
    }
  });

  return editor;
}

function collectEducationForm(editor) {
  const out = {};
  editor.querySelectorAll('.profile-field-input').forEach(el => {
    const key = el.dataset.field;
    let val = el.value;
    if (BOOL_EDU_FIELDS.has(key)) {
      val = Number(val) === 1 ? 1 : 0;
    } else {
      val = val.trim();
    }
    out[key] = val;
  });
  return out;
}

// ---------- Add new ----------
educationAddBtn.addEventListener('click', () => {
  if (educationList.querySelector('.education-editor')) return;
  const editor = buildEducationEditor(null, null);
  educationList.prepend(editor);
});

// ---------- Init ----------
loadEducation();








let modelStatusPollTimer = null;

async function fetchModelStatus() {
  try {
    const res = await fetch(`/api/data/model/status?type=${currentModelTypeSelected}`, { method: 'GET' });
    const data = await res.json().catch(() => ({}));
    // request threw error
    if (!res.ok) {
      return { running: false, error: data.error || `HTTP ${res.status}` };
    }
    // req good, but no model configured
    if(!data.configured){
       return { configured: false };
    }
    return data;
  } catch (err) {
    return { running: false, error: err.message };
  }
}

function renderModelStatus(status) {
  const el     = document.getElementById('modelStatus');
  const textEl = el.querySelector('.model-status-text');
  if (!el || !textEl) return;

  el.classList.remove('running', 'stopped', 'unknown', 'restarting');

  // Explicit "restarting" state passed in
  if (status.restarting) {
    el.classList.add('restarting');
    const provider  = status.provider  || '';
    const modelName = status.model_name || '';
    textEl.textContent = 'Restarting Model…';
    el.title = 'Model connection is restarting';
    return;
  }
  else if(!status.configured) {
    el.classList.add('stopped');
    textEl.textContent = `Model is not Configured`;
    el.title =  'Model is not configured';
  }

  if (status.running) {
    el.classList.add('running');
    const provider  = status.provider  || 'ollama';
    const modelName = status.model_name || 'unknown';
    textEl.textContent = `Connected to ${provider} — ${modelName}`;
    el.title = `Host: ${status.host || 'n/a'}\nLoaded: ${(status.loaded_models || []).join(', ') || 'none'}`;
  } else {
    el.classList.add('stopped');
    const reason = status.error ? ` (${status.error})` : '';
    textEl.textContent = `Disconnected`;
    el.title = status.error || 'Model is not running';
  }
}

async function refreshModelStatus() {
  const status = await fetchModelStatus();
  renderModelStatus(status);
}

function startModelStatusPolling(intervalMs = 5000) {
  stopModelStatusPolling();
  refreshModelStatus();  // immediate
  modelStatusPollTimer = setInterval(refreshModelStatus, intervalMs);
}

function stopModelStatusPolling() {
  if (modelStatusPollTimer) {
    clearInterval(modelStatusPollTimer);
    modelStatusPollTimer = null;
  }
}

// Pause polling when tab is hidden (saves resources)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopModelStatusPolling();
  } else {
    startModelStatusPolling(5000);
  }
});

// Kick off on page load
document.addEventListener('DOMContentLoaded', () => {
  // ... your existing init code ...
  startModelStatusPolling(5000);
});

// setup lucide icons
lucide.createIcons();