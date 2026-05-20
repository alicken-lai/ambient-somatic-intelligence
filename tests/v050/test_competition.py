"""Area 5: salience competition."""

from attention.competition.salience_competition import SalienceCompetition
from attention.core.attention_target import AttentionTarget


def test_competition_fairness_report() -> None:
    comp = SalienceCompetition()
    a = AttentionTarget("somatic", "a", 0.9)
    b = AttentionTarget("task", "b", 0.2)
    report = comp.compete_with_report([(a, 0.9), (b, 0.2)])
    assert len(report.winners) >= 1
    assert report.fairness_score >= 0.5
