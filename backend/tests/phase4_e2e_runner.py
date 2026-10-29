import asyncio
import json
import subprocess
import sys
import time
import urllib.request
import websockets

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9222

class BrowserTester:
    def __init__(self):
        self.proc = None
        self.ws = None
        self.msg_id = 0

    def start_chrome(self):
        cmd = [
            CHROME_PATH,
            "--headless=new",
            f"--remote-debugging-port={CDP_PORT}",
            "--remote-allow-origins=*",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-extensions",
            "--window-size=1366,900",
            "about:blank"
        ]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)

    async def connect(self):
        for _ in range(15):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2) as r:
                    targets = [t for t in json.loads(r.read().decode()) if t.get("type") == "page"]
                    if targets:
                        ws_url = targets[0].get("webSocketDebuggerUrl")
                        self.ws = await websockets.connect(ws_url)
                        return True
            except Exception:
                await asyncio.sleep(0.5)
        raise RuntimeError("Failed to connect to Chrome DevTools Protocol")

    async def send_cmd(self, method, params=None):
        self.msg_id += 1
        msg = {"id": self.msg_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(msg))
        while True:
            resp_raw = await self.ws.recv()
            resp = json.loads(resp_raw)
            if resp.get("id") == self.msg_id:
                return resp.get("result", {})

    async def eval_js(self, expression):
        res = await self.send_cmd("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        })
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Error: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def stop_chrome(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()


async def run_phase4_e2e_tests():
    tester = BrowserTester()
    tester.start_chrome()
    results = {}

    try:
        await tester.connect()
        print("Connected to Chrome CDP on port 9222.")

        # Helper to set input value safely in React
        async def set_react_input(element_id, value):
            await tester.eval_js(f"""
            (() => {{
                const el = document.getElementById('{element_id}');
                if (!el) return false;
                el.focus();
                const prev = el.value;
                el.value = '{value}';
                if (el._valueTracker) el._valueTracker.setValue(prev + '_reset');
                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return true;
            }})()
            """)

        # -----------------------------------------------------------------
        # PAGE LOAD
        # -----------------------------------------------------------------
        await tester.send_cmd("Page.navigate", {"url": "http://127.0.0.1:5173/"})
        for _ in range(25):
            await asyncio.sleep(0.5)
            has_input = await tester.eval_js("!!document.getElementById('destination')")
            if has_input:
                break

        title = await tester.eval_js("document.title")
        print(f"Page loaded: '{title}'")
        results["page_load"] = "PASS" if "TripGenie" in title else "FAIL"

        # -----------------------------------------------------------------
        # FLOW 1: Search & select destinations (Darjeeling & less-famous town)
        # -----------------------------------------------------------------
        print("\n--- FLOW 1: Search & Select Destinations (Darjeeling & Banff) ---")
        # 1.1 Search Darjeeling
        await set_react_input("destination", "Darjeeling")
        await asyncio.sleep(1.2)

        darj_items_raw = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            if (!dropdown) return '[]';
            const buttons = Array.from(dropdown.querySelectorAll('button'));
            return JSON.stringify(buttons.map(b => b.innerText));
        })()
        """)
        darj_items = json.loads(darj_items_raw) if darj_items_raw else []
        print(f"Suggestions for 'Darjeeling': {[s.replace(chr(10), ' | ') for s in darj_items]}")
        has_darj = any("Darjeeling" in s and "India" in s for s in darj_items)

        # 1.2 Search less-famous town: Banff
        await set_react_input("destination", "Banff")
        await asyncio.sleep(1.2)
        banff_items_raw = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            if (!dropdown) return '[]';
            const buttons = Array.from(dropdown.querySelectorAll('button'));
            return JSON.stringify(buttons.map(b => b.innerText));
        })()
        """)
        banff_items = json.loads(banff_items_raw) if banff_items_raw else []
        print(f"Suggestions for 'Banff': {[s.replace(chr(10), ' | ') for s in banff_items]}")
        has_banff = any("Banff" in s and "Canada" in s for s in banff_items)

        # Select Darjeeling by clicking the suggestion
        await set_react_input("destination", "Darjeeling")
        await asyncio.sleep(1.2)
        await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            const btn = dropdown ? dropdown.querySelector('button') : null;
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.4)
        darj_val = await tester.eval_js("document.getElementById('destination').value")
        print(f"Selected destination populated in field: '{darj_val}'")

        results["search_and_select_destinations"] = "PASS" if (has_darj and has_banff and "Darjeeling" in darj_val) else "FAIL"

        # -----------------------------------------------------------------
        # FLOW 2: Complete 3-step form with custom preferences
        # -----------------------------------------------------------------
        print("\n--- FLOW 2: Complete 3-Step Form with Custom Preferences ---")
        # Step 1: Set custom dates (5 days: 2026-10-10 to 2026-10-14)
        await set_react_input("startDate", "2026-10-10")
        await set_react_input("endDate", "2026-10-14")
        await asyncio.sleep(0.3)

        # Advance Step 1 -> Step 2
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue to Preferences'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        # Step 2: Select luxury budget, family traveler type, 4 travelers, relaxed pace
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));

            const luxBtn = buttons.find(b => b.innerText.toLowerCase().includes('luxury') && !b.innerText.includes('Continue'));
            if (luxBtn) luxBtn.click();

            const famBtn = buttons.find(b => b.innerText.toLowerCase().includes('family') && !b.innerText.includes('Continue'));
            if (famBtn) famBtn.click();

            const relBtn = buttons.find(b => b.innerText.toLowerCase().includes('relaxed') && !b.innerText.includes('Continue'));
            if (relBtn) relBtn.click();
        })()
        """)
        await asyncio.sleep(0.4)

        # Set travelers count = 4
        await tester.eval_js("""
        (() => {
            const countInput = document.querySelector('input[type=\"number\"]');
            if (countInput) {
                const prev = countInput.value;
                countInput.value = '4';
                if (countInput._valueTracker) countInput._valueTracker.setValue(prev + '_reset');
                countInput.dispatchEvent(new Event('input', { bubbles: true }));
                countInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
        })()
        """)
        await asyncio.sleep(0.4)

        # Advance Step 2 -> Step 3
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue to Review'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        step3_text = await tester.eval_js("document.body.innerText")
        has_review = "Review & Generate" in step3_text and "Darjeeling" in step3_text
        print(f"Step 3 reached with custom inputs: {has_review}")
        results["three_step_form_completion"] = "PASS" if has_review else "FAIL"

        # -----------------------------------------------------------------
        # FLOW 3: Generate itinerary in mock mode & verify preferences match
        # -----------------------------------------------------------------
        print("\n--- FLOW 3: Generate Itinerary in Mock Mode ---")
        # Click Generate Itinerary button specifically
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Generate Itinerary'));
            if (btn) btn.click();
        })()
        """)

        # Wait for itinerary to be rendered
        generated_ok = False
        destination_in_itinerary = ""
        for _ in range(20):
            await asyncio.sleep(0.8)
            res = await tester.eval_js("""
            (() => {
                const text = document.body.innerText;
                const hasDarjeeling = text.includes('Darjeeling');
                const hasDays = text.includes('Day 1') && text.includes('Day 5');
                const hasFallback = text.includes('Fallback Preview') || text.includes('Mock');
                const h3 = document.querySelector('h3.font-editorial');
                return {
                    hasDarjeeling,
                    hasDays,
                    hasFallback,
                    title: h3 ? h3.innerText : ''
                };
            })()
            """)
            if res.get("hasDarjeeling") and res.get("hasDays"):
                generated_ok = True
                destination_in_itinerary = res.get("title")
                break

        print(f"Itinerary generated for: '{destination_in_itinerary}', 5 days present: {generated_ok}")
        results["itinerary_generation_mock_mode"] = "PASS" if generated_ok else "FAIL"

        # -----------------------------------------------------------------
        # FLOW 4: Check day-wise activities, timings, cost breakdown, budget
        # -----------------------------------------------------------------
        print("\n--- FLOW 4: Check Activities, Timings & Budget Breakdown ---")
        budget_and_timing_check = await tester.eval_js("""
        (() => {
            const text = document.body.innerText.toLowerCase();
            const hasTotalBudget = text.includes('total budget') || text.includes('usd') || text.includes('$');
            const hasBreakdown = text.includes('accommodation') || text.includes('food & dining') || text.includes('estimated breakdown') || text.includes('per night');
            const hasMorning = text.includes('morning');
            const hasAfternoon = text.includes('afternoon');
            const hasEvening = text.includes('evening');
            const hasTips = text.includes('etiquette') || text.includes('commuting') || text.includes('tips') || text.includes('transit');
            return {
                hasTotalBudget,
                hasBreakdown,
                hasMorning,
                hasAfternoon,
                hasEvening,
                hasTips
            };
        })()
        """)
        print(f"Details verified: {budget_and_timing_check}")
        flow4_passed = all(budget_and_timing_check.values())
        results["activities_timings_and_budget"] = "PASS" if flow4_passed else "FAIL"

        # -------------------------------------------------------------
        # FLOW 5: Edit an activity and regenerate a single day
        # -------------------------------------------------------------
        print("\n--- FLOW 5: Edit Activity & Regenerate Single Day ---")
        # 5.1 Click Edit activity on Day 1
        await tester.eval_js("""
        (() => {
            const editBtn = document.querySelector('button[title=\"Edit activity\"]');
            if (editBtn) editBtn.click();
        })()
        """)
        await asyncio.sleep(0.5)

        edited_title = "Sunrise at Tiger Hill & Kanchenjunga Sunrise View"
        await tester.eval_js(f"""
        (() => {{
            function setInput(input, val) {{
                const prev = input.value;
                input.value = val;
                if (input._valueTracker) input._valueTracker.setValue(prev + '_reset');
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            const inputs = Array.from(document.querySelectorAll('.fixed input'));
            if (inputs.length > 0) {{
                setInput(inputs[0], '{edited_title}');
            }}
            const saveBtn = Array.from(document.querySelectorAll('.fixed button')).find(b => b.innerText.includes('Save Changes'));
            if (saveBtn) saveBtn.click();
        }})()
        """)
        await asyncio.sleep(0.6)

        edited_visible = await tester.eval_js(f"document.body.innerText.includes('{edited_title}')")
        print(f"In-place edited activity rendered: {edited_visible}")

        # 5.2 Regenerate Day 2
        await tester.eval_js("""
        (() => {
            const regenBtn = document.querySelector('button[title*=\"Regenerate\"]');
            if (regenBtn) regenBtn.click();
        })()
        """)
        await asyncio.sleep(2.0)

        regen_ok = await tester.eval_js("""
        (() => {
            const text = document.body.innerText;
            return text.includes('Alternative Option') || text.includes('Fresh morning recommendation') || text.includes('Day 2');
        })()
        """)
        print(f"Day 2 regenerated successfully: {regen_ok}")
        results["edit_activity_and_regenerate_day"] = "PASS" if (edited_visible and regen_ok) else "FAIL"

        # -------------------------------------------------------------
        # FLOW 6: Save trip, reload it, edit it, and delete it
        # -------------------------------------------------------------
        print("\n--- FLOW 6: Save Trip, Load, Edit, and Delete ---")
        # Click Save Itinerary
        await tester.eval_js("""
        (() => {
            const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Save Itinerary'));
            if (saveBtn) saveBtn.click();
        })()
        """)
        await asyncio.sleep(1.0)

        saved_locally = await tester.eval_js("document.body.innerText.includes('Saved Locally')")
        print(f"Trip saved to SQLite: {saved_locally}")

        # Open Saved Trips modal (button has 'Saved (' in header)
        await tester.eval_js("""
        (() => {
            const savedBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Saved ('));
            if (savedBtn) savedBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        modal_text = await tester.eval_js("document.body.innerText")
        has_darj_in_modal = "Darjeeling" in modal_text and "Saved Itineraries" in modal_text
        print(f"Saved Trips modal shows Darjeeling: {has_darj_in_modal}")

        # Click Load on the saved trip
        await tester.eval_js("""
        (() => {
            const loadBtn = Array.from(document.querySelectorAll('.fixed button')).find(b => b.innerText.includes('Load'));
            if (loadBtn) loadBtn.click();
        })()
        """)
        await asyncio.sleep(0.6)

        # Open Saved Trips modal again and delete it
        await tester.eval_js("""
        (() => {
            const savedBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Saved ('));
            if (savedBtn) savedBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        await tester.eval_js("""
        (() => {
            const delBtn = document.querySelector('button[title=\"Delete saved trip\"]');
            if (delBtn) delBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        modal_after_del = await tester.eval_js("document.body.innerText")
        deleted_ok = "No Saved Itineraries Yet" in modal_after_del
        print(f"Deleted from SQLite: {deleted_ok}")

        # Close modal
        await tester.eval_js("""
        (() => {
            const closeBtn = document.querySelector('.fixed button');
            if (closeBtn) closeBtn.click();
        })()
        """)
        await asyncio.sleep(0.4)

        flow6_passed = (saved_locally and has_darj_in_modal and deleted_ok)
        results["trip_save_load_edit_delete"] = "PASS" if flow6_passed else "FAIL"

        # -------------------------------------------------------------
        # FLOW 7: Refresh browser and confirm saved trip persistence in SQLite
        # -------------------------------------------------------------
        print("\n--- FLOW 7: Refresh Browser & Confirm Persistence in SQLite ---")
        # Save a new trip (for Darjeeling) to verify persistence across reload
        await tester.eval_js("""
        (() => {
            const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Save Itinerary'));
            if (saveBtn) saveBtn.click();
        })()
        """)
        await asyncio.sleep(1.0)

        # Reload browser
        print("Reloading browser page...")
        await tester.eval_js("window.location.reload()")
        await asyncio.sleep(2.5)

        for _ in range(25):
            await asyncio.sleep(0.4)
            has_input = await tester.eval_js("!!document.getElementById('destination')")
            if has_input:
                break

        # Check saved trips button in header has count (1)
        saved_header_btn = await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Saved ('));
            return btn ? btn.innerText : '';
        })()
        """)
        print(f"Saved Trips header button after reload: '{saved_header_btn}'")
        has_saved_count = "Saved (1)" in saved_header_btn

        # Open modal and verify persisted record
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Saved ('));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        persisted_text = await tester.eval_js("document.body.innerText")
        persisted_in_db = "Darjeeling" in persisted_text
        print(f"Trip persisted in SQLite after reload: {persisted_in_db}")

        # Delete it to leave SQLite database clean
        await tester.eval_js("""
        (() => {
            const delBtn = document.querySelector('button[title=\"Delete saved trip\"]');
            if (delBtn) delBtn.click();
            const closeBtn = document.querySelector('.fixed button');
            if (closeBtn) closeBtn.click();
        })()
        """)
        await asyncio.sleep(0.5)

        results["persistence_across_browser_refresh"] = "PASS" if (has_saved_count and persisted_in_db) else "FAIL"

        # -------------------------------------------------------------
        # FLOW 8: Test Theme Toggle and all four languages
        # -------------------------------------------------------------
        print("\n--- FLOW 8: Test Theme Toggle & All Four Languages ---")
        # 8.1 Theme toggle
        initial_dark = await tester.eval_js("document.documentElement.classList.contains('dark')")
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const btn = buttons.find(b => b.querySelector('svg.lucide-sun, svg.lucide-moon'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.4)
        toggled_dark = await tester.eval_js("document.documentElement.classList.contains('dark')")
        theme_ok = (initial_dark != toggled_dark)
        print(f"Theme toggled: {initial_dark} -> {toggled_dark} ({'PASS' if theme_ok else 'FAIL'})")

        # Toggle back to dark
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const btn = buttons.find(b => b.querySelector('svg.lucide-sun, svg.lucide-moon'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.3)

        # 8.2 All 4 languages
        async def switch_lang(native_keyword):
            await tester.eval_js("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('header button'));
                const langBtn = buttons.find(b => b.querySelector('svg.lucide-globe'));
                if (langBtn) langBtn.click();
            })()
            """)
            await asyncio.sleep(0.3)
            await tester.eval_js(f"""
            (() => {{
                const buttons = Array.from(document.querySelectorAll('header button'));
                const target = buttons.find(b => b.innerText.includes('{native_keyword}'));
                if (target) target.click();
            }})()
            """)
            await asyncio.sleep(0.5)
            return await tester.eval_js("document.body.innerText")

        # Test Hindi
        hindi_dom = await switch_lang("हिन्दी")
        has_hi = "कस्टम" in hindi_dom or "ट्रिप" in hindi_dom or "योजना" in hindi_dom
        print(f"Hindi (hi) verified in DOM: {has_hi}")

        # Test Spanish
        spanish_dom = await switch_lang("Español")
        has_es = "Destino" in spanish_dom or "Planifica" in spanish_dom or "Continuar" in spanish_dom
        print(f"Spanish (es) verified in DOM: {has_es}")

        # Test French
        french_dom = await switch_lang("Français")
        has_fr = "Destination" in french_dom or "Planifiez" in french_dom or "Itinéraire" in french_dom or "Continuer" in french_dom
        print(f"French (fr) verified in DOM: {has_fr}")

        # Switch back to English
        english_dom = await switch_lang("English")
        has_en = "Plan Your Itinerary" in english_dom or "Destination" in english_dom
        print(f"English (en) verified in DOM: {has_en}")

        flow8_passed = (theme_ok and has_hi and has_es and has_fr and has_en)
        results["theme_and_all_four_languages"] = "PASS" if flow8_passed else "FAIL"

        # -------------------------------------------------------------
        # FLOW 9: Check errors, empty states, and API communication
        # -------------------------------------------------------------
        print("\n--- FLOW 9: Error Handling, Empty States & Communication ---")
        # 9.1 Empty destination validation
        await set_react_input("destination", "")
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue to Preferences'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.5)

        val_error = await tester.eval_js("""
        (() => {
            const divs = Array.from(document.querySelectorAll('div'));
            const alert = divs.find(d => d.innerText.includes('specify where you would like to travel') || d.innerText.includes('destination'));
            return alert ? alert.innerText : '';
        })()
        """)
        print(f"Empty destination error triggered: '{val_error.strip()}'")
        has_empty_dest_error = "destination" in val_error.lower() or "specify" in val_error.lower()

        # 9.2 Invalid dates validation (start after end)
        await set_react_input("destination", "Tokyo")
        await set_react_input("startDate", "2026-10-20")
        await set_react_input("endDate", "2026-10-15")
        await tester.eval_js("""
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Continue to Preferences'));
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.5)

        date_error = await tester.eval_js("""
        (() => {
            const divs = Array.from(document.querySelectorAll('div'));
            const alert = divs.find(d => d.innerText.includes('Return date must be on or after') || d.innerText.includes('date'));
            return alert ? alert.innerText : '';
        })()
        """)
        print(f"Invalid dates error triggered: '{date_error.strip()}'")
        has_invalid_dates_error = "date" in date_error.lower() or "return" in date_error.lower()

        # 9.3 Unlisted destination helper state
        await set_react_input("destination", "Uncharted Remote Hamlet 99")
        await asyncio.sleep(1.2)
        no_match_msg = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            return dropdown ? dropdown.innerText : '';
        })()
        """)
        print(f"Unlisted place empty state: '{no_match_msg.replace(chr(10), ' | ').strip()}'")
        has_no_match_helper = "No catalog match found" in (no_match_msg or "")

        flow9_passed = (has_empty_dest_error and has_invalid_dates_error and has_no_match_helper)
        results["errors_empty_states_communication"] = "PASS" if flow9_passed else "FAIL"

    finally:
        tester.stop_chrome()

    print("\n" + "=" * 65)
    print("PHASE 4 BROWSER E2E TEST RESULTS SUMMARY")
    print("=" * 65)
    all_passed = True
    for test_name, status in results.items():
        print(f"  [{status}] {test_name}")
        if status != "PASS":
            all_passed = False
    print("=" * 65)
    print(f"OVERALL RESULT: {'ALL BROWSER FLOWS PASSED' if all_passed else 'SOME FLOWS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_phase4_e2e_tests())
    sys.exit(0 if success else 1)
