"""
Deep State Management - The Blackboard Pattern
Rich, structured state shared across all agents.
"""
from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """Agent roles in the system"""
    SUPERVISOR = "supervisor"
    INFORMATION_GATHERER = "information_gatherer"
    DRAFTSMAN = "draftsman"
    SAFETY_GUARDIAN = "safety_guardian"
    CLINICAL_CRITIC = "clinical_critic"
    DEBATE_MODERATOR = "debate_moderator"


class SafetyStatus(str, Enum):
    """Safety review status"""
    PENDING = "pending"
    PASSED = "passed"
    FLAGGED = "flagged"
    CRITICAL = "critical"


class ClinicalStatus(str, Enum):
    """Clinical review status"""
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"
    REJECTED = "rejected"


class AgentNote(TypedDict):
    """Notes left by agents for each other"""
    agent: AgentRole
    timestamp: str
    message: str
    context: Optional[Dict[str, Any]]


class DraftVersion(TypedDict):
    """Version tracking for drafts"""
    version: int
    content: str
    created_at: str
    created_by: AgentRole
    notes: List[AgentNote]


class SafetyReview(TypedDict):
    """Safety review results"""
    status: SafetyStatus
    flagged_lines: List[int]
    concerns: List[str]
    recommendations: List[str]
    reviewed_at: Optional[str]


class ClinicalReview(TypedDict):
    """Clinical review results"""
    status: ClinicalStatus
    empathy_score: float  # 0-10
    tone_score: float  # 0-10
    structure_score: float  # 0-10
    feedback: List[str]
    reviewed_at: Optional[str]


class FoundryState(TypedDict):
    """
    The Blackboard - Shared state across all agents
    
    This is the central state that all agents read from and write to.
    It tracks the entire workflow from initial request to final approval.
    """
    # User Input
    user_intent: str
    user_query: str
    user_specifics: Dict[str, Any]  # Collected user information
    information_gathered: bool  # Whether we've asked for user specifics
    questions_for_user: Optional[List[str]]  # Questions to ask user
    awaiting_user_response: bool  # Waiting for user to answer questions
    
    # Workflow Control
    iteration_count: int
    max_iterations: int
    is_approved: bool
    is_halted: bool  # Human-in-the-loop interruption
    current_agent: Optional[AgentRole]
    
    # Draft Management (Shared Document - Blackboard Pattern)
    current_draft: Optional[str]  # The shared document all agents edit
    draft_versions: List[DraftVersion]  # History of changes (for tracking)
    current_version: int
    draft_edits: List[Dict[str, Any]]  # Track edits made by each agent
    
    # Agent Communications (The Scratchpad)
    agent_notes: List[AgentNote]
    
    # Reviews
    safety_review: Optional[SafetyReview]
    clinical_review: Optional[ClinicalReview]
    
    # Debate & Argumentation
    agent_debate: List[Dict[str, Any]]  # Internal debate between agents
    debate_complete: bool  # Whether agents have finished debating
    
    # Learning & Adaptation
    learned_patterns: List[Dict[str, Any]]  # Patterns learned from user feedback
    adaptation_notes: List[str]  # Notes on how to adapt based on user input
    
    # Metadata
    started_at: str
    last_updated: str
    final_protocol: Optional[str]
    
    # Human-in-the-Loop
    human_feedback: Optional[str]
    human_edited_draft: Optional[str]
    awaiting_human_approval: bool
    
    # Routing
    next_action: Optional[str]  # Supervisor's routing decision

