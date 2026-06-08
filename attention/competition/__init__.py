"""attention.competition — fair allocation of finite attention across targets."""

from attention.competition.salience_competition import (
    CompetitionReport,
    SalienceCompetition,
    jain_fairness,
)

__all__ = ["SalienceCompetition", "CompetitionReport", "jain_fairness"]
