"""
Skill Candidate Validator — Validate candidates before governance proposal.

Performs structural checks, quality scoring, and optional dry-run simulation
to ensure candidates meet minimum requirements before entering the
governance review pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from agents.skillify.skill_candidate_generator import SkillCandidate

logger = logging.getLogger(__name__)


@dataclass
class CandidateValidation:
    """Result of candidate validation."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    quality_score: float
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "quality_score": round(self.quality_score, 3),
            "recommendations": self.recommendations,
        }


@dataclass
class SimulationResult:
    """Result of a dry-run simulation against test inputs."""
    passed: int
    failed: int
    errors: list[str]
    coverage: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "coverage": round(self.coverage, 3),
        }


class SkillCandidateValidator:
    """
    Validate skill candidates for structural completeness, quality, and
    compatibility with existing registered skills.

    Usage:
        validator = SkillCandidateValidator()
        result = validator.validate(candidate)
        if not result.is_valid:
            print(result.errors)
    """

    def __init__(
        self,
        min_support: int = 3,
        min_success_rate: float = 0.7,
        name_similarity_threshold: float = 0.85,
    ):
        self._min_support = min_support
        self._min_success_rate = min_success_rate
        self._name_sim_threshold = name_similarity_threshold

    def validate(
        self,
        candidate: SkillCandidate,
        existing_skill_names: list[str] | None = None,
    ) -> CandidateValidation:
        """
        Validate a SkillCandidate against all checks.

        Checks:
          - Has name, version, description
          - Has at least one input and one output
          - Governance level is declared
          - Source patterns have sufficient support
          - Success rate above threshold
          - No duplicate of existing registered skill
        """
        errors: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        # Structural checks
        if not candidate.proposed_name:
            errors.append("Missing proposed_name")
        if not candidate.proposed_version:
            errors.append("Missing proposed_version")
        if not candidate.description:
            errors.append("Missing description")

        if not candidate.proposed_inputs:
            errors.append("Must have at least one proposed input")
        if not candidate.proposed_outputs:
            errors.append("Must have at least one proposed output")

        if not candidate.governance_level:
            errors.append("Governance level must be declared")

        # Evidence checks
        occurrence_count = candidate.evidence.get("occurrence_count", 0)
        success_rate = candidate.evidence.get("success_rate", 0.0)

        if occurrence_count < self._min_support:
            errors.append(
                f"Insufficient support: {occurrence_count} occurrences "
                f"(minimum {self._min_support})"
            )

        if success_rate < self._min_success_rate:
            errors.append(
                f"Success rate {success_rate:.1%} below threshold "
                f"{self._min_success_rate:.1%}"
            )

        # Duplicate detection
        if existing_skill_names:
            duplicate = self._check_duplicates(
                candidate.proposed_name, existing_skill_names
            )
            if duplicate:
                errors.append(
                    f"Potential duplicate of existing skill '{duplicate}'"
                )

        # Warnings
        if not candidate.source_patterns:
            warnings.append("No source patterns linked")

        if not candidate.observability_hooks:
            warnings.append("No observability hooks defined")

        if not candidate.routing_conditions:
            warnings.append("No routing conditions specified")

        if len(candidate.proposed_inputs) > 10:
            warnings.append("High input count — consider simplifying the interface")

        # Recommendations
        if success_rate < 0.9:
            recommendations.append(
                "Consider adding retry logic or fallback handling"
            )

        if not candidate.memory_updates:
            recommendations.append(
                "Add memory_updates to enable learning from executions"
            )

        skill_potential = candidate.evidence.get("skill_potential", 0.0)
        if skill_potential < 0.5:
            recommendations.append(
                f"Low skill potential ({skill_potential:.2f}) — "
                "may need more observations before proposing"
            )

        # Quality score
        quality_score = self._compute_quality(candidate, errors, warnings)

        is_valid = len(errors) == 0

        logger.info(
            "Validated candidate '%s': valid=%s, quality=%.3f, errors=%d, warnings=%d",
            candidate.proposed_name, is_valid, quality_score,
            len(errors), len(warnings),
        )

        return CandidateValidation(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
            recommendations=recommendations,
        )

    def simulate(
        self,
        candidate: SkillCandidate,
        test_inputs: list[dict[str, Any]],
    ) -> SimulationResult:
        """
        Dry-run the candidate against test inputs.

        Verifies that each test input contains required fields as declared
        in the candidate's proposed_inputs schema.
        """
        if not test_inputs:
            return SimulationResult(
                passed=0, failed=0, errors=["No test inputs provided"], coverage=0.0,
            )

        required_fields = {
            inp["name"] for inp in candidate.proposed_inputs if inp.get("required")
        }
        all_fields = {inp["name"] for inp in candidate.proposed_inputs}

        passed = 0
        failed = 0
        errors: list[str] = []
        fields_covered: set[str] = set()

        for i, test_input in enumerate(test_inputs):
            input_keys = set(test_input.keys())
            fields_covered.update(input_keys & all_fields)

            missing = required_fields - input_keys
            if missing:
                failed += 1
                errors.append(
                    f"Test input {i}: missing required fields {sorted(missing)}"
                )
            else:
                passed += 1

        coverage = len(fields_covered) / max(len(all_fields), 1)

        return SimulationResult(
            passed=passed,
            failed=failed,
            errors=errors,
            coverage=round(coverage, 3),
        )

    def _check_duplicates(
        self,
        name: str,
        existing_names: list[str],
    ) -> str | None:
        """Check if the candidate name is too similar to an existing skill."""
        for existing in existing_names:
            ratio = SequenceMatcher(None, name.lower(), existing.lower()).ratio()
            if ratio >= self._name_sim_threshold:
                return existing
        return None

    def _compute_quality(
        self,
        candidate: SkillCandidate,
        errors: list[str],
        warnings: list[str],
    ) -> float:
        """Compute a 0.0-1.0 quality score."""
        if errors:
            return 0.0

        score = 0.5

        success_rate = candidate.evidence.get("success_rate", 0.0)
        score += 0.15 * success_rate

        if candidate.observability_hooks:
            score += 0.05
        if candidate.memory_updates:
            score += 0.05
        if candidate.routing_conditions:
            score += 0.05

        skill_potential = candidate.evidence.get("skill_potential", 0.0)
        score += 0.1 * skill_potential

        occurrence = candidate.evidence.get("occurrence_count", 0)
        score += 0.1 * min(occurrence / 20.0, 1.0)

        score -= 0.02 * len(warnings)

        return round(max(0.0, min(1.0, score)), 3)
