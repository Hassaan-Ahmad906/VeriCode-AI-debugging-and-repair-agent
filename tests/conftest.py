from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-docker", action="store_true", default=False,
                     help="Run trusted integration fixtures inside the VeriCode Docker image")


def pytest_configure(config):
    config.addinivalue_line("markers", "docker: explicit opt-in Linux Docker integration check")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-docker"):
        for item in items:
            if "docker" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="requires explicit --run-docker"))


@pytest.fixture
def docker_executor():
    from vericode.docker_executor import DockerExecutor, SandboxUnavailable

    runner = DockerExecutor()
    try:
        runner.prepare()
    except SandboxUnavailable as exc:
        pytest.fail(f"Docker checks were explicitly requested but unavailable: {exc}")
    return runner


@pytest.fixture
def data_root() -> Path:
    return Path(__file__).resolve().parents[1] / "data"
