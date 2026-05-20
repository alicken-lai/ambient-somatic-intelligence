"""Area 3: Non-interference and sandbox."""

from governance.civilization.cognition_sandbox_boundary import CognitionSandboxBoundary
from governance.civilization.non_interference import NonInterferenceGuard


def test_non_interference_respected() -> None:
    assert NonInterferenceGuard().check("Advisory hint only.").respected is True


def test_sandbox_blocks_exec() -> None:
    sb = CognitionSandboxBoundary()
    assert sb.evaluate("exec(os.system('x'))").contained is False
