from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class JourneyTask:
    id: str
    title: str
    reason: str
    urgency: str  # "high", "medium", "low"
    effort: str   # e.g., "2 mins", "5 mins"
    status: str   # "pending", "done", "skipped"
    action_type: str  # "link", "callback", "workflow"
    action_payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class RiskAlert:
    id: str
    type: str  # "glucose", "meal", "medication", "general"
    title: str
    description: str
    severity: str  # "critical", "warning", "info"
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass
class CompletionStatus:
    category: str  # "Logging", "Medication", "Meals", "Risk"
    completed: int
    total: int
    percentage: float

@dataclass
class NextAction:
    label: str
    action_type: str
    payload: dict
    reason: Optional[str] = None

@dataclass
class JourneyState:
    patient_id: int
    tasks: List[JourneyTask] = field(default_factory=list)
    alerts: List[RiskAlert] = field(default_factory=list)
    completion: List[CompletionStatus] = field(default_factory=list)
    suggested_next_action: Optional[NextAction] = None
    last_updated: datetime = field(default_factory=datetime.now)
    greeting: str = "Good Morning"
    hero_message: str = "You have 0 urgent tasks today."
