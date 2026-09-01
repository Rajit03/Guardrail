"""
Phase 4 Risk Engine — Security Score Boundary Tests
=====================================================

Tests calculate_security_score() logarithmic aggregation formula in scoring.py.

New formula (replacing linear penalty sum):
    weighted_sum = Σ( severity_weight × risk_score / 100 )
    penalty      = 100 × (1 − exp(−weighted_sum / 10.0))
    score        = round(100 − penalty)   [clamped 0–100]

Severity weights: CRITICAL=4.0, HIGH=2.0, MEDIUM=1.0, LOW=0.3, INFO=0.0

Key verified values (SCALE=10):
    0 findings               → 100
    1 LOW  (risk=23)         →  99
    1 MED  (risk=45)         →  96
    1 HIGH (risk=68)         →  87  ← same as old linear formula
    1 CRIT (risk=90)         →  70  ← same as old linear formula
    5 HIGH (risk=68)         →  51
    8 HIGH (risk=68)         →  34  (was 0 in old formula — FIXED)
   25 HIGH (risk=68)         →   3  (was 0 in old formula — FIXED)
  ~50 HIGH (risk=68)         →   0  (only at truly extreme counts)
"""

import math
import pytest

from app.risk.scoring import (
    calculate_security_score,
    determine_security_rating,
    determine_risk_level,
    _SCORE_SEVERITY_WEIGHTS,
    _SCORE_SCALE,
)
from app.risk.engine import RiskEngine


# ---------------------------------------------------------------------------
# Helper: compute expected score from the new formula
# ---------------------------------------------------------------------------

def _expected_score(findings: list) -> int:
    """
    Reference implementation of the logarithmic formula for use in assertions.
    Mirrors calculate_security_score() exactly; used to compute expected values
    without duplicating magic numbers in each test.
    """
    if not findings:
        return 100
    weighted_sum = sum(
        _SCORE_SEVERITY_WEIGHTS.get((sev or "MEDIUM").upper(), 0.0) * (r / 100.0)
        for sev, r in findings
    )
    penalty = 100.0 * (1.0 - math.exp(-weighted_sum / _SCORE_SCALE))
    return max(0, min(100, round(100.0 - penalty)))


# ---------------------------------------------------------------------------
# 1. Empty / Zero-Finding Baseline
# ---------------------------------------------------------------------------

class TestEmptyFindings:
    def test_no_findings_returns_100(self):
        """0 findings → perfect score of 100."""
        assert calculate_security_score([]) == 100

    def test_none_treated_as_no_findings(self):
        """
        Passing None is technically invalid, but the guard `if not finding_assessments`
        treats None as falsy and returns 100 (same as an empty list).
        Callers should always pass an explicit [].
        """
        score = calculate_security_score(None)  # type: ignore[arg-type]
        assert score == 100


# ---------------------------------------------------------------------------
# 2. Single Finding Scores
# ---------------------------------------------------------------------------

class TestSingleFinding:
    def test_single_low_finding_score_stays_above_zero(self):
        """1 LOW finding → score stays above 0."""
        score = calculate_security_score([("LOW", 23)])
        assert score > 0

    def test_single_low_finding_score_is_excellent(self):
        """1 LOW finding (risk=23) → Excellent range (≥90)."""
        score = calculate_security_score([("LOW", 23)])
        assert score == _expected_score([("LOW", 23)])  # 99
        assert score >= 90

    def test_single_medium_finding_score_stays_above_zero(self):
        """1 MEDIUM finding → score stays above 0."""
        score = calculate_security_score([("MEDIUM", 45)])
        assert score > 0

    def test_single_medium_finding_score_is_excellent(self):
        """1 MEDIUM finding (risk=45) → Excellent range (≥90)."""
        score = calculate_security_score([("MEDIUM", 45)])
        assert score == _expected_score([("MEDIUM", 45)])  # 96
        assert score >= 90

    def test_single_high_finding_score_stays_above_zero(self):
        """1 HIGH finding → score stays above 0."""
        score = calculate_security_score([("HIGH", 68)])
        assert score > 0

    def test_single_high_finding_decreases_score(self):
        """1 HIGH finding (risk=68) → score=87, lower than 100 but not 0."""
        score = calculate_security_score([("HIGH", 68)])
        assert score == 87  # 100 − 100*(1−exp(−1.36/10)) = 87.28 → 87
        assert score < 100
        assert score > 0

    def test_single_critical_finding_score_stays_above_zero(self):
        """1 CRITICAL finding → score stays above 0."""
        score = calculate_security_score([("CRITICAL", 98)])
        assert score > 0

    def test_single_critical_finding_decreases_score_significantly(self):
        """1 CRITICAL finding (risk=98) → significant decrease, score < 80."""
        score = calculate_security_score([("CRITICAL", 98)])
        assert score == _expected_score([("CRITICAL", 98)])
        assert score < 80

    def test_single_info_finding_does_not_penalize(self):
        """1 INFO finding (weight=0) → no contribution, score stays 100."""
        score = calculate_security_score([("INFO", 0)])
        assert score == 100

    def test_single_unknown_severity_does_not_penalize(self):
        """Unknown severity string gets weight=0.0 → no penalty, score=100."""
        score = calculate_security_score([("BOGUS", 50)])
        assert score == 100


# ---------------------------------------------------------------------------
# 3. Progressive Degradation
# ---------------------------------------------------------------------------

class TestProgressiveDegradation:
    def test_more_high_findings_lower_the_score(self):
        """Adding more HIGH findings must progressively decrease the score."""
        scores = [
            calculate_security_score([("HIGH", 68)] * n)
            for n in range(1, 12)
        ]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Score must be non-increasing: n={i+1} gave {scores[i]}, "
                f"n={i+2} gave {scores[i+1]}"
            )

    def test_more_critical_findings_lower_the_score(self):
        """Adding more CRITICAL findings must progressively decrease the score."""
        scores = [
            calculate_security_score([("CRITICAL", 90)] * n)
            for n in range(1, 8)
        ]
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], (
                f"Score non-increasing failed: {scores[i]} >= {scores[i+1]}"
            )

    def test_severity_ordering_single_finding(self):
        """
        For a single finding with the same risk_score, higher severity
        produces a lower or equal security score.
        score(CRITICAL) ≤ score(HIGH) ≤ score(MEDIUM) ≤ score(LOW) ≤ score(INFO).
        """
        r = 50
        score_crit = calculate_security_score([("CRITICAL", r)])
        score_high = calculate_security_score([("HIGH", r)])
        score_med  = calculate_security_score([("MEDIUM", r)])
        score_low  = calculate_security_score([("LOW", r)])
        score_info = calculate_security_score([("INFO", 0)])

        assert score_crit <= score_high, "CRITICAL must score ≤ HIGH"
        assert score_high <= score_med,  "HIGH must score ≤ MEDIUM"
        assert score_med  <= score_low,  "MEDIUM must score ≤ LOW"
        assert score_low  <= score_info, "LOW must score ≤ INFO"

    def test_mixed_severities_lower_than_equivalent_low_only(self):
        """Mixed CRIT+HIGH+MED+LOW penalties more than 4×LOW."""
        mixed    = [("CRITICAL", 90), ("HIGH", 68), ("MEDIUM", 45), ("LOW", 23)]
        low_only = [("LOW", 23)] * 4
        assert calculate_security_score(mixed) < calculate_security_score(low_only)


# ---------------------------------------------------------------------------
# 4. Hard Boundaries: Score Always in [0, 100]
# ---------------------------------------------------------------------------

class TestScoreBounds:
    def test_score_never_below_zero(self):
        """100 HIGH findings at max risk_score must clamp to 0, not negative."""
        score = calculate_security_score([("HIGH", 100)] * 100)
        assert score >= 0

    def test_score_never_above_100(self):
        """0 findings → 100, which is the maximum."""
        score = calculate_security_score([])
        assert score <= 100

    def test_score_never_below_zero_critical_extreme(self):
        """100 CRITICAL findings at max risk_score → clamped to 0."""
        score = calculate_security_score([("CRITICAL", 100)] * 100)
        assert score == 0

    def test_score_never_below_zero_large_count(self):
        """1000 HIGH findings → still clamped to 0, not negative."""
        score = calculate_security_score([("HIGH", 68)] * 1000)
        assert score == 0

    def test_score_maximum_is_100_for_no_findings(self):
        """Maximum possible score is 100."""
        assert calculate_security_score([]) == 100

    @pytest.mark.parametrize("count", [1, 5, 10, 25, 50, 100, 500])
    def test_score_always_in_range_for_various_counts(self, count):
        """Score is always [0, 100] for any count of HIGH findings."""
        score = calculate_security_score([("HIGH", 68)] * count)
        assert 0 <= score <= 100, f"Score out of range for count={count}: {score}"


# ---------------------------------------------------------------------------
# 5. Logarithmic Formula: No Collapse at Low Finding Counts (the fix)
# ---------------------------------------------------------------------------

class TestScoringImprovement:
    """
    These tests document the key improvement over the old linear formula:
    the score no longer collapses to 0 at only 8 HIGH findings.

    Old (linear) behaviour:
        8 HIGH findings  → score = 0   (collapsed)
        25 HIGH findings → score = 0   (indistinguishable)

    New (logarithmic) behaviour:
        8 HIGH findings  → score = 34  (High Risk — still bad, but not zero)
        25 HIGH findings → score =  3  (Critical Risk — appropriately severe)
        Score approaches 0 only at extreme counts (≥50 HIGH findings).
    """

    def test_8_high_findings_is_NOT_zero(self):
        """
        FIX VERIFIED: 8 HIGH findings no longer collapse to 0.
        Old formula: penalty=107.52 → clamped to 0.
        New formula: score=34 (High Risk).
        """
        score = calculate_security_score([("HIGH", 68)] * 8)
        assert score > 0, (
            f"8 HIGH findings must not produce 0 anymore. Got {score}."
        )
        assert score == 34

    def test_25_high_findings_is_NOT_zero(self):
        """
        FIX VERIFIED: 25 HIGH findings no longer collapse to 0.
        Old formula: penalty=336 → clamped to 0.
        New formula: score=3 (Critical Risk, but distinguishable).
        """
        score = calculate_security_score([("HIGH", 68)] * 25)
        assert score > 0, (
            f"25 HIGH findings must not produce 0 anymore. Got {score}."
        )
        assert score == 3

    def test_score_is_discriminating_across_finding_counts(self):
        """
        Key property: different finding counts produce different scores,
        allowing meaningful comparison between repositories.
        """
        score_1  = calculate_security_score([("HIGH", 68)] * 1)
        score_5  = calculate_security_score([("HIGH", 68)] * 5)
        score_8  = calculate_security_score([("HIGH", 68)] * 8)
        score_25 = calculate_security_score([("HIGH", 68)] * 25)

        assert score_1 > score_5 > score_8 > score_25, (
            f"Scores must be strictly decreasing: "
            f"1→{score_1}, 5→{score_5}, 8→{score_8}, 25→{score_25}"
        )

    def test_score_only_reaches_zero_at_extreme_counts(self):
        """Score approaches 0 only at extreme counts, not at realistic counts."""
        # Realistic counts (common in real repos) must all be > 0
        for n in [1, 5, 8, 10, 15, 20, 25, 30]:
            s = calculate_security_score([("HIGH", 68)] * n)
            assert s > 0, f"n={n} HIGH findings must not be 0 (got {s})"

    def test_expected_collapse_point_is_around_50(self):
        """Score reaches 0 around 50 HIGH findings, not at 8."""
        score_45 = calculate_security_score([("HIGH", 68)] * 45)
        score_55 = calculate_security_score([("HIGH", 68)] * 55)
        # By ~50 the score is 0 or very close; confirm 8 isn't collapsed
        score_8  = calculate_security_score([("HIGH", 68)] * 8)
        assert score_8 > 0, f"8 HIGH must not be 0, got {score_8}"
        assert score_55 == 0, f"55 HIGH must be 0, got {score_55}"


# ---------------------------------------------------------------------------
# 6. Input Format Flexibility
# ---------------------------------------------------------------------------

class TestInputFormats:
    """
    calculate_security_score() accepts three formats:
    - (severity, risk_score) tuples   ← used by dashboard_service
    - dicts with "severity" / "risk_score" keys
    - objects with .severity and .risk_score attributes
    """

    def test_tuple_input(self):
        """Tuple format (severity, risk_score) works correctly."""
        score = calculate_security_score([("HIGH", 68)])
        assert score == 87

    def test_dict_input(self):
        """Dict format {'severity': ..., 'risk_score': ...} works correctly."""
        score = calculate_security_score([{"severity": "HIGH", "risk_score": 68}])
        assert score == 87

    def test_dict_default_severity(self):
        """Dict missing 'severity' key defaults to MEDIUM."""
        score_no_sev = calculate_security_score([{"risk_score": 45}])
        score_medium = calculate_security_score([("MEDIUM", 45)])
        assert score_no_sev == score_medium

    def test_dict_default_risk_score(self):
        """Dict missing 'risk_score' key defaults to 45."""
        score_no_rs   = calculate_security_score([{"severity": "HIGH"}])
        score_explicit = calculate_security_score([("HIGH", 45)])
        assert score_no_rs == score_explicit

    def test_object_input(self):
        """Object with .severity and .risk_score attributes works correctly."""
        class FakeAssessment:
            severity = "HIGH"
            risk_score = 68

        score = calculate_security_score([FakeAssessment()])
        assert score == 87

    def test_mixed_input_formats(self):
        """Mixed formats in the same call produce consistent results."""
        class FakeAssessment:
            severity = "MEDIUM"
            risk_score = 45

        items = [
            ("HIGH", 68),
            {"severity": "CRITICAL", "risk_score": 90},
            FakeAssessment(),
        ]
        score = calculate_security_score(items)
        assert 0 <= score <= 100

    def test_tuple_and_dict_produce_same_result(self):
        """Tuple and dict formats for the same data produce identical scores."""
        as_tuples = [("HIGH", 68), ("CRITICAL", 90), ("MEDIUM", 45)]
        as_dicts  = [
            {"severity": "HIGH",     "risk_score": 68},
            {"severity": "CRITICAL", "risk_score": 90},
            {"severity": "MEDIUM",   "risk_score": 45},
        ]
        assert calculate_security_score(as_tuples) == calculate_security_score(as_dicts)


# ---------------------------------------------------------------------------
# 7. Security Rating Thresholds
# ---------------------------------------------------------------------------

class TestSecurityRatingThresholds:
    """
    Verify determine_security_rating() maps scores to correct labels.
    Thresholds (unchanged by this fix):
        90–100 → Excellent     (LOW risk)
         75–89 → Good          (LOW risk)
         50–74 → Needs Attention (MEDIUM risk)
         25–49 → High Risk     (HIGH risk)
          0–24 → Critical Risk (CRITICAL risk)
    """

    @pytest.mark.parametrize("score,expected_rating,expected_level", [
        (100, "Excellent",        "LOW"),
        (90,  "Excellent",        "LOW"),
        (89,  "Good",             "LOW"),
        (75,  "Good",             "LOW"),
        (74,  "Needs Attention",  "MEDIUM"),
        (50,  "Needs Attention",  "MEDIUM"),
        (49,  "High Risk",        "HIGH"),
        (25,  "High Risk",        "HIGH"),
        (24,  "Critical Risk",    "CRITICAL"),
        (1,   "Critical Risk",    "CRITICAL"),
        (0,   "Critical Risk",    "CRITICAL"),
    ])
    def test_threshold_boundaries(self, score, expected_rating, expected_level):
        from app.risk.scoring import determine_security_rating
        result = determine_security_rating(score)
        assert result["rating"] == expected_rating, (
            f"score={score}: expected '{expected_rating}', got '{result['rating']}'"
        )
        assert result["risk_level"] == expected_level, (
            f"score={score}: expected level '{expected_level}', got '{result['risk_level']}'"
        )

    def test_zero_score_maps_to_critical_risk(self):
        from app.risk.scoring import determine_security_rating
        result = determine_security_rating(0)
        assert result["rating"] == "Critical Risk"
        assert result["risk_level"] == "CRITICAL"

    def test_score_clamped_above_100(self):
        from app.risk.scoring import determine_security_rating
        result = determine_security_rating(200)
        assert result["rating"] == "Excellent"

    def test_score_clamped_below_zero(self):
        from app.risk.scoring import determine_security_rating
        result = determine_security_rating(-50)
        assert result["rating"] == "Critical Risk"

    def test_25_high_findings_maps_to_critical_risk(self):
        """25 HIGH findings → score=3 → Critical Risk (score is low but not 0)."""
        from app.risk.scoring import determine_security_rating
        score = calculate_security_score([("HIGH", 68)] * 25)
        result = determine_security_rating(score)
        assert score > 0,          f"Score must be >0 (was {score}), formula is now logarithmic"
        assert score < 25,         f"Score must be in Critical Risk range, got {score}"
        assert result["rating"] == "Critical Risk"
        assert result["risk_level"] == "CRITICAL"


# ---------------------------------------------------------------------------
# 8. Logarithmic Formula Arithmetic (White-Box)
# ---------------------------------------------------------------------------

class TestWeightedLogarithmicArithmetic:
    """
    Verify the exact weighted-logarithmic computation for key inputs.
    Pins the formula constants: weights and scale factor.
    Any change to _SCORE_SEVERITY_WEIGHTS or _SCORE_SCALE will break these.
    """

    def test_weights_are_correct(self):
        """Verify published severity weights."""
        assert _SCORE_SEVERITY_WEIGHTS["CRITICAL"] == 4.0
        assert _SCORE_SEVERITY_WEIGHTS["HIGH"]     == 2.0
        assert _SCORE_SEVERITY_WEIGHTS["MEDIUM"]   == 1.0
        assert _SCORE_SEVERITY_WEIGHTS["LOW"]      == 0.3
        assert _SCORE_SEVERITY_WEIGHTS["INFO"]     == 0.0

    def test_scale_is_correct(self):
        """Verify published scale factor."""
        assert _SCORE_SCALE == 10.0

    @pytest.mark.parametrize("sev,r,expected_score", [
        # CRITICAL: weight=4.0, ws=4.0*(r/100), penalty=100*(1−exp(−ws/10))
        ("CRITICAL", 0,   100),  # ws=0 → penalty=0 → 100
        ("CRITICAL", 90,   70),  # ws=3.6 → penalty≈30.2 → 70
        ("CRITICAL", 100,  67),  # ws=4.0 → penalty≈33.0 → 67
        # HIGH: weight=2.0
        ("HIGH",     0,   100),  # ws=0 → 100
        ("HIGH",     68,   87),  # ws=1.36 → penalty≈12.7 → 87
        ("HIGH",     100,  82),  # ws=2.0 → penalty≈18.1 → 82
        # MEDIUM: weight=1.0
        ("MEDIUM",   0,   100),
        ("MEDIUM",   45,   96),  # ws=0.45 → penalty≈4.4 → 96
        ("MEDIUM",   100,  90),  # ws=1.0 → penalty≈9.5 → 90 (rounds from 90.5)
        # LOW: weight=0.3
        ("LOW",      0,   100),
        ("LOW",      23,   99),  # ws=0.069 → penalty≈0.69 → 99
        ("LOW",      100,  97),  # ws=0.3 → penalty≈2.96 → 97
        # INFO: weight=0.0 → no contribution
        ("INFO",     0,   100),
        ("INFO",     100, 100),
    ])
    def test_single_finding_exact_score(self, sev, r, expected_score):
        """Verify exact score for each severity at key risk_score values."""
        actual = calculate_security_score([(sev, r)])
        assert actual == expected_score, (
            f"{sev} r={r}: expected={expected_score}, got={actual}"
        )

    def test_additive_weighted_sum(self):
        """
        weighted_sum accumulates correctly across multiple findings.
        Two HIGH(r=68) = one finding with ws=2×1.36=2.72 equivalent.
        """
        two_high = calculate_security_score([("HIGH", 68), ("HIGH", 68)])
        expected = _expected_score([("HIGH", 68), ("HIGH", 68)])
        assert two_high == expected

    def test_formula_is_not_linear(self):
        """
        Key property: the formula is sublinear — each additional finding
        contributes a smaller marginal penalty than the previous one.

        This is tested over a range large enough that integer rounding does
        not obscure the logarithmic curve.
        """
        # Compare the penalty contributed by findings 1-5 vs findings 21-25.
        # Going from 0→5 findings should reduce the score more than 20→25.
        score_0   = calculate_security_score([("HIGH", 68)] * 0)
        score_5   = calculate_security_score([("HIGH", 68)] * 5)
        score_20  = calculate_security_score([("HIGH", 68)] * 20)
        score_25  = calculate_security_score([("HIGH", 68)] * 25)

        delta_first_5 = score_0 - score_5    # penalty from findings 1-5
        delta_last_5  = score_20 - score_25  # penalty from findings 21-25

        assert delta_last_5 < delta_first_5, (
            f"Diminishing returns: first 5 findings penalize Δ={delta_first_5}, "
            f"findings 21-25 penalize Δ={delta_last_5}. "
            f"Last-5 must be strictly less than first-5."
        )


# ---------------------------------------------------------------------------
# 9. RiskEngine Integration: Per-Finding → Aggregate
# ---------------------------------------------------------------------------

class TestRiskEngineIntegration:
    """
    End-to-end: RiskEngine.evaluate() → individual risk_score →
    calculate_security_score() aggregate.
    """

    def test_osv_high_finding_individual_score(self):
        """
        OSV HIGH dependency finding (GHSA rule, scanner=osv):
        - exploitability bumped to HIGH (1.05) because rule_id starts with GHSA
        - confidence bumped to HIGH (1.15) because scanner=osv
        - context_multiplier = (1.05+1.00+1.00+1.15)/4 = 1.05
        - raw_score = 65.0 × 1.05 = 68.25 → risk_score = 68
        Individual RiskEngine scores are unchanged by this fix.
        """
        res = RiskEngine.evaluate(
            type="DEPENDENCY",
            severity="HIGH",
            title="Test GHSA Vulnerability",
            scanner="osv",
            rule_id="GHSA-xxxx-xxxx-xxxx",
            exposure="UNKNOWN",
            asset_criticality="UNKNOWN",
        )
        assert res.risk_score == 68
        assert res.raw_score == pytest.approx(68.25, abs=0.01)
        assert res.risk_level == "HIGH"
        assert res.priority == "P1"

    def test_gitleaks_critical_secret_individual_score(self):
        """
        Gitleaks CRITICAL secret: risk_score=89 (unchanged by this fix).
        """
        res = RiskEngine.evaluate(
            type="SECRET",
            severity="CRITICAL",
            title="AWS Access Key",
            scanner="gitleaks",
            exposure="UNKNOWN",
            asset_criticality="UNKNOWN",
        )
        assert res.risk_score == 89
        assert res.raw_score == pytest.approx(89.25, abs=0.01)
        assert res.risk_level == "CRITICAL"
        assert res.priority in ("P0", "P1")

    def test_single_osv_high_finding_aggregate_unchanged(self):
        """
        1 OSV HIGH finding → score=87.
        The new logarithmic formula preserves single-finding scores from
        the old linear formula (both give 87 for HIGH risk_score=68).
        """
        score = calculate_security_score([("HIGH", 68)])
        assert score == 87

    def test_single_osv_critical_finding_aggregate_unchanged(self):
        """
        1 CRITICAL finding (risk_score=90) → score=70.
        Preserved from the old formula.
        """
        score = calculate_security_score([("CRITICAL", 90)])
        assert score == 70

    def test_8_osv_high_findings_no_longer_collapse(self):
        """
        FIX VERIFIED end-to-end:
        8 OSV HIGH findings (risk_score=68 each) → score=34, NOT 0.

        The old linear formula produced total_penalty=107.52 → 0.
        The new logarithmic formula produces score=34 (High Risk).
        """
        score = calculate_security_score([("HIGH", 68)] * 8)
        assert score == 34
        assert score > 0

    def test_25_osv_high_findings_produce_low_but_nonzero_score(self):
        """
        25 OSV HIGH findings (risk_score=68 each) → score=3, NOT 0.
        The repository is genuinely in Critical Risk territory,
        but the score retains information (3 ≠ 0).
        """
        res = RiskEngine.evaluate(
            type="DEPENDENCY",
            severity="HIGH",
            title="Test GHSA Vulnerability",
            scanner="osv",
            rule_id="GHSA-xxxx-xxxx-xxxx",
            exposure="UNKNOWN",
            asset_criticality="UNKNOWN",
        )
        assert res.risk_score == 68  # engine score unchanged

        score = calculate_security_score([("HIGH", res.risk_score)] * 25)
        assert score == 3
        assert score > 0, (
            "25 HIGH findings must no longer produce 0. "
            "The logarithmic formula prevents early collapse."
        )

    def test_aggregate_deterministic_for_same_inputs(self):
        """calculate_security_score() is deterministic: same inputs → same output."""
        findings = [("HIGH", 68)] * 10 + [("CRITICAL", 90)] * 3 + [("MEDIUM", 45)] * 5
        results = [calculate_security_score(findings) for _ in range(50)]
        assert len(set(results)) == 1, f"Non-deterministic results: {set(results)}"
