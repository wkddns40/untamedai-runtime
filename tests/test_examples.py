import importlib.util
import sys
from pathlib import Path
from types import ModuleType

APP_PATH = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "provider_prompt_override"
    / "app.py"
)


def _load_example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("provider_prompt_override", APP_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load provider prompt override example.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


async def test_provider_prompt_override_example_runs() -> None:
    module = _load_example_module()

    result = await module.run_turn()

    assert result["system_prompt"] == (
        "consumer-policy: answer in en; keep responses compact."
    )
    assert result["emit"][0]["content"] == (
        "Override demo: handled 'hello from my app' with app-owned policy."
    )
