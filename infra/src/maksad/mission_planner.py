"""
Mission Planner - Strategic planning and coordination of agent goals
Creates mission hierarchies, dependencies, and execution plans
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from .agent_goals import AgentGoalsRegistry, AgentGoal
from .goal_tracker import GoalTracker

logger = logging.getLogger(__name__)

@dataclass
class MissionPlan:
    """Represents a coordinated mission involving multiple goals"""
    id: str
    title: str
    description: str
    goals_involved: List[str]
    priority: str
    start_time: str
    estimated_duration: str
    resource_requirements: Dict[str, Any]
    dependencies: List[str]
    status: str  # planned, active, completed, cancelled

class MissionPlanner:
    """Plans and coordinates complex missions involving multiple agent goals"""
    
    def __init__(self, goals_registry: AgentGoalsRegistry, goal_tracker: GoalTracker):
        self.goals_registry = goals_registry
        self.goal_tracker = goal_tracker
        self.missions: Dict[str, MissionPlan] = {}
        self.mission_dependencies: Dict[str, Set[str]] = {}
        
    def create_mission(self, title: str, description: str, 
                      goal_ids: List[str], priority: str = "medium",
                      resource_requirements: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new mission coordinating multiple goals"""
        try:
            # Validate goal IDs
            invalid_goals = [gid for gid in goal_ids if not self.goals_registry.get_goal(gid)]
            if invalid_goals:
                logger.error(f"Invalid goal IDs: {invalid_goals}")
                return None
                
            # Generate mission ID
            mission_id = f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Resolve dependencies
            dependencies = self._resolve_mission_dependencies(goal_ids)
            
            # Create mission plan
            mission = MissionPlan(
                id=mission_id,
                title=title,
                description=description,
                goals_involved=goal_ids,
                priority=priority,
                start_time=datetime.now().isoformat(),
                estimated_duration=self._estimate_mission_duration(goal_ids),
                resource_requirements=resource_requirements or {},
                dependencies=list(dependencies),
                status="planned"
            )
            
            self.missions[mission_id] = mission
            self.mission_dependencies[mission_id] = dependencies
            
            # Update goal statuses to indicate mission involvement
            for goal_id in goal_ids:
                self.goals_registry.update_goal(goal_id, {
                    'status': 'active',
                    'metadata': {**(self.goals_registry.get_goal(goal_id).metadata), 'mission_id': mission_id}
                })
                
            logger.info(f"Created mission: {title} ({mission_id})")
            return mission_id
            
        except Exception as e:
            logger.error(f"Failed to create mission: {e}")
            return None
            
    def _resolve_mission_dependencies(self, goal_ids: List[str]) -> Set[str]:
        """Resolve dependencies between goals in a mission"""
        dependencies = set()
        
        for goal_id in goal_ids:
            goal = self.goals_registry.get_goal(goal_id)
            if goal and goal.dependencies:
                dependencies.update(goal.dependencies)
                
        # Remove internal dependencies (goals within the same mission)
        internal_deps = set(goal_ids)
        return dependencies - internal_deps
        
    def _estimate_mission_duration(self, goal_ids: List[str]) -> str:
        """Estimate total duration for mission completion"""
        total_duration = timedelta()
        
        for goal_id in goal_ids:
            goal = self.goals_registry.get_goal(goal_id)
            if goal:
                # Simple estimation based on goal complexity and current progress
                progress = self.goal_tracker.get_progress(goal_id)
                current_progress = progress.progress_percentage if progress else 0
                
                # Base estimates (in days) - would be more sophisticated in production
                base_estimates = {
                    'core': 30,
                    'economic': 15,
                    'integration': 20,
                    'archiving': 10,
                    'evolution': 25,
                    'communication': 5,
                    'automation': 8,
                    'capture': 3,
                    'monitoring': 7,
                    'knowledge': 12
                }
                
                base_days = base_estimates.get(goal.category, 10)
                remaining_days = base_days * (100 - current_progress) / 100
                total_duration += timedelta(days=remaining_days)
                
        return str(total_duration)
        
    def activate_mission(self, mission_id: str) -> bool:
        """Activate a planned mission"""
        try:
            if mission_id in self.missions:
                mission = self.missions[mission_id]
                if mission.status == "planned":
                    mission.status = "active"
                    mission.start_time = datetime.now().isoformat()
                    
                    # Activate all involved goals
                    for goal_id in mission.goals_involved:
                        self.goals_registry.update_goal(goal_id, {'status': 'active'})
                        
                    logger.info(f"Activated mission: {mission.title}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to activate mission {mission_id}: {e}")
            return False
            
    def get_mission(self, mission_id: str) -> Optional[MissionPlan]:
        """Retrieve a specific mission"""
        return self.missions.get(mission_id)
        
    def get_active_missions(self) -> List[MissionPlan]:
        """Get all currently active missions"""
        return [mission for mission in self.missions.values() if mission.status == "active"]
        
    def get_mission_progress(self, mission_id: str) -> Dict[str, Any]:
        """Get detailed progress for a mission"""
        if mission_id not in self.missions:
            return {'error': 'Mission not found'}
            
        mission = self.missions[mission_id]
        goal_progresses = []
        total_progress = 0
        
        for goal_id in mission.goals_involved:
            progress = self.goal_tracker.get_progress(goal_id)
            goal = self.goals_registry.get_goal(goal_id)
            
            if progress and goal:
                goal_progresses.append({
                    'goal_id': goal_id,
                    'goal_title': goal.title,
                    'progress': progress.progress_percentage,
                    'status': goal.status,
                    'blockers': progress.blockers
                })
                total_progress += progress.progress_percentage
                
        avg_progress = total_progress / len(mission.goals_involved) if mission.goals_involved else 0
        
        return {
            'mission_info': {
                'id': mission.id,
                'title': mission.title,
                'status': mission.status,
                'priority': mission.priority
            },
            'progress_metrics': {
                'overall_progress': round(avg_progress, 2),
                'goals_completed': len([gp for gp in goal_progresses if gp['progress'] >= 100]),
                'total_goals': len(mission.goals_involved),
                'active_blockers': sum(len(gp['blockers']) for gp in goal_progresses)
            },
            'goal_breakdown': goal_progresses,
            'dependencies_status': self._check_dependencies_status(mission_id),
            'report_timestamp': datetime.now().isoformat()
        }
        
    def _check_dependencies_status(self, mission_id: str) -> Dict[str, Any]:
        """Check status of mission dependencies"""
        dependencies = self.mission_dependencies.get(mission_id, set())
        dependency_status = {}
        
        for dep_id in dependencies:
            goal = self.goals_registry.get_goal(dep_id)
            progress = self.goal_tracker.get_progress(dep_id)
            
            if goal and progress:
                dependency_status[dep_id] = {
                    'title': goal.title,
                    'status': goal.status,
                    'progress': progress.progress_percentage,
                    'completed': progress.progress_percentage >= 100
                }
            else:
                dependency_status[dep_id] = {
                    'status': 'unknown',
                    'completed': False
                }
                
        blockers = [dep_id for dep_id, status in dependency_status.items() 
                   if not status.get('completed', False)]
                   
        return {
            'total_dependencies': len(dependencies),
            'completed_dependencies': len(dependencies) - len(blockers),
            'blocking_dependencies': blockers,
            'dependency_status': dependency_status
        }
        
    def get_mission_hierarchy(self) -> Dict[str, Any]:
        """Get hierarchical view of all missions and their relationships"""
        hierarchy = {
            'missions': [],
            'orphaned_goals': []
        }
        
        # Get all missions
        for mission in self.missions.values():
            mission_detail = {
                'mission': {
                    'id': mission.id,
                    'title': mission.title,
                    'status': mission.status,
                    'priority': mission.priority
                },
                'goals': []
            }
            
            # Add goals in this mission
            for goal_id in mission.goals_involved:
                goal = self.goals_registry.get_goal(goal_id)
                progress = self.goal_tracker.get_progress(goal_id)
                
                if goal and progress:
                    mission_detail['goals'].append({
                        'id': goal_id,
                        'title': goal.title,
                        'progress': progress.progress_percentage,
                        'status': goal.status
                    })
                    
            hierarchy['missions'].append(mission_detail)
            
        # Find goals not in any mission
        mission_goal_ids = set()
        for mission in self.missions.values():
            mission_goal_ids.update(mission.goals_involved)
            
        all_goals = self.goals_registry.get_all_goals()
        orphaned_goals = [goal for goal in all_goals if goal.id not in mission_goal_ids]
        
        hierarchy['orphaned_goals'] = [
            {
                'id': goal.id,
                'title': goal.title,
                'agent': goal.agent_name,
                'status': goal.status,
                'progress': self.goal_tracker.get_progress(goal.id).progress_percentage if self.goal_tracker.get_progress(goal.id) else 0
            }
            for goal in orphaned_goals
        ]
        
        return hierarchy
        
    def get_strategic_plan(self) -> Dict[str, Any]:
        """Generate high-level strategic plan"""
        active_missions = self.get_active_missions()
        all_goals = self.goals_registry.get_all_goals()
        
        # Priority-based mission scheduling
        high_priority_missions = [m for m in active_missions if m.priority == "high"]
        medium_priority_missions = [m for m in active_missions if m.priority == "medium"]
        low_priority_missions = [m for m in active_missions if m.priority == "low"]
        
        # Resource allocation overview
        resource_needs = {}
        for mission in active_missions:
            for resource, amount in mission.resource_requirements.items():
                resource_needs[resource] = resource_needs.get(resource, 0) + amount
                
        return {
            'strategic_overview': {
                'total_missions': len(self.missions),
                'active_missions': len(active_missions),
                'total_goals': len(all_goals),
                'mission_priorities': {
                    'high': len(high_priority_missions),
                    'medium': len(medium_priority_missions),
                    'low': len(low_priority_missions)
                }
            },
            'resource_planning': {
                'required_resources': resource_needs,
                'critical_resources': [r for r, amt in resource_needs.items() if amt > 50]
            },
            'timeline_projection': self._project_timeline(),
            'risk_assessment': self._assess_mission_risks(),
            'report_generated': datetime.now().isoformat()
        }
        
    def _project_timeline(self) -> Dict[str, Any]:
        """Project mission completion timeline"""
        active_missions = self.get_active_missions()
        timeline = {}
        
        for mission in active_missions:
            # Simple timeline projection
            start_date = datetime.fromisoformat(mission.start_time)
            try:
                duration = timedelta(days=float(mission.estimated_duration.split()[0]))
                end_date = start_date + duration
                timeline[mission.id] = {
                    'mission': mission.title,
                    'start_date': start_date.isoformat(),
                    'projected_end': end_date.isoformat(),
                    'days_remaining': (end_date - datetime.now()).days
                }
            except:
                timeline[mission.id] = {
                    'mission': mission.title,
                    'start_date': start_date.isoformat(),
                    'projected_end': 'unknown'
                }
                
        return timeline
        
    def _assess_mission_risks(self) -> List[Dict[str, Any]]:
        """Assess risks for active missions"""
        risks = []
        active_missions = self.get_active_missions()
        
        for mission in active_missions:
            progress = self.get_mission_progress(mission.id)
            dependencies = self._check_dependencies_status(mission.id)
            
            risk_factors = []
            
            # Dependency risks
            if dependencies['blocking_dependencies']:
                risk_factors.append({
                    'type': 'dependency_blocker',
                    'severity': 'high',
                    'description': f"{len(dependencies['blocking_dependencies'])} blocking dependencies"
                })
                
            # Progress risks
            if progress['progress_metrics']['overall_progress'] < 30:
                risk_factors.append({
                    'type': 'slow_progress',
                    'severity': 'medium',
                    'description': 'Below expected progress threshold'
                })
                
            # Resource risks
            critical_resources = [r for r in mission.resource_requirements.values() if r > 80]
            if critical_resources:
                risk_factors.append({
                    'type': 'resource_constraint',
                    'severity': 'high',
                    'description': 'High resource requirements'
                })
                
            if risk_factors:
                risks.append({
                    'mission_id': mission.id,
                    'mission_title': mission.title,
                    'risk_factors': risk_factors,
                    'overall_risk': max(rf['severity'] for rf in risk_factors)
                })
                
        return risks

# Global mission planner instance
mission_planner = MissionPlanner(AgentGoalsRegistry(), GoalTracker(AgentGoalsRegistry()))