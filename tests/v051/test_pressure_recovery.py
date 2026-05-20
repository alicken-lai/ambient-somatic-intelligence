"""Area 5: pressure controller, budget, overload recovery."""

from attention.runtime.attention_pressure_controller import AttentionPressureController
from attention.runtime.runtime_attention_budget import RuntimeAttentionBudget
from attention.runtime.overload_recovery import OverloadRecovery
from attention.kernel.attention_kernel import AttentionKernel


def test_pressure_evaluate(runtime_kernel: AttentionKernel) -> None:
    ctrl = AttentionPressureController(runtime_kernel)
    d = ctrl.evaluate()
    assert d.pressure.composite >= 0.0


def test_budget_consume(runtime_kernel: AttentionKernel) -> None:
    budget = RuntimeAttentionBudget(runtime_kernel)
    assert budget.try_allocate("somatic", 0.05) is True


def test_recovery_step(runtime_kernel: AttentionKernel) -> None:
    rec = OverloadRecovery(runtime_kernel)
    out = rec.step()
    assert "recovery" in out
