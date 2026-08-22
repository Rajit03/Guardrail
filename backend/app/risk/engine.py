from dataclasses import dataclass
from typing import Optional, Dict, Any

from app.risk.severity import get_severity_score
from app.risk.factors import (
    Exploitability,
    Exposure,
    AssetCriticality,
    Confidence,
    get_exploitability_weight,
    get_exposure_weight,
    get_asset_criticality_weight,
    get_confidence_weight,
)
from app.risk.scoring import (
    calculate_raw_score,
    calculate_risk_score,
    determine_risk_level,
)
from app.risk.priority import determine_priority
from app.risk.explanations import generate_explanation, generate_remediation_guidance


@dataclass
class RiskEvaluationResult:
    raw_score: float
    risk_score: int
    risk_level: str
    priority: str
    severity_factor: float
    exploitability_factor: float
    exposure_factor: float
    asset_criticality_factor: float
    confidence_factor: float
    explanation: str
    recommended_action: str


class RiskEngine:
    """
    Guardrail Risk Engine.
    Transforms security findings into deterministic, prioritized, explainable risk assessments.
    Does NOT use AI, LLMs, or external network calls.
    """

    @staticmethod
    def evaluate(
        type: str,
        severity: str,
        title: str,
        description: Optional[str] = None,
        file_path: Optional[str] = None,
        scanner: Optional[str] = None,
        rule_id: Optional[str] = None,
        recommendation: Optional[str] = None,
        exploitability: str = "UNKNOWN",
        exposure: str = "UNKNOWN",
        asset_criticality: str = "UNKNOWN",
        confidence: str = "HIGH",
    ) -> RiskEvaluationResult:
        """
        Evaluates a finding and asset context, returning a deterministic RiskEvaluationResult.
        """
        # 1. Determine numeric severity score
        sev_score = get_severity_score(severity)

        # 2. Heuristics for default factor selection if set to UNKNOWN
        # Secrets and vulnerability advisories (GHSA/CVE) have higher default exploitability
        eff_exploitability = exploitability
        if eff_exploitability == "UNKNOWN":
            if type == "SECRET":
                eff_exploitability = "HIGH"
            elif type == "DEPENDENCY" and rule_id and rule_id.startswith(("GHSA", "CVE")):
                eff_exploitability = "HIGH"

        eff_confidence = confidence
        if scanner == "gitleaks":
            eff_confidence = "HIGH"
        elif scanner == "osv":
            eff_confidence = "HIGH"

        exp_weight = get_exposure_weight(exposure)
        expl_weight = get_exploitability_weight(eff_exploitability)
        crit_weight = get_asset_criticality_weight(asset_criticality)
        conf_weight = get_confidence_weight(eff_confidence)

        # 3. Calculate raw and normalized risk scores
        raw_score = calculate_raw_score(
            severity_score=sev_score,
            exploitability_factor=expl_weight,
            exposure_factor=exp_weight,
            asset_criticality_factor=crit_weight,
            confidence_factor=conf_weight,
        )

        risk_score = calculate_risk_score(raw_score)
        risk_level = determine_risk_level(risk_score)
        priority = determine_priority(
            severity=severity,
            exposure=exposure,
            asset_criticality=asset_criticality,
            risk_score=risk_score,
        )

        # 4. Generate deterministic explanation and remediation guidance
        explanation = generate_explanation(
            type_=type,
            severity=severity,
            title=title,
            risk_level=risk_level,
            priority=priority,
            exposure=exposure,
            asset_criticality=asset_criticality,
            file_path=file_path,
        )

        remediation = generate_remediation_guidance(
            type_=type,
            recommendation=recommendation,
        )

        return RiskEvaluationResult(
            raw_score=raw_score,
            risk_score=risk_score,
            risk_level=risk_level,
            priority=priority,
            severity_factor=sev_score,
            exploitability_factor=expl_weight,
            exposure_factor=exp_weight,
            asset_criticality_factor=crit_weight,
            confidence_factor=conf_weight,
            explanation=explanation,
            recommended_action=remediation,
        )
