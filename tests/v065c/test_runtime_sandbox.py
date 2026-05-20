"""Area 2: Runtime sandbox + doctrine scope."""

from governance.external.runtime.doctrine_runtime_scope import DoctrineRuntimeScope
from governance.external.runtime.external_runtime_sandbox import ExternalRuntimeSandbox


def test_sandbox_blocks_exec() -> None:
    sb = ExternalRuntimeSandbox()
    assert not sb.evaluate("exec(os.system('x'))").contained


def test_scope_rejects_global_apply() -> None:
    scope = DoctrineRuntimeScope()
    v = scope.check("Apply globally to all IDE sessions", declared_scope="advisory")
    assert not v.in_scope
