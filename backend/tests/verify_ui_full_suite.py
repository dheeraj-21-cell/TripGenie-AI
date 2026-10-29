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


async def run_full_ui_verification():
    tester = BrowserTester()
    tester.start_chrome()
    results = {}

    try:
        await tester.connect()
        print("Connected to Chrome via DevTools Protocol!")

        # Navigate to Vite dev server
        await tester.send_cmd("Page.navigate", {"url": "http://127.0.0.1:5173/"})
        for _ in range(25):
            await asyncio.sleep(0.5)
            has_input = await tester.eval_js("!!document.getElementById('destination')")
            if has_input:
                break

        title = await tester.eval_js("document.title")
        print(f"Loaded TripGenie UI: '{title}'")

        # -------------------------------------------------------------
        # 1. THEME TOGGLE VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 1. Testing Theme Toggle ---")
        initial_dark = await tester.eval_js("document.documentElement.classList.contains('dark')")
        print(f"Initial theme dark: {initial_dark}")

        # Click theme toggle button
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const btn = buttons.find(b =>
                (b.getAttribute('aria-label') && b.getAttribute('aria-label').toLowerCase().includes('theme')) ||
                b.querySelector('svg.lucide-sun, svg.lucide-moon')
            );
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.5)
        toggled_dark = await tester.eval_js("document.documentElement.classList.contains('dark')")
        print(f"Theme after toggle dark: {toggled_dark}")
        theme_passed = (initial_dark != toggled_dark)
        results["theme_toggle"] = "PASS" if theme_passed else "FAIL"

        # Toggle back to dark
        if theme_passed and not toggled_dark:
            await tester.eval_js("""
            (() => {
                const buttons = Array.from(document.querySelectorAll('header button'));
                const btn = buttons.find(b =>
                    (b.getAttribute('aria-label') && b.getAttribute('aria-label').toLowerCase().includes('theme')) ||
                    b.querySelector('svg.lucide-sun, svg.lucide-moon')
                );
                if (btn) btn.click();
            })()
            """)
            await asyncio.sleep(0.3)

        # -------------------------------------------------------------
        # 2. MULTILINGUAL LANGUAGE SELECTOR VERIFICATION
        # -------------------------------------------------------------
        print("\n--- 2. Testing Multilingual Language Selector ---")
        # Open language dropdown and click Hindi
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const langBtn = buttons.find(b => b.querySelector('svg.lucide-globe'));
            if (langBtn) langBtn.click();
        })()
        """)
        await asyncio.sleep(0.3)

        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const hiBtn = buttons.find(b => b.innerText.includes('हिन्दी') || b.innerText.includes('Hindi'));
            if (hiBtn) hiBtn.click();
        })()
        """)
        await asyncio.sleep(0.6)
        body_text_hi = await tester.eval_js("document.body.innerText")
        has_hindi = "कस्टम" in body_text_hi or "योजना" in body_text_hi or "ट्रिप" in body_text_hi or "स्थान" in body_text_hi or "दिन" in body_text_hi
        print(f"Hindi text detected in DOM: {has_hindi}")

        # Switch to Spanish
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const langBtn = buttons.find(b => b.querySelector('svg.lucide-globe'));
            if (langBtn) langBtn.click();
        })()
        """)
        await asyncio.sleep(0.3)

        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const esBtn = buttons.find(b => b.innerText.includes('Español') || b.innerText.includes('Spanish'));
            if (esBtn) esBtn.click();
        })()
        """)
        await asyncio.sleep(0.6)
        body_text_es = await tester.eval_js("document.body.innerText")
        has_spanish = "Destino" in body_text_es or "Continuar" in body_text_es or "Presupuesto" in body_text_es or "Personalizado" in body_text_es
        print(f"Spanish text detected in DOM: {has_spanish}")

        # Switch back to English
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const langBtn = buttons.find(b => b.querySelector('svg.lucide-globe'));
            if (langBtn) langBtn.click();
        })()
        """)
        await asyncio.sleep(0.3)

        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('header button'));
            const enBtn = buttons.find(b => b.innerText.includes('English'));
            if (enBtn) enBtn.click();
        })()
        """)
        await asyncio.sleep(0.4)
        results["language_selector"] = "PASS" if (has_hindi and has_spanish) else "FAIL"

        # Helper to set input value safely in React
        async def type_in_destination(val):
            await tester.eval_js(f"""
            (() => {{
                const input = document.getElementById('destination');
                input.focus();
                const lastVal = input.value;
                input.value = '{val}';
                if (input._valueTracker) input._valueTracker.setValue(lastVal + '_trigger');
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }})()
            """)
            await asyncio.sleep(1.2)

        async def get_dropdown_items():
            raw = await tester.eval_js("""
            (() => {
                const dropdown = document.getElementById('destination-autocomplete-dropdown');
                if (!dropdown) return '[]';
                const buttons = Array.from(dropdown.querySelectorAll('button'));
                return JSON.stringify(buttons.map(b => b.innerText));
            })()
            """)
            return json.loads(raw) if raw else []

        async def get_dropdown_text():
            return await tester.eval_js("""
            (() => {
                const dropdown = document.getElementById('destination-autocomplete-dropdown');
                return dropdown ? dropdown.innerText : '';
            })()
            """)

        # -------------------------------------------------------------
        # 3. COUNTRIES ACROSS CONTINENTS IN UI
        # -------------------------------------------------------------
        print("\n--- 3. Testing Countries in Autocomplete UI ---")
        await type_in_destination("Iceland")
        iceland_items = await get_dropdown_items()
        print(f"UI items for 'Iceland': {[i.replace(chr(10), ' | ') for i in iceland_items[:2]]}")
        has_iceland_country = any("Iceland" in i and "COUNTRY" in i.upper() for i in iceland_items)
        results["ui_country_search"] = "PASS" if has_iceland_country else "FAIL"

        # -------------------------------------------------------------
        # 4. MAJOR CITIES & LESS-FAMOUS TOWNS IN UI
        # -------------------------------------------------------------
        print("\n--- 4. Testing Major Cities and Less-Famous Towns in UI ---")
        # India less-famous town: Manali
        await type_in_destination("Manali")
        manali_items = await get_dropdown_items()
        print(f"UI items for 'Manali': {[i.replace(chr(10), ' | ') for i in manali_items[:2]]}")
        has_manali = any("Himachal Pradesh" in i and "India" in i for i in manali_items)

        # Europe town: Banff (Americas) or Zermatt (Europe)
        await type_in_destination("Banff")
        banff_items = await get_dropdown_items()
        print(f"UI items for 'Banff': {[i.replace(chr(10), ' | ') for i in banff_items]}")
        has_banff = any("Alberta" in i and "Canada" in i for i in banff_items)

        results["ui_towns_search"] = "PASS" if (has_manali and has_banff) else "FAIL"

        # -------------------------------------------------------------
        # 5. DUPLICATE PLACE NAMES DISAMBIGUATION IN UI
        # -------------------------------------------------------------
        print("\n--- 5. Testing Duplicate Names Disambiguation in UI ---")
        await type_in_destination("Paris")
        paris_items = await get_dropdown_items()
        print(f"UI items for 'Paris': {[i.replace(chr(10), ' | ') for i in paris_items[:3]]}")
        has_paris_fr = any("France" in i for i in paris_items)
        has_paris_us = any("Texas" in i or "United States" in i for i in paris_items)
        results["ui_duplicate_names_disambiguation"] = "PASS" if (has_paris_fr and has_paris_us) else "FAIL"

        # Click Paris, France suggestion
        await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            const btn = dropdown ? dropdown.querySelector('button') : null;
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.4)
        selected_dest = await tester.eval_js("document.getElementById('destination').value")
        print(f"Selected destination after click: '{selected_dest}'")
        results["ui_select_suggestion"] = "PASS" if "Paris" in selected_dest and "France" in selected_dest else "FAIL"

        # -------------------------------------------------------------
        # 6. UNLISTED REMOTE HAMLET / ZERO SUGGESTIONS IN UI
        # -------------------------------------------------------------
        print("\n--- 6. Testing Unlisted Remote Village / No Matches in UI ---")
        unlisted_name = "Ollantaytambo Hidden Farmstead 88"
        await type_in_destination(unlisted_name)
        unlisted_text = await get_dropdown_text()
        print(f"Dropdown message for unlisted place: '{unlisted_text.replace(chr(10), ' | ').strip()}'")
        has_no_match = "No catalog match found" in (unlisted_text or "")
        has_reassurance = "You can still type and plan a trip" in (unlisted_text or "")
        results["ui_no_results_state"] = "PASS" if (has_no_match and has_reassurance) else "FAIL"

        # -------------------------------------------------------------
        # 7. CONFIRM MANUAL ENTRY WITH ZERO SUGGESTIONS PROCEEDS TO STEP 2
        # -------------------------------------------------------------
        print("\n--- 7. Confirming Manual Entry with Zero Suggestions ---")
        # Fill dates
        await tester.eval_js("""
        (() => {
            function setInput(id, val) {
                const el = document.getElementById(id);
                const prev = el.value;
                el.value = val;
                if (el._valueTracker) el._valueTracker.setValue(prev + '_reset');
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            }
            setInput('startDate', '2026-07-10');
            setInput('endDate', '2026-07-15');
        })()
        """)
        await asyncio.sleep(0.3)

        # Click Continue to Preferences
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const nextBtn = buttons.find(b => b.innerText.includes('Continue to Preferences'));
            if (nextBtn) nextBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        step2_active = await tester.eval_js("""
        (() => {
            return document.body.innerText.includes('Travel Style') || document.body.innerText.includes('Pace');
        })()
        """)
        print(f"Advanced to Step 2 with manual unlisted entry: {step2_active}")
        results["manual_entry_without_suggestions"] = "PASS" if step2_active else "FAIL"

        # -------------------------------------------------------------
        # 8. COMPLETE ITINERARY GENERATION WITH MANUAL UNLISTED DESTINATION
        # -------------------------------------------------------------
        print("\n--- 8. Testing Itinerary Generation with Manual Destination ---")
        # Step 2 -> Step 3
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const nextBtn = buttons.find(b => b.innerText.includes('Continue to Review'));
            if (nextBtn) nextBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        # Click Generate Itinerary with Groq AI
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const genBtn = buttons.find(b => b.innerText.includes('Generate') || b.innerText.includes('Trip'));
            if (genBtn) genBtn.click();
        })()
        """)

        # Poll for rendered itinerary
        itinerary_rendered = False
        heading_text = ""
        for _ in range(30):
            await asyncio.sleep(0.5)
            heading_text = await tester.eval_js("""
            (() => {
                const heading = document.querySelector('h3.font-editorial');
                if (heading) return heading.innerText;
                return document.body.innerText.includes('Ollantaytambo Hidden Farmstead 88') ? 'Ollantaytambo Hidden Farmstead 88' : '';
            })()
            """)
            if unlisted_name.lower() in (heading_text or "").lower():
                itinerary_rendered = True
                break

        print(f"Generated Itinerary Heading in DOM: '{heading_text}'")
        results["itinerary_generation"] = "PASS" if itinerary_rendered else "FAIL"

    finally:
        tester.stop_chrome()

    print("\n" + "=" * 65)
    print("BROWSER UI VERIFICATION SUMMARY")
    print("=" * 65)
    all_passed = True
    for test_name, status in results.items():
        print(f"  [{status}] {test_name}")
        if status != "PASS":
            all_passed = False
    print("=" * 65)
    print(f"FINAL RESULT: {'ALL BROWSER UI CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_full_ui_verification())
    sys.exit(0 if success else 1)
