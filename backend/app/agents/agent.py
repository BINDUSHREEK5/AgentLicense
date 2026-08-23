"""Agent decision engine for autonomous license selection."""

from typing import List, Tuple, Optional
from sqlalchemy.orm import Session

from app.models import LicenseOption, AgentRequirement, AgentDecision
from app.db.models import License, LicenseStatus


def evaluate_license_compatibility(
    license_option: LicenseOption,
    requirement: AgentRequirement,
) -> Tuple[bool, List[str]]:
    """
    Evaluate if a license meets agent requirements.
    
    Returns: (compatible, reasons_for_rejection)
    """
    
    rejection_reasons = []
    
    # Check usage limit
    if license_option.usage_limit < requirement.required_uses:
        rejection_reasons.append(
            f"Usage limit {license_option.usage_limit} < required {requirement.required_uses}"
        )
    
    # Check commercial use requirement
    if requirement.commercial_use_required and not license_option.commercial_use:
        rejection_reasons.append("Commercial use required but not permitted")
    
    # Check redistribution requirement
    if requirement.redistribution_required and not license_option.redistribution_allowed:
        rejection_reasons.append("Redistribution required but not allowed")
    
    # Check training requirement
    if requirement.training_required and not license_option.training_allowed:
        rejection_reasons.append("Training use required but not allowed")
    
    # Check budget
    if license_option.price > requirement.budget:
        rejection_reasons.append(
            f"Price {license_option.price} exceeds budget {requirement.budget}"
        )
    
    # Check expiry if duration is specified
    if requirement.duration_days and license_option.duration_days:
        if license_option.duration_days < requirement.duration_days:
            rejection_reasons.append(
                f"Duration {license_option.duration_days} < required {requirement.duration_days}"
            )
    
    is_compatible = len(rejection_reasons) == 0
    return is_compatible, rejection_reasons


def select_best_license(
    license_options: List[LicenseOption],
    requirement: AgentRequirement,
) -> Tuple[Optional[AgentDecision], List[dict]]:
    """
    Select the best license for agent requirements using deterministic rules.
    
    Strategy: Lowest cost that satisfies all requirements.
    Fallback: None if no compatible license exists.
    
    Returns: (decision, evaluation_log)
    """
    
    evaluation_log = []
    compatible_licenses = []
    
    # Evaluate each license
    for license_opt in license_options:
        is_compatible, rejection_reasons = evaluate_license_compatibility(
            license_opt, requirement
        )
        
        eval_entry = {
            "license_id": license_opt.license_id,
            "name": license_opt.name,
            "compatible": is_compatible,
            "price": license_opt.price,
            "usage_limit": license_opt.usage_limit,
            "commercial": license_opt.commercial_use,
        }
        
        if not is_compatible:
            eval_entry["rejection_reasons"] = rejection_reasons
            evaluation_log.append(eval_entry)
        else:
            eval_entry["status"] = "compatible"
            evaluation_log.append(eval_entry)
            compatible_licenses.append(license_opt)
    
    # If no compatible licenses, return None
    if not compatible_licenses:
        return None, evaluation_log
    
    # Sort by price (lowest first) to minimize cost
    best_license = min(compatible_licenses, key=lambda x: x.price)
    
    decision = AgentDecision(
        selected_license_id=best_license.license_id,
        reason=(
            f"Selected '{best_license.name}' for ${best_license.price} {best_license.currency}. "
            f"Provides {best_license.usage_limit} uses with required permissions. "
            f"Meets all requirements within budget of ${requirement.budget}."
        ),
        confidence=1.0,
    )
    
    return decision, evaluation_log


def explain_license_selection(
    license_options: List[LicenseOption],
    requirement: AgentRequirement,
) -> dict:
    """
    Provide detailed explanation of license selection process.
    
    Returns: Dictionary with decision and reasoning.
    """
    
    decision, evaluation_log = select_best_license(license_options, requirement)
    
    explanation = {
        "agent_requirement": requirement.model_dump(),
        "evaluation": evaluation_log,
        "decision": decision.model_dump() if decision else None,
        "compatible_count": sum(1 for e in evaluation_log if e.get("status") == "compatible"),
        "incompatible_count": sum(1 for e in evaluation_log if "rejection_reasons" in e),
    }
    
    return explanation


def get_fallback_decision(
    requirement: AgentRequirement,
    fallback_reason: str = "No compatible licenses found",
) -> dict:
    """Get fallback decision when automatic selection fails."""
    
    return {
        "selected_license_id": None,
        "reason": fallback_reason,
        "confidence": 0.0,
        "requires_manual_review": True,
    }