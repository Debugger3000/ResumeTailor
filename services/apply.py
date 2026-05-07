from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

# app/services/page_reader.py

# return page html from playwright session
# async def get_page_html(session):
#     """Return the full rendered HTML of the current page."""
#     return await session.page.content()



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


# async def fill_one(page_or_frame, field: dict) -> None:
#     """Fill a single field. Raises on failure."""
#     agent_id = field["agent_id"]
#     kind = field["kind"]
#     value = field["value"]
#     locator = page_or_frame.locator(f'[data-agent-id="{agent_id}"]')
    
#     # Make sure the field is visible/in view before interacting
#     await locator.scroll_into_view_if_needed(timeout=5000)
    
#     if kind in ("text", "email", "tel", "textarea", "number", "url", "password"):
#         await locator.fill(str(value))
    
#     elif kind == "select":
#         await locator.select_option(value=str(value))
    
#     elif kind == "checkbox":
#         if value:
#             await locator.check()
#         else:
#             await locator.uncheck()
    
#     elif kind == "radio":
#         # Radios share a `name` attribute; click the one whose value matches
#         name = field.get("name")
#         value = field["value"]
#         if not name:
#             raise ValueError(f"radio field {field['agent_id']} has no name attribute")
#         radio = page_or_frame.locator(f'input[type="radio"][name="{name}"][value="{value}"]')
#         await radio.check()
        
#     elif kind == "file":
#         await locator.set_input_files(str(value))
    
#     else:
#         raise ValueError(f"unknown field kind: {kind!r}")

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
    
    # Non-radio: agent_id is unique, normal locator path
    locator = page_or_frame.locator(f'[data-agent-id="{agent_id}"]')
    await locator.scroll_into_view_if_needed(timeout=5000)
    
    if kind in ("text", "email", "tel", "textarea", "number", "url", "password"):
        await locator.fill(str(value))
    elif kind == "select":
        await locator.select_option(value=str(value))
    elif kind == "checkbox":
        if value:
            await locator.check()
        else:
            await locator.uncheck()
    elif kind == "file":
        await locator.set_input_files(str(value))
    else:
        raise ValueError(f"unknown field kind: {kind!r}")

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


# grab input fields and extract data of specific input fields manually 
# async def extract_form_fields(page: Page) -> list[dict]:
#     """Walk the DOM, return one dict per input with everything pre-resolved."""
#     fields = await page.evaluate("""
#         () => {
#             const results = [];
#             const controls = document.querySelectorAll(
#                 'input:not([type=hidden]):not([type=submit]):not([type=button]), select, textarea'
#             );
            
#             controls.forEach((el, idx) => {
#                 // Tag the element so we can find it later without a fragile selector
#                 el.setAttribute('data-agent-id', `field-${idx}`);
                
#                 // Find associated label text
#                 let labelText = '';
#                 if (el.id) {
#                     const lbl = document.querySelector(`label[for="${el.id}"]`);
#                     if (lbl) labelText = lbl.innerText.trim();
#                 }
#                 if (!labelText) {
#                     const wrapping = el.closest('label');
#                     if (wrapping) labelText = wrapping.innerText.trim();
#                 }
#                 if (!labelText) {
#                     labelText = el.getAttribute('aria-label') 
#                         || el.getAttribute('placeholder') 
#                         || '';
#                 }
                
#                 // Pull options for selects/radios
#                 let options = null;
#                 if (el.tagName === 'SELECT') {
#                     options = Array.from(el.options)
#                         .map(o => ({ value: o.value, label: o.text.trim() }))
#                         .filter(o => o.value);
#                 }
                
#                 results.push({
#                     index: idx,
#                     agent_id: `field-${idx}`,
#                     tag: el.tagName.toLowerCase(),
#                     input_type: el.type || null,
#                     name: el.name || null,
#                     question: labelText,
#                     options: options,
#                     required: el.required || el.getAttribute('aria-required') === 'true',
#                     current_value: el.value || '',
#                 });
#             });
            
#             // Also pick up radio groups — group them by name
#             // (radios share a `name` and the user picks one)
            
#             return results;
#         }
#     """)
#     return fields




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


async def extract_form_fields(page_or_frame) -> list[dict]:
    """Walk the DOM, return one dict per input. Radio groups are collapsed into single fields."""
    fields = await page_or_frame.evaluate("""
        () => {
            const results = [];
                                          
            // Add this helper near the top of the evaluate function
            function isLikelyHoneypot(el) {
                const cs = getComputedStyle(el);

                // Standard CSS hides
                if (cs.display === 'none') return true;
                if (cs.visibility === 'hidden') return true;
                if (cs.opacity === '0') return true;

                // Zero or near-zero size
                const r = el.getBoundingClientRect();
                if (r.width < 2 || r.height < 2) return true;

                // Positioned off-screen (common honeypot trick)
                if (r.left + r.width < 0 || r.top + r.height < 0) return true;
                if (r.left > window.innerWidth + 1000) return true;

                // tabindex=-1 on a text input is suspicious — real forms don't skip
                // their own inputs in tab order
                if (el.getAttribute('tabindex') === '-1') return true;

                // autocomplete=off combined with no label is another tell, but too
                // aggressive on its own — skip unless we want to be paranoid

                // Walk up a few ancestors and check if any of them is hidden
                let node = el.parentElement;
                let depth = 0;
                while (node && depth < 5) {
                    const ncs = getComputedStyle(node);
                    if (ncs.display === 'none' || ncs.visibility === 'hidden') return true;
                    // Off-screen wrapper (e.g. position:absolute; left:-9999px)
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
            
            // ---- helper: find the question text for an element or radio group ----
            function findQuestion(el) {
                // 1. Associated <label for=id>
                if (el.id) {
                    const lbl = document.querySelector(`label[for="${el.id}"]`);
                    if (lbl && lbl.innerText.trim()) return lbl.innerText.trim();
                }
                // 2. Wrapping <label>
                const wrapping = el.closest('label');
                if (wrapping && wrapping.innerText.trim()) return wrapping.innerText.trim();
                // 3. ARIA / placeholder
                const aria = el.getAttribute('aria-label');
                if (aria) return aria.trim();
                const ph = el.getAttribute('placeholder');
                if (ph) return ph.trim();
                return '';
            }
            
            // For radio groups: walk up to find a fieldset, legend, or
            // the nearest ancestor containing a heading/label-like element above the radios
            function findGroupQuestion(radios) {
                // Try fieldset > legend
                const first = radios[0];
                const fs = first.closest('fieldset');
                if (fs) {
                    const legend = fs.querySelector('legend');
                    if (legend && legend.innerText.trim()) return legend.innerText.trim();
                }
                
                // Try aria-labelledby on a wrapping role="radiogroup"
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
                
                // Walk up the DOM until we find an ancestor that contains
                // a question-like element (heading, strong text, label) appearing
                // BEFORE the first radio
                let node = first.parentElement;
                while (node && node !== document.body) {
                    // Look for question text in this container that comes before any radio
                    const candidates = node.querySelectorAll(
                        'legend, h1, h2, h3, h4, h5, h6, label, [class*="question"], [class*="label"], p, span, div'
                    );
                    for (const c of candidates) {
                        // Skip if this element is the radio's own label or contains the radio
                        if (c.contains(first)) continue;
                        if (c.querySelector('input[type=radio]')) continue;
                        const text = c.innerText ? c.innerText.trim() : '';
                        // Heuristic: question text usually has ? or is a meaningful sentence
                        if (text.length > 10 && text.length < 500) {
                            return text;
                        }
                    }
                    node = node.parentElement;
                }
                return '';
            }
            
            // ---- pass 1: collect non-radio inputs ----
            const nonRadios = document.querySelectorAll(
                'input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=radio]),'
                + ' select, textarea'
            );
            
            let idCounter = 0;
            
            nonRadios.forEach((el) => {
                if (isLikelyHoneypot(el)) return;   // get rid of honeypot input fields
                const agentId = `field-${idCounter++}`;
                el.setAttribute('data-agent-id', agentId);
                
                let options = null;
                if (el.tagName === 'SELECT') {
                    options = Array.from(el.options)
                        .map(o => ({ value: o.value, label: o.text.trim() }))
                        .filter(o => o.value);
                }
                
                results.push({
                    agent_id: agentId,
                    kind: el.tagName === 'SELECT' ? 'select'
                        : el.tagName === 'TEXTAREA' ? 'textarea'
                        : (el.type || 'text'),
                    question: findQuestion(el),
                    name: el.name || null,
                    options: options,
                    value: el.value || '',
                });
            });
            
            // ---- pass 2: group radios by name ----
            const radios = document.querySelectorAll('input[type=radio]');
            const groups = {};
            radios.forEach(r => {
                const key = r.name || `_anon_${r.outerHTML.length}`;
                if (!groups[key]) groups[key] = [];
                groups[key].push(r);
            });
            
            Object.entries(groups).forEach(([name, radioList]) => {
                                          
                const visibleRadios = radioList.filter(r => !isLikelyHoneypot(r));
                if (visibleRadios.length === 0) return;   // ← add this
                                          
                const agentId = `field-${idCounter++}`;
                
                // Tag every radio in the group with the SAME agent_id so locator works
                // even though we treat them as one logical field
                radioList.forEach(r => r.setAttribute('data-agent-id', agentId));
                
                const options = radioList.map(r => ({
                    value: r.value,
                    label: findQuestion(r) || r.value,  // label text per radio
                }));
                
                const question = findGroupQuestion(radioList);
                const anyChecked = radioList.find(r => r.checked);
                
                results.push({
                    agent_id: agentId,
                    kind: 'radio',   
                    question: question,
                    name: name,
                    options: options,
                    value: anyChecked ? anyChecked.value : '',
                });
            });
            
            return results;
        }
    """)
    return fields




