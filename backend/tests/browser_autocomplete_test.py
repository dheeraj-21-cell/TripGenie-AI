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


async def run_autocomplete_browser_tests():
    tester = BrowserTester()
    tester.start_chrome()
    results = {}

    try:
        await tester.connect()
        print("Connected to Chrome CDP successfully.")

        # 1. Navigate to local Vite dev server
        await tester.send_cmd("Page.navigate", {"url": "http://127.0.0.1:5173/"})
        for _ in range(25):
            await asyncio.sleep(0.5)
            has_input = await tester.eval_js("!!document.getElementById('destination')")
            if has_input:
                break

        title = await tester.eval_js("document.title")
        print(f"Loaded page: '{title}'")

        # -----------------------------------------------------------------
        # TEST 1: Paris Autocomplete & Disambiguation (France vs Texas)
        # -----------------------------------------------------------------
        print("\n--- TEST 1: Testing Paris Autocomplete & Disambiguation ---")
        await tester.eval_js("""
        (() => {
            const input = document.getElementById('destination');
            input.focus();
            const lastVal = input.value;
            input.value = 'Paris';
            const tracker = input._valueTracker;
            if (tracker) {
                tracker.setValue(lastVal + '_trigger');
            }
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        })()
        """)
        # Wait for 250ms debounce and fetch
        await asyncio.sleep(1.2)

        paris_suggestions_json = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            if (!dropdown) return '[]';
            const buttons = Array.from(dropdown.querySelectorAll('button'));
            return JSON.stringify(buttons.map(b => b.innerText));
        })()
        """)
        paris_suggestions = json.loads(paris_suggestions_json) if paris_suggestions_json else []
        print(f"Suggestions for 'Paris' ({len(paris_suggestions)} items):")
        for s in paris_suggestions[:4]:
            print(f"   -> {s.replace(chr(10), ' | ')}")

        has_france = any("France" in s for s in paris_suggestions)
        has_texas = any("Texas" in s or "United States" in s for s in paris_suggestions)
        results["paris_disambiguation"] = "PASS" if (has_france and has_texas) else "FAIL"
        print(f"Paris disambiguation (France & Texas both present): {results['paris_disambiguation']}")

        # Click the first suggestion (Paris, France)
        await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            const btn = dropdown ? dropdown.querySelector('button') : null;
            if (btn) btn.click();
        })()
        """)
        await asyncio.sleep(0.5)
        selected_val = await tester.eval_js("document.getElementById('destination').value")
        print(f"Selected destination value: '{selected_val}'")
        results["select_suggestion"] = "PASS" if "Paris" in selected_val and "France" in selected_val else "FAIL"

        # -----------------------------------------------------------------
        # TEST 2: Country Search (e.g. "Iceland")
        # -----------------------------------------------------------------
        print("\n--- TEST 2: Testing Country Search ('Iceland') ---")
        await tester.eval_js("""
        (() => {
            const input = document.getElementById('destination');
            input.focus();
            const lastVal = input.value;
            input.value = 'Iceland';
            const tracker = input._valueTracker;
            if (tracker) {
                tracker.setValue(lastVal + '_trigger');
            }
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        })()
        """)
        await asyncio.sleep(1.2)

        iceland_suggestions_json = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            if (!dropdown) return '[]';
            const buttons = Array.from(dropdown.querySelectorAll('button'));
            return JSON.stringify(buttons.map(b => b.innerText));
        })()
        """)
        iceland_suggestions = json.loads(iceland_suggestions_json) if iceland_suggestions_json else []
        print(f"Suggestions for 'Iceland': {[s.replace(chr(10), ' | ') for s in iceland_suggestions[:3]]}")
        results["country_search_iceland"] = "PASS" if any("Iceland" in s for s in iceland_suggestions) else "FAIL"

        # -----------------------------------------------------------------
        # TEST 3: Less-Famous Town Search ("Banff")
        # -----------------------------------------------------------------
        print("\n--- TEST 3: Testing Town Search ('Banff') ---")
        await tester.eval_js("""
        (() => {
            const input = document.getElementById('destination');
            input.focus();
            const lastVal = input.value;
            input.value = 'Banff';
            const tracker = input._valueTracker;
            if (tracker) {
                tracker.setValue(lastVal + '_trigger');
            }
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
        })()
        """)
        await asyncio.sleep(1.2)

        banff_suggestions_json = await tester.eval_js("""
        (() => {
            const dropdown = document.getElementById('destination-autocomplete-dropdown');
            if (!dropdown) return '[]';
            const buttons = Array.from(dropdown.querySelectorAll('button'));
            return JSON.stringify(buttons.map(b => b.innerText));
        })()
        """)
        banff_suggestions = json.loads(banff_suggestions_json) if banff_suggestions_json else []
        print(f"Suggestions for 'Banff': {[s.replace(chr(10), ' | ') for s in banff_suggestions]}")
        results["town_search_banff"] = "PASS" if any("Canada" in s and "Banff" in s for s in banff_suggestions) else "FAIL"

        # -----------------------------------------------------------------
        # TEST 4: Unlisted / Custom Place Free Typing & No-Result Message
        # -----------------------------------------------------------------
        print("\n--- TEST 4: Testing Unlisted Free-Typing ('Secret Wilderness 42') ---")
        custom_place = "Secret Wilderness 42"
        await tester.eval_js(f"""
        (() => {{
            const input = document.getElementById('destination');
            input.focus();
            const lastVal = input.value;
            input.value = '{custom_place}';
            const tracker = input._valueTracker;
            if (tracker) {{
                tracker.setValue(lastVal + '_trigger');
            }}
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }})()
        """)
        await asyncio.sleep(1.2)

        no_result_text = await tester.eval_js("""
        (() => {
            const el = document.getElementById('destination-autocomplete-dropdown');
            return el ? el.innerText : '';
        })()
        """)
        print(f"Dropdown text for custom unlisted place: '{no_result_text.replace(chr(10), ' | ').strip()}'")
        results["no_catalog_match_message"] = "PASS" if "No catalog match" in (no_result_text or "") else "FAIL"

        # -----------------------------------------------------------------
        # TEST 5: Manual Entry End-to-End Progression
        # -----------------------------------------------------------------
        print("\n--- TEST 5: Manual Entry Can Proceed to Next Step ---")
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
            setInput('startDate', '2026-08-10');
            setInput('endDate', '2026-08-14');
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

        step2_rendered = await tester.eval_js("""
        (() => {
            return document.body.innerText.includes('Travel Style') || document.body.innerText.includes('Pace');
        })()
        """)
        results["manual_entry_proceeds_to_step2"] = "PASS" if step2_rendered else "FAIL"
        print(f"Step 2 rendered with custom place: {results['manual_entry_proceeds_to_step2']}")

        # -----------------------------------------------------------------
        # TEST 6: Complete Itinerary Generation with Custom Destination
        # -----------------------------------------------------------------
        print("\n--- TEST 6: Generate Itinerary with Custom Destination ---")
        # Click Continue to Review
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const nextBtn = buttons.find(b => b.innerText.includes('Continue to Review'));
            if (nextBtn) nextBtn.click();
        })()
        """)
        await asyncio.sleep(0.8)

        # Click Generate Itinerary
        await tester.eval_js("""
        (() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            const genBtn = buttons.find(b => b.innerText.includes('Generate') || b.innerText.includes('Trip'));
            if (genBtn) genBtn.click();
        })()
        """)

        # Wait for itinerary to be rendered
        generated_found = False
        destination_rendered = ""
        for _ in range(30):
            await asyncio.sleep(0.5)
            destination_rendered = await tester.eval_js("""
            (() => {
                const heading = document.querySelector('h3.font-editorial');
                if (heading) return heading.innerText;
                const matches = document.body.innerText.includes('Secret Wilderness 42');
                return matches ? 'Secret Wilderness 42' : '';
            })()
            """)
            if custom_place.lower() in (destination_rendered or "").lower():
                generated_found = True
                break

        print(f"Generated Destination in DOM: '{destination_rendered}'")
        results["custom_destination_itinerary"] = "PASS" if generated_found else "FAIL"

    finally:
        tester.stop_chrome()

    print("\n" + "=" * 60)
    print("BROWSER AUTOCOMPLETE E2E TEST SUMMARY")
    print("=" * 60)
    all_passed = True
    for test_name, status in results.items():
        print(f"  [{status}] {test_name}")
        if status != "PASS":
            all_passed = False
    print("=" * 60)
    print(f"Overall Result: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_autocomplete_browser_tests())
    sys.exit(0 if success else 1)
