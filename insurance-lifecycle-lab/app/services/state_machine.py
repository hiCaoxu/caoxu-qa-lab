from ..errors import AppError

TRANSITIONS = {
    "APPLICATION": {
        "DRAFT": {"SUBMITTED", "CANCELLED"},
        "SUBMITTED": {"UNDERWRITING"},
        "UNDERWRITING": {"APPROVED", "REJECTED"},
        "APPROVED": {"PAYING", "CANCELLED"},
        "REJECTED": set(),
        "PAYING": {"POLICY_ISSUED", "APPROVED"},
        "POLICY_ISSUED": set(),
        "CANCELLED": set(),
    },
    "PAYMENT": {
        "INIT": {"SUCCESS", "FAILED"},
        "FAILED": {"SUCCESS", "INIT"},
        "SUCCESS": set(),
    },
    "POLICY": {
        "ACTIVE": {"SURRENDER_PENDING"},
        "SURRENDER_PENDING": {"ACTIVE", "SURRENDERED"},
        "SURRENDERED": set(),
    },
    "CLAIM": {
        "SUBMITTED": {"REVIEWING"},
        "REVIEWING": {"APPROVED", "REJECTED"},
        "APPROVED": {"PAID"},
        "REJECTED": set(),
        "PAID": set(),
    },
    "ENDORSEMENT": {
        "PENDING": {"APPROVED", "REJECTED"},
        "APPROVED": set(),
        "REJECTED": set(),
    },
    "SURRENDER": {
        "PENDING": {"APPROVED", "REJECTED"},
        "APPROVED": set(),
        "REJECTED": set(),
    },
}


def ensure_transition(entity: str, current: str, target: str) -> None:
    allowed = TRANSITIONS.get(entity, {}).get(current, set())
    if target not in allowed:
        raise AppError(
            409,
            "INVALID_STATE_TRANSITION",
            f"Cannot change {entity} from {current} to {target}",
            {"current": current, "target": target},
        )
