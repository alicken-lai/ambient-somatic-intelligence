"""Area 4: IDE runtime boundary + export containment."""

from governance.external.runtime.export_containment import ExportContainment
from governance.external.runtime.ide_runtime_boundary import IdeRuntimeBoundary


def test_ide_boundary_blocks_always_apply() -> None:
    ide = IdeRuntimeBoundary()
    assert not ide.check("alwaysApply: true").boundary_intact


def test_export_containment_requires_markers() -> None:
    ex = ExportContainment()
    text = "advisory-only not sovereign does not override guardian hermes canonical rules prevail"
    assert ex.evaluate(text, is_export=True).contained
