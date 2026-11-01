from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    print("launching...", flush=True)
    b = p.chromium.launch(args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--single-process"])
    print("launched", flush=True)
    page = b.new_page(viewport={"width": 390, "height": 300})
    print("page ok", flush=True)
    page.set_content("<h1 style='font:700 40px sans-serif;color:#3d2a17;background:#f7e7c6'>halo dunia</h1>")
    print("content ok", flush=True)
    page.screenshot(path="/tmp/t.png")
    print("shot ok", flush=True)
    b.close()
    print("selesai")
