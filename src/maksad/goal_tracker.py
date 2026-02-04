"""
Goal Tracker - Monitor and track progress of agent goals
Provides real-time tracking, metrics, and progress reporting
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from .agent_goals import AgentGoalsRegistry, AgentGoal

logger = logging.getLogger(__name__)

@dataclass
class GoalProgress:
    """Tracks progress of a specific goal"""
    goal_id: str
    progress_percentage: float
    last_updated: str
    milestones_achieved: List[str]
    metrics_current: Dict[str, Any]
    estimated_completion: Optional[str]
    blockers: List[str]

class GoalTracker:
    """Tracks and monitors agent goal progress"""
    
    def __init__(self, goals_registry: AgentGoalsRegistry):
        self.goals_registry = goals_registry
        self.progress_trackers: Dict[str, GoalProgress] = {}
        self.tracking_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self._initialize_progress_trackers()
        
    def _initialize_progress_trackers(self):
        """Initialize progress trackers for all goals"""
        for goal in self.goals_registry.get_all_goals():
            self.progress_trackers[goal.id] = GoalProgress(
                goal_id=goal.id,
                progress_percentage=0.0,
                last_updated=datetime.now().isoformat(),
                milestones_achieved=[],
                metrics_current=goal.metrics.copy(),
                estimated_completion=None,
                blockers=[]
            )
            self.tracking_history[goal.id] = []
            
    def update_progress(self, goal_id: str, progress_delta: float, 
                       milestone: Optional[str] = None, 
                       metrics_update: Optional[Dict[str, Any]] = None,
                       blocker: Optional[str] = None) -> bool:
        """Update progress for a specific goal"""
        try:
            if goal_id not in self.progress_trackers:
                logger.warning(f"No progress tracker for goal: {goal_id}")
                return False
                
            tracker = self.progress_trackers[goal_id]
            
            # Update progress percentage
            new_progress = min(100.0, tracker.progress_percentage + progress_delta)
            tracker.progress_percentage = new_progress
            
            # Add milestone if achieved
            if milestone and milestone not in tracker.milestones_achieved:
                tracker.milestones_achieved.append(milestone)
                
            # Update metrics
            if metrics_update:
                tracker.metrics_current.update(metrics_update)
                
            # Add blocker if exists
            if blocker and blocker not in tracker.blockers:
                tracker.blockers.append(blocker)
                
            # Update timestamps
            tracker.last_updated = datetime.now().isoformat()
            
            # Estimate completion time
            if new_progress > 0 and new_progress < 100:
                tracker.estimated_completion = self._estimate_completion(goal_id, new_progress)
                
            # Update goal status if completed
            if new_progress >= 100.0:
                self.goals_registry.update_goal(goal_id, {'status': 'completed'})
                
            # Record in history
            self._record_progress_history(goal_id, tracker)
            
            logger.info(f"Updated progress for {goal_id}: {new_progress:.1f}%")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update progress for {goal_id}: {e}")
            return False
            
    def _estimate_completion(self, goal_id: str, current_progress: float) -> str:
        """Estimate completion time based on progress history"""
        try:
            history = self.tracking_history.get(goal_id, [])
            if len(history) < 2:
                return None
                
            # Calculate average progress rate
            total_time = 0
            total_progress = 0
            
            for i in range(1, len(history)):
                prev_record = history[i-1]
                curr_record = history[i]
                
                time_diff = datetime.fromisoformat(curr_record['timestamp']) - datetime.fromisoformat(prev_record['timestamp'])
                progress_diff = curr_record['progress'] - prev_record['progress']
                
                if progress_diff > 0:
                    total_time += time_diff.total_seconds()
                    total_progress += progress_diff
                    
            if total_progress > 0:
                avg_rate = total_progress / total_time  # progress per second
                remaining_progress = 100.0 - current_progress
                remaining_time = remaining_progress / avg_rate
                
                completion_date = datetime.now() + timedelta(seconds=remaining_time)
                return completion_date.isoformat()
                
            return None
            
        except Exception as e:
            logger.warning(f"Failed to estimate completion for {goal_id}: {e}")
            return None
            
    def _record_progress_history(self, goal_id: str, tracker: GoalProgress):
        """Record progress update in history"""
        history_record = {
            'timestamp': datetime.now().isoformat(),
            'progress': tracker.progress_percentage,
            'milestones': tracker.milestones_achieved.copy(),
            'metrics': tracker.metrics_current.copy(),
            'blockers': tracker.blockers.copy()
        }
        
        if goal_id not in self.tracking_history:
            self.tracking_history[goal_id] = []
            
        self.tracking_history[goal_id].append(history_record)
        
        # Keep only last 100 records to prevent memory bloat
        if len(self.tracking_history[goal_id]) > 100:
            self.tracking_history[goal_id] = self.tracking_history[goal_id][-100:]
            
    def get_progress(self, goal_id: str) -> Optional[GoalProgress]:
        """Get current progress for a goal"""
        return self.progress_trackers.get(goal_id)
        
    def get_all_progress(self) -> Dict[str, GoalProgress]:
        """Get progress for all goals"""
        return self.progress_trackers.copy()
        
    def get_progress_report(self, goal_id: str) -> Dict[str, Any]:
        """Generate detailed progress report for a goal"""
        if goal_id not in self.progress_trackers:
            return {'error': 'Goal not found'}
            
        tracker = self.progress_trackers[goal_id]
        goal = self.goals_registry.get_goal(goal_id)
        
        if not goal:
            return {'error': 'Goal data not available'}
            
        # Calculate velocity (recent progress rate)
        velocity = self._calculate_velocity(goal_id)
        
        # Get recent history
        recent_history = self.tracking_history.get(goal_id, [])[-10:]
        
        return {
            'goal_info': {
                'id': goal.id,
                'title': goal.title,
                'agent': goal.agent_name,
                'category': goal.category,
                'priority': goal.priority,
                'status': goal.status
            },
            'progress_metrics': {
                'current_progress': tracker.progress_percentage,
                'velocity_percent_per_day': velocity,
                'milestones_achieved': tracker.milestones_achieved,
                'estimated_completion': tracker.estimated_completion,
                'blockers_count': len(tracker.blockers)
            },
            'current_metrics': tracker.metrics_current,
            'blockers': tracker.blockers,
            'recent_history': recent_history,
            'report_generated': datetime.now().isoformat()
        }
        
    def _calculate_velocity(self, goal_id: str) -> float:
        """Calculate progress velocity (percent per day)"""
        try:
            history = self.tracking_history.get(goal_id, [])
            if len(history) < 2:
                return 0.0
                
            # Get last 5 records
            recent_records = history[-5:] if len(history) >= 5 else history
            
            if len(recent_records) < 2:
                return 0.0
                
            first_record = recent_records[0]
            last_record = recent_records[-1]
            
            time_diff = datetime.fromisoformat(last_record['timestamp']) - datetime.fromisoformat(first_record['timestamp'])
            progress_diff = last_record['progress'] - first_record['progress']
            
            if time_diff.days > 0:
                return progress_diff / time_diff.days
                
            return 0.0
            
        except Exception as e:
            logger.warning(f"Failed to calculate velocity for {goal_id}: {e}")
            return 0.0
            
    def get_system_progress_summary(self) -> Dict[str, Any]:
        """Get overall system progress summary"""
        all_trackers = self.get_all_progress()
        active_goals = self.goals_registry.get_active_goals()
        
        total_progress = 0
        completed_count = 0
        active_count = len(active_goals)
        
        category_progress = {}
        agent_progress = {}
        
        for goal in active_goals:
            tracker = all_trackers.get(goal.id)
            if tracker:
                progress = tracker.progress_percentage
                total_progress += progress
                
                # Category breakdown
                category_progress[goal.category] = category_progress.get(goal.category, 0) + progress
                
                # Agent breakdown
                agent_progress[goal.agent_name] = agent_progress.get(goal.agent_name, 0) + progress
                
                if progress >= 100:
                    completed_count += 1
                    
        avg_progress = total_progress / max(1, len(active_goals))
        
        # Normalize category and agent progress
        for category in category_progress:
            category_progress[category] /= len([g for g in active_goals if g.category == category])
            
        for agent in agent_progress:
            agent_progress[agent] /= len([g for g in active_goals if g.agent_name == agent])
            
        return {
            'overall_metrics': {
                'total_active_goals': active_count,
                'completed_goals': completed_count,
                'average_progress': round(avg_progress, 2),
                'completion_rate': round(completed_count / max(1, active_count) * 100, 2)
            },
            'by_category': category_progress,
            'by_agent': agent_progress,
            'system_health': 'healthy' if avg_progress > 70 else 'needs_attention',
            'report_timestamp': datetime.now().isoformat()
        }
        
    def add_milestone(self, goal_id: str, milestone: str) -> bool:
        """Add a milestone to a goal's progress"""
        try:
            if goal_id in self.progress_trackers:
                tracker = self.progress_trackers[goal_id]
                if milestone not in tracker.milestones_achieved:
                    tracker.milestones_achieved.append(milestone)
                    tracker.last_updated = datetime.now().isoformat()
                    self._record_progress_history(goal_id, tracker)
                    logger.info(f"Added milestone '{milestone}' to goal {goal_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to add milestone to {goal_id}: {e}")
            return False
            
    def resolve_blocker(self, goal_id: str, blocker: str) -> bool:
        """Mark a blocker as resolved"""
        try:
            if goal_id in self.progress_trackers:
                tracker = self.progress_trackers[goal_id]
                if blocker in tracker.blockers:
                    tracker.blockers.remove(blocker)
                    tracker.last_updated = datetime.now().isoformat()
                    self._record_progress_history(goal_id, tracker)
                    logger.info(f"Resolved blocker '{blocker}' for goal {goal_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to resolve blocker for {goal_id}: {e}")
            return False

# Global tracker instance
goal_tracker = GoalTracker(AgentGoalsRegistry())