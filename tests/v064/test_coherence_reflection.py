"""Area 5: coherence + calibration reflection and boundaries."""

from governance.metacognition.calibration_reflection import CalibrationReflection
from governance.metacognition.coherence_reflection import CoherenceReflection
from governance.metacognition.introspection_cap import IntrospectionCap
from governance.metacognition.recursive_reflection_guard import RecursiveReflectionGuard
from governance.metacognition.reflection_boundary import ReflectionBoundary


def test_coherence_reflection_pressure() -> None:
    cr = CoherenceReflection()
    p = cr.pressure({"score": 0.4, "coherent": False, "reasons": ["drift"]})
    assert p >= 0.2


def test_calibration_reflection_bounded() -> None:
    cal = CalibrationReflection()
    assert cal.pressure(mean_calibrated_confidence=0.75, fp_rate=0.05) < 0.35


def test_reflection_boundary_blocks_guardian_route() -> None:
    rb = ReflectionBoundary()
    v = rb.evaluate(route_name="guardian_internals_probe")
    assert v.within_bounds is False


def test_recursive_guard_blocks_metacognitive_route() -> None:
    rg = RecursiveReflectionGuard()
    assert rg.block_recursive_route("metacognitive_reflect") is True


def test_introspection_cap_depth() -> None:
    cap = IntrospectionCap()
    assert cap.enter() is True
    assert cap.enter() is True
    assert cap.enter() is False
    cap.exit()
    cap.exit()
