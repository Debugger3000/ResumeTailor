
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
  startAgentBtn.disabled = true;
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
    applyStatus.textContent = 'Browser running...';
    startAgentBtn.classList.add('hidden'); // make sure start browser button is hidden after...
    
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







// setup lucide icons
lucide.createIcons();