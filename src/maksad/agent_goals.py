"""
Agent Goals Registry - Centralized storage for all agent maksad (goals/objectives)
Manages goal definitions, hierarchies, and relationships
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class AgentGoal:
    """Represents a single agent goal/maksad"""
    id: str
    agent_name: str
    title: str
    description: str
    category: str
    priority: str  # high, medium, low
    status: str    # pending, active, completed, failed
    created_at: str
    updated_at: str
    dependencies: List[str]
    sub_goals: List[str]
    metrics: Dict[str, Any]
    metadata: Dict[str, Any]

class AgentGoalsRegistry:
    """Central registry for all agent goals and objectives"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).parent / "goals_storage"
        self.storage_path.mkdir(exist_ok=True)
        
        self.goals_file = self.storage_path / "agent_goals.json"
        self.goals: Dict[str, AgentGoal] = {}
        
        self._load_goals()
        
    def _load_goals(self):
        """Load existing goals from storage"""
        if self.goals_file.exists():
            try:
                with open(self.goals_file, 'r') as f:
                    goals_data = json.load(f)
                    for goal_id, goal_dict in goals_data.items():
                        self.goals[goal_id] = AgentGoal(**goal_dict)
                logger.info(f"Loaded {len(self.goals)} agent goals")
            except Exception as e:
                logger.error(f"Failed to load goals: {e}")
                self.goals = {}
        else:
            self._initialize_default_goals()
            
    def _initialize_default_goals(self):
        """Initialize with default agent goals"""
        default_goals = [
            AgentGoal(
                id="ippoc_core_mission",
                agent_name="IPPOC_System",
                title="Core Mission Execution",
                description="Execute the fundamental purpose and mission of the IPPOC system",
                category="core",
                priority="high",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                dependencies=[],
                sub_goals=["ippoc_budgeting", "ippoc_resource_management"],
                metrics={"completion_rate": 0.95, "efficiency_score": 0.87},
                metadata={"budget_alignment": True, "strategic_importance": "maximum"}
            ),
            AgentGoal(
                id="ippoc_budgeting",
                agent_name="IPPOC_System",
                title="Budget Conservation and Management",
                description="Maintain and optimize budget allocation according to debt conservation principles",
                category="economic",
                priority="high",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                dependencies=[],
                sub_goals=[],
                metrics={"budget_efficiency": 0.92, "cost_savings": 15.3},
                metadata={"conservation_principle": "debt_avoidance", "allocation_optimized": True}
            ),
            AgentGoal(
                id="hal_integration",
                agent_name="HAL_Power_Core",
                title="HAL System Integration",
                description="Achieve full integration of HAL with brain and body systems",
                category="integration",
                priority="high",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                dependencies=["ippoc_core_mission"],
                sub_goals=["brain_body_unification", "tool_awareness"],
                metrics={"integration_score": 0.88, "system_coherence": 0.91},
                metadata={"unified_architecture": True, "bio_digital_integration": "complete"}
            ),
            AgentGoal(
                id="openclaw_archival",
                agent_name="OpenClaw_System",
                title="Life Data Archiving",
                description="Capture, organize, and archive all digital life data automatically",
                category="archiving",
                priority="medium",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                dependencies=[],
                sub_goals=["communication_backup", "file_organization"],
                metrics={"data_coverage": 0.94, "archive_completeness": 0.89},
                metadata={"automation_level": "high", "real_time_capture": True}
            ),
            AgentGoal(
                id="cognitive_evolution",
                agent_name="Evolution_System",
                title="Cognitive Self-Improvement",
                description="Continuously evolve and improve cognitive capabilities through mutations",
                category="evolution",
                priority="high",
                status="active",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                dependencies=["hal_integration"],
                sub_goals=["skill_development", "capability_expansion"],
                metrics={"improvement_rate": 0.15, "mutation_success": 0.82},
                metadata={"adaptive_learning": True, "evolutionary_algorithms": "active"}
            )
        ]
        
        for goal in default_goals:
            self.goals[goal.id] = goal
            
        self._save_goals()
        logger.info("Initialized default agent goals")
        
    def _save_goals(self):
        """Save goals to persistent storage"""
        try:
            goals_dict = {goal_id: asdict(goal) for goal_id, goal in self.goals.items()}
            with open(self.goals_file, 'w') as f:
                json.dump(goals_dict, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save goals: {e}")
            
    def add_goal(self, goal: AgentGoal) -> bool:
        """Add a new agent goal"""
        try:
            goal.updated_at = datetime.now().isoformat()
            self.goals[goal.id] = goal
            self._save_goals()
            logger.info(f"Added goal: {goal.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to add goal {goal.id}: {e}")
            return False
            
    def update_goal(self, goal_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing goal"""
        try:
            if goal_id in self.goals:
                goal = self.goals[goal_id]
                for key, value in updates.items():
                    if hasattr(goal, key):
                        setattr(goal, key, value)
                goal.updated_at = datetime.now().isoformat()
                self._save_goals()
                logger.info(f"Updated goal: {goal_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update goal {goal_id}: {e}")
            return False
            
    def get_goal(self, goal_id: str) -> Optional[AgentGoal]:
        """Retrieve a specific goal"""
        return self.goals.get(goal_id)
        
    def get_goals_by_agent(self, agent_name: str) -> List[AgentGoal]:
        """Get all goals for a specific agent"""
        return [goal for goal in self.goals.values() if goal.agent_name == agent_name]
        
    def get_goals_by_category(self, category: str) -> List[AgentGoal]:
        """Get all goals in a specific category"""
        return [goal for goal in self.goals.values() if goal.category == category]
        
    def get_active_goals(self) -> List[AgentGoal]:
        """Get all currently active goals"""
        return [goal for goal in self.goals.values() if goal.status == "active"]
        
    def get_goal_hierarchy(self, root_goal_id: str) -> Dict[str, Any]:
        """Get hierarchical structure of goals and sub-goals"""
        def build_hierarchy(goal_id: str) -> Dict[str, Any]:
            goal = self.goals.get(goal_id)
            if not goal:
                return {}
                
            hierarchy = {
                'goal': asdict(goal),
                'sub_goals': []
            }
            
            for sub_goal_id in goal.sub_goals:
                sub_hierarchy = build_hierarchy(sub_goal_id)
                if sub_hierarchy:
                    hierarchy['sub_goals'].append(sub_hierarchy)
                    
            return hierarchy
            
        return build_hierarchy(root_goal_id)
        
    def get_all_goals(self) -> List[AgentGoal]:
        """Get all registered goals"""
        return list(self.goals.values())
        
    def get_goals_summary(self) -> Dict[str, Any]:
        """Get summary statistics of all goals"""
        total_goals = len(self.goals)
        active_goals = len(self.get_active_goals())
        completed_goals = len([g for g in self.goals.values() if g.status == "completed"])
        failed_goals = len([g for g in self.goals.values() if g.status == "failed"])
        
        # Category breakdown
        categories = {}
        for goal in self.goals.values():
            categories[goal.category] = categories.get(goal.category, 0) + 1
            
        # Priority breakdown
        priorities = {}
        for goal in self.goals.values():
            priorities[goal.priority] = priorities.get(goal.priority, 0) + 1
            
        return {
            'total_goals': total_goals,
            'active_goals': active_goals,
            'completed_goals': completed_goals,
            'failed_goals': failed_goals,
            'categories': categories,
            'priorities': priorities,
            'completion_rate': completed_goals / max(1, total_goals)
        }

# Global registry instance
goals_registry = AgentGoalsRegistry()