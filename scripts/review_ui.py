"""Inspect the owned local preview through a separately launched Edge CDP port."""

import asyncio
import base64
import json
from pathlib import Path
import urllib.request

from websockets.asyncio.client import connect


async def main():
    with urllib.request.urlopen("http://127.0.0.1:9223/json", timeout=5) as response:
        tabs = json.load(response)
    target = next(tab for tab in tabs if tab["type"] == "page")
    async with connect(target["webSocketDebuggerUrl"], max_size=16 * 1024 * 1024) as socket:
        sequence = 0
        async def call(method, params=None):
            nonlocal sequence
            sequence += 1
            await socket.send(json.dumps({"id": sequence, "method": method, "params": params or {}}))
            while True:
                reply = json.loads(await asyncio.wait_for(socket.recv(), timeout=30))
                if reply.get("id") == sequence:
                    if "error" in reply:
                        raise RuntimeError(reply["error"])
                    return reply.get("result", {})
        await call("Page.enable")
        await call("Emulation.setDeviceMetricsOverride", {"width": 1536, "height": 1100, "deviceScaleFactor": 1, "mobile": False})
        await call("Page.navigate", {"url": "http://127.0.0.1:8501"})
        for _ in range(60):
            result = await call("Runtime.evaluate", {"expression": "document.body.innerText.includes('Better code.') && document.body.innerText.includes('Build your agent')", "returnByValue": True})
            if result.get("result", {}).get("value"):
                break
            await asyncio.sleep(0.5)
        else:
            raise RuntimeError("Workspace did not finish rendering")
        await asyncio.sleep(1)
        result = await call("Page.captureScreenshot", {"format": "png"})
        root = Path(__file__).resolve().parents[1] / "artifacts"
        (root / "ui-overview-reviewed.png").write_bytes(base64.b64decode(result["data"]))
        print("Rendered desktop workspace", flush=True)
        for title in ("Repair workbench", "Models & API", "Usage & cost", "Training studio", "Deployment", "Run history", "Research & reports"):
            expression = "Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes(" + json.dumps(title) + "))?.click()"
            await call("Runtime.evaluate", {"expression": expression})
            await asyncio.sleep(1)
            screenshot = await call("Page.captureScreenshot", {"format": "png"})
            name = title.lower().replace(" & ", "-").replace(" ", "-")
            (root / f"ui-{name}.png").write_bytes(base64.b64decode(screenshot["data"]))
        await call("Runtime.evaluate", {"expression": "Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Overview'))?.click()"})
        await asyncio.sleep(1)
        await call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
        await asyncio.sleep(1)
        screenshot = await call("Page.captureScreenshot", {"format": "png"})
        (root / "ui-mobile.png").write_bytes(base64.b64decode(screenshot["data"]))
        print("Captured models, training, history, research and mobile views", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
