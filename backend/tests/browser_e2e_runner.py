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

async def run_e2e_tests():
    tester = BrowserTester()
    tester.start_chrome()
    results = {}

    try:
        await tester.connect()
        print("Connected to Chrome via DevTools Protocol!")

        # 1. Navigate to local Vite frontend
        await tester.send_cmd("Page.navigate", {"url": "http://127.0.0.1:5173/"})

        # Wait for React to mount and render #destination
        for _ in range(25):
            await asyncio.sleep(0.5)
            has_input = await tester.eval_js("!!document.getElementById('destination')")
            if has_input:
                break

        title = await tester.eval_js("document.title")
        print(f"Page Title: {title}")
        results["page_load"] = "PASS" if "TripGenie" in title else "FAIL"

        # -------------------------------------------------------------
        # FLOW 1: Custom Destination Free Typing & Travel Dates
        # -------------------------------------------------------------
        print("\n--- Testing Custom Destination Free Typing & Dates ---")
        dest_val = await tester.eval_js("""
            (() => {
                function setReactInput(input, value) {
                    const previousValue = input.value;
                    input.value = value;
                    const tracker = input._valueTracker;
                    if (tracker) {
                        tracker.setValue(previousValue + '_reset');
                    }
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }

                const dest = document.getElementById('destination');
                const start = document.getElementById('startDate');
                const end = document.getElementById('endDate');

                setReactInput(dest, 'Reykjavik');
                setReactInput(start, '2026-06-15');
                setReactInput(end, '2026-06-18');

                return {
                    dest: dest.value,
                    start: start.value,
                    end: end.value
                };
            })()
        """)
        print(f"Custom Destination and Dates set: {dest_val}")
        results["custom_destination"] = "PASS" if dest_val.get("dest") == "Reykjavik" else "FAIL"

        # -------------------------------------------------------------
        # FLOW 2: Complete All Three Form Steps
        # -------------------------------------------------------------
        print("\n--- Testing 3-Step Wizard Navigation ---")
        # Step 1 -> Step 2
        await tester.eval_js("""
            (() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b =>
                    b.innerText.includes('Continue to Preferences')
                );
                if (btn) btn.click();
            })()
        """)
        await asyncio.sleep(0.8)

        step2_check = await tester.eval_js("""
            (() => {
                return document.body.innerText.includes('Travelers & Style') || document.body.innerText.includes('Step 2');
            })()
        """)
        print(f"Step 2 reached: {step2_check}")

        # Step 2 -> Step 3
        await tester.eval_js("""
            (() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b =>
                    b.innerText.includes('Continue to Review')
                );
                if (btn) btn.click();
            })()
        """)
        await asyncio.sleep(0.8)

        step3_reached = await tester.eval_js("""
            (() => {
                return Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('Generate Itinerary'));
            })()
        """)
        print(f"Step 3 reached (Generate button visible): {step3_reached}")
        results["three_step_form"] = "PASS" if (step2_check and step3_reached) else "FAIL"

        # -------------------------------------------------------------
        # FLOW 3: Generate Itinerary in Mock Mode
        # -------------------------------------------------------------
        print("\n--- Testing Itinerary Generation in Mock Mode ---")
        gen_clicked = await tester.eval_js("""
            (() => {
                const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Generate Itinerary'));
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            })()
        """)
        print(f"Generate button clicked: {gen_clicked}")

        generated = False
        for _ in range(15):
            await asyncio.sleep(1)
            status = await tester.eval_js("""
                (() => {
                    const text = document.body.innerText;
                    const hasReykjavik = text.includes('Reykjavik');
                    const hasFallback = text.includes('Fallback Preview') || text.includes('Mock');
                    const hasDays = text.includes('Day 1') || text.includes('recommendations');
                    return { hasReykjavik, hasFallback, hasDays };
                })()
            """)
            if status.get("hasReykjavik") and status.get("hasDays"):
                generated = True
                print("Generated itinerary rendered in DOM:", status)
                break

        results["itinerary_generation"] = "PASS" if generated else "FAIL"

        # -------------------------------------------------------------
        # FLOW 4: Verify Daily Activities, Budget Estimates & Language
        # -------------------------------------------------------------
        print("\n--- Verifying Daily Activities & Budget Estimates ---")
        details = await tester.eval_js("""
            (() => {
                const text = document.body.innerText;
                const upper = text.toUpperCase();
                const hasActivities = text.includes('recommendations') && (text.includes('Morning') || text.includes('Day 1'));
                const hasBudget = upper.includes('TOTAL BUDGET') && text.includes('$');
                const hasSourceBadge = text.includes('Fallback Preview');
                const hasBreakdown = text.includes('Lodging') || text.includes('Food & Dining');
                return { hasActivities, hasBudget, hasSourceBadge, hasBreakdown };
            })()
        """)
        print("Verified details:", details)
        if details.get("hasActivities") and details.get("hasBudget"):
            results["activities_and_budget"] = "PASS"
        else:
            results["activities_and_budget"] = "FAIL"

        # -------------------------------------------------------------
        # FLOW 5: In-Place Activity Editing
        # -------------------------------------------------------------
        print("\n--- Testing In-Place Activity Editing ---")
        await tester.eval_js("""
            (() => {
                const editBtn = document.querySelector('button[title=\"Edit activity\"]');
                if (editBtn) editBtn.click();
            })()
        """)
        await asyncio.sleep(0.6)

        await tester.eval_js("""
            (() => {
                function setReactInput(input, value) {
                    const previousValue = input.value;
                    input.value = value;
                    const tracker = input._valueTracker;
                    if (tracker) tracker.setValue(previousValue + '_reset');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }

                const inputs = Array.from(document.querySelectorAll('.fixed input'));
                if (inputs.length > 0) {
                    setReactInput(inputs[0], 'Reykjavik Geothermal Lagoon & Artisan Bakery');
                }
                const saveBtn = Array.from(document.querySelectorAll('.fixed button')).find(b => b.innerText.includes('Save Changes'));
                if (saveBtn) saveBtn.click();
            })()
        """)
        await asyncio.sleep(0.6)

        has_edited_text = await tester.eval_js("""
            (() => {
                return document.body.innerText.includes('Reykjavik Geothermal Lagoon & Artisan Bakery');
            })()
        """)
        print(f"Activity edited and rendered in DOM: {has_edited_text}")
        results["edit_activity"] = "PASS" if has_edited_text else "FAIL"

        # -------------------------------------------------------------
        # FLOW 6: Single-Day Itinerary Regeneration
        # -------------------------------------------------------------
        print("\n--- Testing Single-Day Itinerary Regeneration ---")
        await tester.eval_js("""
            (() => {
                const regenBtn = document.querySelector('button[title*=\"Regenerate\"]');
                if (regenBtn) regenBtn.click();
            })()
        """)
        await asyncio.sleep(1.8)

        regen_verified = await tester.eval_js("""
            (() => {
                const text = document.body.innerText;
                return text.includes('Alternative Option') || text.includes('Fresh morning recommendation');
            })()
        """)
        print(f"Day regenerated with alternative recommendations: {regen_verified}")
        results["regenerate_day"] = "PASS" if regen_verified else "FAIL"

        # -------------------------------------------------------------
        # FLOW 7: Save Trip & Local SQLite Persistence
        # -------------------------------------------------------------
        print("\n--- Testing Save Trip to Local SQLite DB ---")
        await tester.eval_js("""
            (() => {
                const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Save Itinerary'));
                if (saveBtn) saveBtn.click();
            })()
        """)
        await asyncio.sleep(1.2)

        saved_locally = await tester.eval_js("""
            (() => {
                return document.body.innerText.includes('Saved Locally');
            })()
        """)
        print(f"Trip marked as Saved Locally: {saved_locally}")
        results["save_trip"] = "PASS" if saved_locally else "FAIL"

        # -------------------------------------------------------------
        # FLOW 8: Saved Trips Modal & Loading Saved Itinerary
        # -------------------------------------------------------------
        print("\n--- Testing Saved Trips Modal & Retrieval ---")
        await tester.eval_js("""
            (() => {
                const savedBtn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Saved ('));
                if (savedBtn) savedBtn.click();
            })()
        """)
        await asyncio.sleep(0.8)

        modal_has_trip = await tester.eval_js("""
            (() => {
                const text = document.body.innerText;
                return text.includes('Reykjavik') && text.includes('Saved Itineraries');
            })()
        """)
        print(f"Saved Trips modal displays Reykjavik: {modal_has_trip}")
        results["list_saved_trips"] = "PASS" if modal_has_trip else "FAIL"

        # -------------------------------------------------------------
        # FLOW 9: Delete Trip from Local SQLite
        # -------------------------------------------------------------
        print("\n--- Testing Deletion of Saved Trip ---")
        await tester.eval_js("""
            (() => {
                const delBtn = document.querySelector('button[title=\"Delete saved trip\"]');
                if (delBtn) delBtn.click();
            })()
        """)
        await asyncio.sleep(0.8)

        deleted_verified = await tester.eval_js("""
            (() => {
                const text = document.body.innerText;
                return !text.includes('Reykjavik') || text.includes('No Saved Itineraries Yet');
            })()
        """)
        print(f"Trip deleted from local list: {deleted_verified}")
        results["delete_trip"] = "PASS" if deleted_verified else "FAIL"

        # Close saved modal
        await tester.eval_js("""
            (() => {
                const closeBtn = document.querySelector('.fixed button');
                if (closeBtn) closeBtn.click();
            })()
        """)
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # FLOW 10: Refresh Browser & Verify Persistence / Clean State
        # -------------------------------------------------------------
        print("\n--- Testing Page Reload & React Hydration ---")
        await tester.eval_js("window.location.reload()")
        await asyncio.sleep(2.0)

        reload_check = await tester.eval_js("""
            (() => {
                const hasPlanner = !!document.getElementById('destination');
                const hasSavedBtn = Array.from(document.querySelectorAll('button')).some(b => b.innerText.includes('Saved ('));
                return hasPlanner && hasSavedBtn;
            })()
        """)
        print(f"Page reloaded cleanly and form responsive: {reload_check}")
        results["page_reload_persistence"] = "PASS" if reload_check else "FAIL"

        # -------------------------------------------------------------
        # FLOW 11: Validation on Empty Destination
        # -------------------------------------------------------------
        print("\n--- Testing Validation on Empty Destination ---")
        await tester.eval_js("""
            (() => {
                function setReactInput(input, value) {
                    const previousValue = input.value;
                    input.value = value;
                    const tracker = input._valueTracker;
                    if (tracker) tracker.setValue(previousValue + '_reset');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }

                const dest = document.getElementById('destination');
                const start = document.getElementById('startDate');
                const end = document.getElementById('endDate');

                setReactInput(dest, '');
                setReactInput(start, '2026-06-15');
                setReactInput(end, '2026-06-18');

                const nextBtn = Array.from(document.querySelectorAll('button')).find(b =>
                    b.innerText.includes('Continue to Preferences')
                );
                if (nextBtn) nextBtn.click();
            })()
        """)
        await asyncio.sleep(0.6)

        val_result = await tester.eval_js("""
            (() => {
                return document.body.innerText.includes('Please enter a destination') || document.body.innerText.includes('⚠️');
            })()
        """)
        print(f"Empty destination validation triggered: {val_result}")
        results["empty_destination_validation"] = "PASS" if val_result else "FAIL"

    finally:
        tester.stop_chrome()

    print("\n==========================================")
    print("BROWSER TEST SUMMARY:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(run_e2e_tests())
