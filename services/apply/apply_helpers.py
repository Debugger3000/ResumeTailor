from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from database.queries.get_user_data_apply import get_user_profile, get_user_skills, get_work_experience
# app/services/page_reader.py

# return page html from playwright session
# async def get_page_html(session):
#     """Return the full rendered HTML of the current page."""
#     return await session.page.content()





def get_full_user_data() -> dict:
    """
    Aggregate user data from all sources into a single flat-ish dict
    suitable for passing to the model.
    """
    print(get_user_profile())
    return {
        **get_user_profile(),          # Flattens keys
        "experience": get_work_experience(),
        "skills": get_user_skills(),
    }


# Input: page object (playwright import), fields (input html fields grabbed from page)
# Fill fields with
async def fill_fields(page_or_frame, fields: list[dict]) -> dict:
    """
    Fill all fields on the page that have a value populated.
    
    Returns a summary dict:
      {
        "filled": int,
        "skipped": int,
        "errors": [{"agent_id": str, "question": str, "error": str}, ...]
      }
    """
    print("fields before fill_fields processes.......")
    print(fields)
    results = {"filled": 0, "skipped": 0, "errors": []}
    
    print(f"=== fill_fields: processing {len(fields)} fields ===")
    
    for field in fields:
        value = field.get("value")
        agent_id = field.get("agent_id")
        question = field.get("question", "")
        kind = field.get("kind")
        
        # Skip fields the model didn't populate
        # Note: False is a valid value for checkboxes, so check explicitly
        if value is None or value == "":
            if kind == "checkbox" and value is False:
                pass  # actually a real value, fall through
            else:
                results["skipped"] += 1
                continue
        
        try:
            await fill_one(page_or_frame, field)
            results["filled"] += 1
            print(f"  filled [{agent_id}] {question!r} -> {value!r}")
        except Exception as e:
            err = {
                "agent_id": agent_id,
                "question": question,
                "error": str(e),
            }
            results["errors"].append(err)
            print(f"  ERROR [{agent_id}] {question!r}: {e}")
    
    print(f"=== fill_fields done: {results['filled']} filled, "
          f"{results['skipped']} skipped, {len(results['errors'])} errors ===")
    return results



async def fill_one(page_or_frame, field: dict) -> None:
    agent_id = field["agent_id"]
    kind = field["kind"]
    value = field["value"]
    
    if kind == "radio":
        # Radios share an agent_id; resolve by name+value instead
        name = field.get("name")
        if not name:
            raise ValueError(f"radio field {agent_id} has no name attribute")
        radio = page_or_frame.locator(
            f'input[type="radio"][name="{name}"][value="{value}"]'
        )
        await radio.scroll_into_view_if_needed(timeout=5000)
        await radio.check()
        return

    # --- PRECISION FIX FOR ASHBY TOGGLES - stupid checkbox html structure ---
    if kind == "ashby_toggle_yes_no":
        normalized_value = str(value).strip().lower()
        if normalized_value in ("on", "true", "yes"):
            target_text = "Yes"
        elif normalized_value in ("off", "false", "no", ""):
            target_text = "No"
        else:
            target_text = str(value) # Fallback to literal if it's somehow different

        # Target the button matching our text choice
        toggle_button = page_or_frame.locator(
            f'button[data-agent-id="{agent_id}"]', 
            has_text=target_text
        )
        await toggle_button.scroll_into_view_if_needed(timeout=5000)
        await toggle_button.click()
        return
    
    
    
    if kind in ("text", "email", "tel", "textarea", "number", "url", "password"):
        # Non-radio: agent_id is unique, normal locator path
        locator = page_or_frame.locator(f'[data-agent-id="{agent_id}"]')
        await locator.scroll_into_view_if_needed(timeout=5000)
        await locator.fill(str(value))
    elif kind == "select":
        await locator.select_option(value=str(value))
    elif kind == "checkbox":
        if value:
            await locator.check()
        else:
            await locator.uncheck()
    elif kind == 'combobox':
        await fill_react_select(page_or_frame, agent_id, value)
    else:
        raise ValueError(f"unknown field kind: {kind!r}")
    


async def fill_react_select(frame, agent_id: str, target_value: str) -> None:
    combobox = frame.locator(f'[data-agent-id="{agent_id}"]')
    
    await combobox.scroll_into_view_if_needed()
    
    # Open the dropdown. React-select listens for mousedown on its control,
    # not click. Try multiple strategies in order.
    opened = await frame.evaluate("""
        (agentId) => {
            const el = document.querySelector(`[data-agent-id="${agentId}"]`);
            if (!el) return false;
            
            // Find the clickable wrapper
            const wrapper = el.closest('.select__control')
                || el.closest('[class*="select__control"]')
                || el.closest('[class*="control"]')
                || el.closest('[role="combobox"]')
                || el.parentElement;
            
            const target = wrapper || el;
            
            // Focus first
            try { el.focus(); } catch {}
            
            // React-select uses mousedown
            const opts = { bubbles: true, cancelable: true, button: 0 };
            target.dispatchEvent(new MouseEvent('mousedown', opts));
            target.dispatchEvent(new MouseEvent('mouseup', opts));
            target.dispatchEvent(new MouseEvent('click', opts));
            
            return true;
        }
    """, agent_id)
    
    if not opened:
        raise RuntimeError(f"Could not find combobox {agent_id} to open")
    
    # Wait for either aria-expanded=true OR a visible listbox to appear
    # (some libraries don't toggle aria-expanded reliably)
    try:
        await frame.wait_for_function(
            """(agentId) => {
                const el = document.querySelector(`[data-agent-id="${agentId}"]`);
                if (!el) return false;
                if (el.getAttribute('aria-expanded') === 'true') return true;
                
                // Fallback: look for a listbox that appeared near this combobox
                let scope = el.closest('.select, [class*="select"], .field-wrapper')
                    || el.parentElement;
                let depth = 0;
                while (scope && depth < 6) {
                    const lbs = scope.querySelectorAll('[role="listbox"]');
                    for (const lb of lbs) {
                        if (lb.offsetParent !== null
                            && lb.querySelectorAll('[role="option"]').length > 0) {
                            return true;
                        }
                    }
                    scope = scope.parentElement;
                    depth++;
                }
                return false;
            }""",
            arg=agent_id,
            timeout=5000,
        )
    except Exception:
        # Last resort: try arrow-down to open
        await combobox.press('ArrowDown')
        await frame.wait_for_function(
            """(agentId) => {
                const el = document.querySelector(`[data-agent-id="${agentId}"]`);
                return el && el.getAttribute('aria-expanded') === 'true';
            }""",
            arg=agent_id,
            timeout=3000,
        )
    
    # Read options
    options = await frame.evaluate("""
        (agentId) => {
            const el = document.querySelector(`[data-agent-id="${agentId}"]`);
            if (!el) return [];
            
            const controlsId = el.getAttribute('aria-controls');
            let listbox = controlsId ? document.getElementById(controlsId) : null;
            
            if (!listbox || listbox.offsetParent === null) {
                let scope = el.closest('.select, [class*="select"], .field-wrapper, fieldset')
                    || el.parentElement;
                let depth = 0;
                while (scope && depth < 6) {
                    const candidates = scope.querySelectorAll('[role="listbox"]');
                    for (const lb of candidates) {
                        if (lb.offsetParent !== null
                            && lb.querySelectorAll('[role="option"]').length > 0) {
                            listbox = lb;
                            break;
                        }
                    }
                    if (listbox) break;
                    scope = scope.parentElement;
                    depth++;
                }
            }
            
            if (!listbox) return [];
            
            return Array.from(listbox.querySelectorAll('[role="option"]'))
                .filter(o => o.offsetParent !== null)
                .map(o => ({
                    id: o.id,
                    text: o.innerText.trim(),
                }));
        }
    """, agent_id)
    
    if not options:
        raise RuntimeError(f"No visible options found for {agent_id}")
    
    # Fuzzy match
    target_lower = target_value.lower().strip()
    match = next((o for o in options if o['text'] == target_value), None) \
        or next((o for o in options if o['text'].lower() == target_lower), None) \
        or next((o for o in options if target_lower in o['text'].lower()), None) \
        or next((o for o in options if o['text'].lower() in target_lower), None)
    
    if not match:
        raise RuntimeError(
            f"No option matching '{target_value}' in {[o['text'] for o in options]}"
        )
    
    # Click the matched option, with mousedown fallback
    if match.get('id'):
        option_locator = frame.locator(f'#{match["id"]}')
    else:
        option_locator = frame.get_by_role('option', name=match['text']).first
    
    try:
        await option_locator.click(timeout=2000)
    except Exception:
        # React-select sometimes needs mousedown on options too
        await option_locator.evaluate("""
            el => {
                const opts = { bubbles: true, cancelable: true, button: 0 };
                el.dispatchEvent(new MouseEvent('mousedown', opts));
                el.dispatchEvent(new MouseEvent('mouseup', opts));
                el.dispatchEvent(new MouseEvent('click', opts));
            }
        """)

async def find_apply_frame(page):
    """
    Find the frame containing the apply form. Falls back to the main page
    if no apply iframe is found.
    """
    # Indeed serves apply forms from a few hosts; match broadly
    for frame in page.frames:
        if any(host in frame.url for host in ("smartapply.indeed.com", "indeedapply", "/beta/indeedapply")):
            return frame
    
    # Fallback: pick the frame with the most non-search inputs
    best = page.main_frame
    best_count = 0
    for frame in page.frames:
        try:
            count = await frame.evaluate("""
                () => document.querySelectorAll(
                    'input:not([type=hidden]):not([type=submit]):not([type=button]):not([name="q"]):not([name="l"]),'
                    + ' select, textarea'
                ).length
            """)
            if count > best_count:
                best_count = count
                best = frame
        except Exception:
            continue
    return best


async def get_focused_page(session) -> Page:
    """Return the page the user is actually looking at."""
    context = session.page.context
    pages = [p for p in context.pages if not p.is_closed()]
    
    if not pages:
        return session.page
    if len(pages) == 1:
        return pages[0]
    
    # Check which page has focus and is visible
    for p in pages:
        try:
            is_focused = await p.evaluate(
                "() => document.hasFocus() && document.visibilityState === 'visible'"
            )
            if is_focused:
                return p
        except Exception:
            continue
    
    # Fallback: most recently opened
    return pages[-1]

async def get_form_frame(page):
    """Find the Greenhouse iframe (or whichever frame actually has the form)."""
    # Wait for the iframe element to exist
    await page.wait_for_selector('iframe', timeout=10000)
    
    # Find the frame by URL pattern — Greenhouse embeds use these
    for f in page.frames:
        if any(s in f.url for s in ['greenhouse.io', 'job_app', 'job-boards']):
            return f
    
    # Fallback: pick the frame with the most form inputs
    best_frame = page.main_frame
    best_count = 0
    for f in page.frames:
        try:
            c = await f.evaluate("document.querySelectorAll('input, select, textarea').length")
            if c > best_count:
                best_count = c
                best_frame = f
        except Exception:
            pass
    return best_frame


# async def extract_form_fields(page_or_frame) -> list[dict]:
#     """Walk the DOM, return one dict per input. Radio groups are collapsed into single fields."""
#     fields = await page_or_frame.evaluate("""
#         () => {
#             const results = [];
                                          
#             // Add this helper near the top of the evaluate function
#             function isLikelyHoneypot(el) {
#                 const cs = getComputedStyle(el);

#                 // Standard CSS hides
#                 if (cs.display === 'none') return true;
#                 if (cs.visibility === 'hidden') return true;
#                 if (cs.opacity === '0') return true;

#                 // Zero or near-zero size
#                 const r = el.getBoundingClientRect();
#                 if (r.width < 2 || r.height < 2) return true;

#                 // Positioned off-screen (common honeypot trick)
#                 if (r.left + r.width < 0 || r.top + r.height < 0) return true;
#                 if (r.left > window.innerWidth + 1000) return true;

#                 // tabindex=-1 on a text input is suspicious — real forms don't skip
#                 // their own inputs in tab order
#                 if (el.getAttribute('tabindex') === '-1') return true;

#                 // autocomplete=off combined with no label is another tell, but too
#                 // aggressive on its own — skip unless we want to be paranoid

#                 // Walk up a few ancestors and check if any of them is hidden
#                 let node = el.parentElement;
#                 let depth = 0;
#                 while (node && depth < 5) {
#                     const ncs = getComputedStyle(node);
#                     if (ncs.display === 'none' || ncs.visibility === 'hidden') return true;
#                     // Off-screen wrapper (e.g. position:absolute; left:-9999px)
#                     if (ncs.position === 'absolute' || ncs.position === 'fixed') {
#                         const left = parseFloat(ncs.left);
#                         const top = parseFloat(ncs.top);
#                         if (left < -1000 || top < -1000) return true;
#                     }
#                     node = node.parentElement;
#                     depth++;
#                 }

#                 return false;
#             }            


                            
            
#             // ---- helper: find the question text for an element or radio group ----
#             function findQuestion(el) {
#                 // 1. Associated <label for=id>
#                 if (el.id) {
#                     const lbl = document.querySelector(`label[for="${el.id}"]`);
#                     if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
#                 }
#                 // 2. Wrapping <label>
#                 const wrapping = el.closest('label');
#                 if (wrapping && wrapping.innerText.trim()) return wrapping.innerText.trim();
#                 // 3. ARIA / placeholder
#                 const aria = el.getAttribute('aria-label');
#                 if (aria) return aria.trim();
#                 const ph = el.getAttribute('placeholder');
#                 if (ph) return ph.trim();
#                 return '';
#             }
            
#             // For radio groups: walk up to find a fieldset, legend, or
#             // the nearest ancestor containing a heading/label-like element above the radios
#             function findGroupQuestion(radios) {
#                 // Try fieldset > legend
#                 const first = radios[0];
#                 const fs = first.closest('fieldset');
#                 if (fs) {
#                     const legend = fs.querySelector('legend');
#                     if (legend && legend.innerText.trim()) return legend.innerText.trim();
#                 }
                
#                 // Try aria-labelledby on a wrapping role="radiogroup"
#                 const group = first.closest('[role="radiogroup"]');
#                 if (group) {
#                     const labelledBy = group.getAttribute('aria-labelledby');
#                     if (labelledBy) {
#                         const lbl = document.getElementById(labelledBy);
#                         if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
#                     }
#                     const aria = group.getAttribute('aria-label');
#                     if (aria) return aria.trim();
#                 }
                
#                 // Walk up the DOM until we find an ancestor that contains
#                 // a question-like element (heading, strong text, label) appearing
#                 // BEFORE the first radio
#                 let node = first.parentElement;
#                 while (node && node !== document.body) {
#                     // Look for question text in this container that comes before any radio
#                     const candidates = node.querySelectorAll(
#                         'legend, h1, h2, h3, h4, h5, h6, label, [class*="question"], [class*="label"], p, span, div'
#                     );
#                     for (const c of candidates) {
#                         // Skip if this element is the radio's own label or contains the radio
#                         if (c.contains(first)) continue;
#                         if (c.querySelector('input[type=radio]')) continue;
#                         const text = c.innerText ? c.innerText.trim() : '';
#                         // Heuristic: question text usually has ? or is a meaningful sentence
#                         if (text.length > 10 && text.length < 500) {
#                             return text;
#                         }
#                     }
#                     node = node.parentElement;
#                 }
#                 return '';
#             }
            
#             // ---- pass 1: collect non-radio inputs ----
#             const nonRadios = document.querySelectorAll(
#                 'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=radio]),'
#                 + ' select, textarea'
#             );
            
#             let idCounter = 0;
            
#             nonRadios.forEach((el) => {
#                 if (isLikelyHoneypot(el)) return;   // get rid of honeypot input fields
#                 const agentId = `field-${idCounter++}`;
#                 el.setAttribute('data-agent-id', agentId);
                
#                 let options = null;
#                 if (el.tagName === 'SELECT') {
#                     options = Array.from(el.options)
#                         .map(o => ({ value: o.value, label: o.text.trim() }))
#                         .filter(o => o.value);
#                 }
                
#                 results.push({
#                     agent_id: agentId,
#                     kind: el.tagName === 'SELECT' ? 'select'
#                         : el.tagName === 'TEXTAREA' ? 'textarea'
#                         : (el.type || 'text'),
#                     question: findQuestion(el),
#                     name: el.name || null,
#                     options: options,
#                     value: el.value || '',
#                 });
#             });
            
#             // ---- pass 2: group radios by name ----
#             const radios = document.querySelectorAll('input[type=radio]');
#             const groups = {};
#             radios.forEach(r => {
#                 const key = r.name || `_anon_${r.outerHTML.length}`;
#                 if (!groups[key]) groups[key] = [];
#                 groups[key].push(r);
#             });
            
#             Object.entries(groups).forEach(([name, radioList]) => {
                                          
#                 const visibleRadios = radioList.filter(r => !isLikelyHoneypot(r));
#                 if (visibleRadios.length === 0) return;   // ← add this
                                          
#                 const agentId = `field-${idCounter++}`;
                
#                 // Tag every radio in the group with the SAME agent_id so locator works
#                 // even though we treat them as one logical field
#                 radioList.forEach(r => r.setAttribute('data-agent-id', agentId));
                
#                 const options = radioList.map(r => ({
#                     value: r.value,
#                     label: findQuestion(r) || r.value,  // label text per radio
#                 }));
                
#                 const question = findGroupQuestion(radioList);
#                 const anyChecked = radioList.find(r => r.checked);
                
#                 results.push({
#                     agent_id: agentId,
#                     kind: 'radio',   
#                     question: question,
#                     name: name,
#                     options: options,
#                     value: anyChecked ? anyChecked.value : '',
#                 });
#             });
            
#             return results;
#         }
#     """)
#     return fields



async def extract_form_fields(page_or_frame) -> list[dict]:
    """Walk the DOM, return one dict per input. Radio groups are collapsed into single fields."""
    fields = await page_or_frame.evaluate("""
        () => {
            const results = [];

            // ---- honeypot detection ----
            function isLikelyHoneypot(el) {
                // PRECISION PATCH: If it's a standard named checkbox/radio framework element,
                // do NOT treat it as a honeypot just because it's visually hidden or sized 0.
                if ((el.type === 'checkbox' || el.type === 'radio') && el.name) {
                    if (el.getAttribute('aria-hidden') === 'true') return true;
                    return false; 
                }

                const cs = getComputedStyle(el);

                if (cs.display === 'none') return true;
                if (cs.visibility === 'hidden') return true;
                if (cs.opacity === '0') return true;

                // aria-hidden is a strong honeypot signal on its own
                if (el.getAttribute('aria-hidden') === 'true') return true;

                // Combobox inputs often have 0–2px width when collapsed (react-select),
                // so don't size-check them
                const isCombobox = el.getAttribute('role') === 'combobox'
                    || el.getAttribute('aria-haspopup') === 'listbox'
                    || el.getAttribute('aria-haspopup') === 'true';

                const r = el.getBoundingClientRect();
                if (!isCombobox) {
                    if (r.width < 2 || r.height < 2) return true;
                }

                if (r.left + r.width < -100 || r.top + r.height < -100) return true;
                if (r.left > window.innerWidth + 1000) return true;

                // tabindex=-1 alone is too aggressive (many real comboboxes use it).
                // Only flag if combined with aria-hidden.
                if (el.getAttribute('tabindex') === '-1'
                    && el.getAttribute('aria-hidden') === 'true') {
                    return true;
                }

                let node = el.parentElement;
                let depth = 0;
                while (node && depth < 5) {
                    const ncs = getComputedStyle(node);
                    if (ncs.display === 'none' || ncs.visibility === 'hidden') return true;
                    if (ncs.position === 'absolute' || ncs.position === 'fixed') {
                        const left = parseFloat(ncs.left);
                        const top = parseFloat(ncs.top);
                        if (left < -1000 || top < -1000) return true;
                    }
                    node = node.parentElement;
                    depth++;
                }
                return false;
            }

            // ---- detect what kind of field this is ----
            function detectKind(el) {
                if (el.tagName === 'SELECT') return 'select';
                if (el.tagName === 'TEXTAREA') return 'textarea';
                
                // PRECISION PATCH: If it's a checkbox hidden inside a Yes/No toggle wrapper, 
                // treat its functional kind as a radio/toggle group so the AI handles choices properly.

                // handle checkboxes that use buttons as clickable elements...
                if (el.type === 'checkbox' && el.parentElement && el.parentElement.querySelector('button')) {
                    return 'ashby_toggle_yes_no';
                }
                if (el.type === 'checkbox') return 'checkbox';

                const role = el.getAttribute('role');
                if (role === 'combobox') return 'combobox';
                // aria-haspopup=listbox without role=combobox is also a dropdown
                const popup = el.getAttribute('aria-haspopup');
                if (popup === 'listbox' || popup === 'true') return 'combobox';
                return el.type || 'text';
            }

            // ---- find options for an ARIA combobox if listbox is pre-rendered ----
            function findComboboxOptions(el) {
                const controls = el.getAttribute('aria-controls');
                if (!controls) return null;
                const listbox = document.getElementById(controls);
                if (!listbox) return null;
                const items = listbox.querySelectorAll('[role="option"], li');
                const opts = Array.from(items)
                    .map(i => ({
                        value: i.getAttribute('data-value') || i.id || i.innerText.trim(),
                        label: i.innerText.trim(),
                    }))
                    .filter(o => o.label);
                return opts.length ? opts : null;
            }

            // ---- find question text for an element ----
            function findQuestion(el) {
                // 1. aria-labelledby (modern component libs use this constantly)
                const labelledBy = el.getAttribute('aria-labelledby');
                if (labelledBy) {
                    const texts = labelledBy.split(/\\s+/)
                        .map(id => document.getElementById(id))
                        .filter(Boolean)
                        .map(n => n.innerText.trim())
                        .filter(Boolean);
                    if (texts.length) return texts.join(' ');
                }
                // 2. <label for=id>
                if (el.id) {
                    const lbl = document.querySelector(`label[for="${el.id}"]`);
                    if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
                }
                // 3. Wrapping <label>
                const wrapping = el.closest('label');
                if (wrapping && wrapping.innerText.trim()) return wrapping.innerText.trim();
                // 4. aria-label
                const aria = el.getAttribute('aria-label');
                if (aria) return aria.trim();
                // 5. placeholder
                const ph = el.getAttribute('placeholder');
                if (ph) return ph.trim();
                // 6. Walk up looking for a label-ish sibling
                let node = el.parentElement;
                let depth = 0;
                while (node && depth < 4) {
                    const candidates = node.querySelectorAll(
                        'label, [class*="label" i], [class*="question" i], [class*="title" i]'
                    );
                    for (const c of candidates) {
                        if (c.contains(el)) continue;
                        if (c.querySelector('input:not([type=checkbox]):not([type=radio]), select, textarea')) continue;
                        const text = c.innerText ? c.innerText.trim() : '';
                        if (text && text.length < 300) return text;
                    }
                    node = node.parentElement;
                    depth++;
                }
                return '';
            }

            // ---- find question for a radio group ----
            function findGroupQuestion(radios) {
                const first = radios[0];
                const fs = first.closest('fieldset');
                if (fs) {
                    const legend = fs.querySelector('legend');
                    if (legend && legend.innerText.trim()) return legend.innerText.trim();
                }

                const group = first.closest('[role="radiogroup"]');
                if (group) {
                    const labelledBy = group.getAttribute('aria-labelledby');
                    if (labelledBy) {
                        const lbl = document.getElementById(labelledBy);
                        if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
                    }
                    const aria = group.getAttribute('aria-label');
                    if (aria) return aria.trim();
                }

                let node = first.parentElement;
                while (node && node !== document.body) {
                    const candidates = node.querySelectorAll(
                        'legend, h1, h2, h3, h4, h5, h6, label, [class*="question"], [class*="label"], p, span, div'
                    );
                    for (const c of candidates) {
                        if (c.contains(first)) continue;
                        if (c.querySelector('input[type=radio]')) continue;
                        const text = c.innerText ? c.innerText.trim() : '';
                        if (text.length > 10 && text.length < 500) {
                            return text;
                        }
                    }
                    node = node.parentElement;
                }
                return '';
            }

            // ---- pass 1: non-radio inputs ----
            // PRECISION PATCH: Included checkboxes directly inside pass 1 selection query
            const nonRadios = document.querySelectorAll(
                'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=radio]),'
                + ' select, textarea'
            );

            let idCounter = 0;

            nonRadios.forEach((el) => {
                if (isLikelyHoneypot(el)) return;
                                          
                // Skip inputs that are inside a hidden dropdown panel (iti search, etc.)
                const inHiddenDropdown = el.closest('[role="dialog"][aria-modal="true"]')
                    || el.closest('.iti__dropdown-content')
                    || el.closest('[class*="dropdown-content"]');
                if (inHiddenDropdown) {
                    const dcs = getComputedStyle(inHiddenDropdown);
                    if (dcs.display === 'none' || inHiddenDropdown.classList.contains('iti__hide')) {
                        return;
                    }
                }

                const agentId = `field-${idCounter++}`;
                el.setAttribute('data-agent-id', agentId);

                const kind = detectKind(el);

                let options = null;
                if (el.tagName === 'SELECT') {
                    options = Array.from(el.options)
                        .map(o => ({ value: o.value, label: o.text.trim() }))
                        .filter(o => o.value);
                } else if (kind === 'combobox') {
                    options = findComboboxOptions(el);
                } 
                // PRECISION PATCH: If this is an Ashby style pseudo-checkbox, map neighboring buttons to choices
                else if (el.type === 'checkbox' && el.parentElement) {
                    const siblingButtons = el.parentElement.querySelectorAll('button');
                    if (siblingButtons.length > 0) {
                        // Tag sibling buttons with the same data-agent-id so Playwright can click them seamlessly
                        siblingButtons.forEach(btn => btn.setAttribute('data-agent-id', agentId));
                        options = Array.from(siblingButtons).map(b => ({
                            value: b.innerText.trim(),
                            label: b.innerText.trim()
                        }));
                    }
                }

                results.push({
                    agent_id: agentId,
                    kind: kind,
                    question: findQuestion(el),
                    name: el.name || null,
                    options: options,
                    value: el.value || '',
                });
            });

            // ---- pass 2: radio groups ----
            const radios = document.querySelectorAll('input[type=radio]');
            const groups = {};
            radios.forEach(r => {
                const key = r.name || `_anon_${r.outerHTML.length}`;
                if (!groups[key]) groups[key] = [];
                groups[key].push(r);
            });

            Object.entries(groups).forEach(([name, radioList]) => {
                const visibleRadios = radioList.filter(r => !isLikelyHoneypot(r));
                if (visibleRadios.length === 0) return;

                const agentId = `field-${idCounter++}`;
                radioList.forEach(r => r.setAttribute('data-agent-id', agentId));

                const options = radioList.map(r => ({
                    value: r.value,
                    label: findQuestion(r) || r.value,
                }));

                results.push({
                    agent_id: agentId,
                    kind: 'radio',
                    question: findGroupQuestion(radioList),
                    name: name,
                    options: options,
                    value: (radioList.find(r => r.checked) || {}).value || '',
                });
            });

            return results;
        }
    """)
    return fields