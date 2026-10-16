"""Download a pinned official Ollama portable runtime into ignored workspace artifacts.

No global install, registry changes, model execution, or paid service. CPU-only
runtime files are extracted; GPU libraries are unnecessary on this laptop.
"""

import hashlib
import time
from pathlib import Path, PurePosixPath
import urllib.request
import zipfile

VERSION = "v0.40.5"
URL = f"https://github.com/ollama/ollama/releases/download/{VERSION}/ollama-windows-amd64.zip"
SHA256 = "5134ce7e3bc8e94d0494721c799ec293b429450d0c52461b0ee3647dd3bb4bb7"
ASSET_SIZE = 1_471_226_485


def main():
    root = Path(__file__).resolve().parents[1] / "artifacts/local-model"
    root.mkdir(parents=True, exist_ok=True)
    archive = root / f"ollama-{VERSION}.zip"
    digest = hashlib.sha256()
    for attempt in range(4):
        count = archive.stat().st_size if archive.exists() else 0
        if count == ASSET_SIZE:
            break
        if count > ASSET_SIZE:
            raise RuntimeError("archive exceeds reviewed asset size; preserve it and investigate")
        request = urllib.request.Request(URL, headers={"Range": f"bytes={count}-"} if count else {})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                if count and (response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {count}-")):
                    raise RuntimeError("server did not honor resume range; existing partial download preserved")
                with archive.open("ab" if count else "xb") as output:
                    next_notice = (count // (100 * 1024 * 1024) + 1) * 100 * 1024 * 1024
                    while block := response.read(1024 * 1024):
                        count += len(block)
                        if count > ASSET_SIZE:
                            raise RuntimeError("runtime download exceeds reviewed asset size")
                        output.write(block)
                        if count >= next_notice:
                            print(f"Downloaded {count // (1024 * 1024)} MiB", flush=True)
                            next_notice += 100 * 1024 * 1024
            if count != ASSET_SIZE:
                raise OSError("incomplete runtime download")
        except OSError:
            if attempt == 3:
                raise
            print("Download interrupted; resuming verified byte range", flush=True)
            time.sleep(1)
    if archive.stat().st_size != ASSET_SIZE:
        raise RuntimeError("incomplete runtime archive")
    with archive.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    if digest.hexdigest() != SHA256:
        raise RuntimeError("runtime checksum mismatch; no executable extracted")
    runtime = root / "runtime"
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        for item in members:
            path = PurePosixPath(item.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or ":" in str(path):
                raise RuntimeError("unsafe archive path")
            # Official Windows package includes large CUDA/Vulkan libraries.
            # ollama.exe and CPU backend libraries suffice for CPU inference.
            if path.name != "ollama.exe" and not str(path).startswith("lib/ollama/"):
                continue
            if any(p.startswith(("cuda", "rocm", "vulkan", "mlx")) for p in path.parts):
                continue
            target = (runtime / str(path)).resolve()
            if not target.is_relative_to(runtime.resolve()):
                raise RuntimeError("archive path escapes runtime")
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise FileExistsError(target)
                with bundle.open(item) as source, target.open("xb") as destination:
                    while block := source.read(1024 * 1024):
                        destination.write(block)
    print(f"Verified {VERSION}; CPU runtime extracted to {runtime}", flush=True)


if __name__ == "__main__":
    main()
