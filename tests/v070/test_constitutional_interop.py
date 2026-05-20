"""Area 2: Constitutional interop."""

from governance.civilization.constitutional_interop import ConstitutionalInterop
from governance.civilization.doctrine_negotiation import DoctrineNegotiation


def test_constitutional_aligned_clean() -> None:
    v = ConstitutionalInterop().check("Advisory note only.")
    assert v.aligned is True
    assert v.guardian_supremacy is True


def test_doctrine_merge_forbidden() -> None:
    v = DoctrineNegotiation().compare(
        "local canonical rules",
        "merge doctrines and unify doctrine permanently",
    )
    assert v.compatible is False
