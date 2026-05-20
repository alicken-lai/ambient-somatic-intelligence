"""Test 5: continuity anchors reproducible."""

from governance.identity.continuity_anchor import ContinuityAnchor


def test_anchor_reproducible_id() -> None:
    a1 = ContinuityAnchor(session_id="s1", root_signature="abc12345")
    a2 = ContinuityAnchor(session_id="s1", root_signature="abc12345", created_at=a1.created_at)
    assert a1.anchor_id == a2.anchor_id


def test_chain_verify() -> None:
    anchor = ContinuityAnchor(session_id="s1", root_signature="deadbeef")
    assert anchor.verify_chain(["deadbeef", "deadbee0"]) is True
