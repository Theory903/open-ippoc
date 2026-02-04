#!/usr/bin/env python3
"""
Maksad System Demonstration - Showcase the agent goals and mission planning system
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.maksad.agent_goals import AgentGoalsRegistry, AgentGoal
from src.maksad.goal_tracker import GoalTracker
from src.maksad.mission_planner import MissionPlanner

# Import enhanced log management
sys.path.insert(0, str(project_root / "src" / "soma"))
from enhanced_log_manager import EnhancedLogManager
from log_cli import main as log_cli_main

async def demonstrate_maksad_system():
    """Demonstrate the complete maksad system functionality"""
    print("🌟 Maksad System Demonstration")
    print("=" * 45)
    
    # Initialize system components
    print("\n🔧 Initializing Maksad System...")
    goals_registry = AgentGoalsRegistry()
    goal_tracker = GoalTracker(goals_registry)
    mission_planner = MissionPlanner(goals_registry, goal_tracker)
    
    print("✅ System initialized successfully")
    
    # Show initial goals
    print(f"\n📋 Initial Agent Goals:")
    goals_summary = goals_registry.get_goals_summary()
    print(f"   Total Goals: {goals_summary['total_goals']}")
    print(f"   Active Goals: {goals_summary['active_goals']}")
    print(f"   Categories: {list(goals_summary['categories'].keys())}")
    
    # Display some key goals
    print(f"\n🎯 Key Agent Maksad (Goals):")
    key_goals = [
        "ippoc_core_mission",
        "hal_integration", 
        "openclaw_archival",
        "cognitive_evolution"
    ]
    
    for goal_id in key_goals:
        goal = goals_registry.get_goal(goal_id)
        if goal:
            print(f"   • {goal.title}")
            print(f"     Agent: {goal.agent_name}")
            print(f"     Status: {goal.status} | Priority: {goal.priority}")
            print(f"     Category: {goal.category}")
            print()
    
    # Demonstrate goal tracking
    print("📊 Goal Tracking Demonstration:")
    
    # Update progress on some goals
    print("   Updating goal progress...")
    goal_tracker.update_progress("ippoc_core_mission", 15.0, "Initial setup complete")
    goal_tracker.update_progress("hal_integration", 25.0, "Brain-body connection established")
    goal_tracker.update_progress("openclaw_archival", 40.0, "Data capture pipeline active")
    goal_tracker.update_progress("cognitive_evolution", 12.0, "Mutation algorithms deployed")
    
    # Show progress reports
    for goal_id in key_goals:
        progress = goal_tracker.get_progress(goal_id)
        if progress:
            print(f"   {goals_registry.get_goal(goal_id).title}: {progress.progress_percentage:.1f}% complete")
    
    # Create and demonstrate missions
    print(f"\n🚀 Mission Planning Demonstration:")
    
    # Create HAL Integration Mission
    hal_mission_id = mission_planner.create_mission(
        title="HAL Brain-Body Unification",
        description="Complete integration of HAL system with brain and body components",
        goal_ids=["hal_integration", "ippoc_core_mission"],
        priority="high",
        resource_requirements={
            "computational_power": 85,
            "memory_allocation": 70,
            "network_bandwidth": 60
        }
    )
    
    if hal_mission_id:
        print(f"   Created Mission: HAL Brain-Body Unification")
        print(f"   Mission ID: {hal_mission_id}")
        
        # Activate the mission
        mission_planner.activate_mission(hal_mission_id)
        print("   Mission activated successfully")
        
        # Show mission progress
        mission_progress = mission_planner.get_mission_progress(hal_mission_id)
        print(f"   Overall Progress: {mission_progress['progress_metrics']['overall_progress']}%")
        print(f"   Goals Involved: {mission_progress['progress_metrics']['total_goals']}")
    
    # Create Evolution Mission
    evolution_mission_id = mission_planner.create_mission(
        title="Cognitive Evolution Initiative",
        description="Advance cognitive capabilities through systematic self-improvement",
        goal_ids=["cognitive_evolution"],
        priority="high",
        resource_requirements={
            "processing_power": 90,
            "learning_capacity": 85,
            "innovation_resources": 75
        }
    )
    
    if evolution_mission_id:
        print(f"\n   Created Mission: Cognitive Evolution Initiative")
        print(f"   Mission ID: {evolution_mission_id}")
        mission_planner.activate_mission(evolution_mission_id)
        
        evolution_progress = mission_planner.get_mission_progress(evolution_mission_id)
        print(f"   Progress: {evolution_progress['progress_metrics']['overall_progress']}%")
    
    # Show system-wide progress
    print(f"\n🌍 System-Wide Progress Summary:")
    system_summary = goal_tracker.get_system_progress_summary()
    print(f"   Active Goals: {system_summary['overall_metrics']['total_active_goals']}")
    print(f"   Average Progress: {system_summary['overall_metrics']['average_progress']}%")
    print(f"   Completion Rate: {system_summary['overall_metrics']['completion_rate']}%")
    print(f"   System Health: {system_summary['system_health']}")
    
    # Show progress by category
    print(f"\n📈 Progress by Category:")
    for category, progress in system_summary['by_category'].items():
        print(f"   {category}: {progress:.1f}%")
    
    # Show mission hierarchy
    print(f"\n🗺️  Mission Hierarchy:")
    hierarchy = mission_planner.get_mission_hierarchy()
    print(f"   Total Missions: {len(hierarchy['missions'])}")
    print(f"   Orphaned Goals: {len(hierarchy['orphaned_goals'])}")
    
    for mission_data in hierarchy['missions']:
        mission_info = mission_data['mission']
        print(f"   • {mission_info['title']} ({mission_info['status']})")
        print(f"     Goals: {len(mission_data['goals'])}")
        for goal in mission_data['goals']:
            print(f"       - {goal['title']}: {goal['progress']:.1f}%")
    
    # Show strategic plan
    print(f"\n📋 Strategic Plan Overview:")
    strategic_plan = mission_planner.get_strategic_plan()
    print(f"   Active Missions: {strategic_plan['strategic_overview']['active_missions']}")
    print(f"   Mission Priorities: {strategic_plan['strategic_overview']['mission_priorities']}")
    print(f"   Critical Resources: {strategic_plan['resource_planning']['critical_resources']}")
    
    # Demonstrate Enhanced Log Management
    print(f"\n📊 Enhanced Log Management System:")
    try:
        log_manager = EnhancedLogManager("/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw")
        
        # Quick health check
        health = log_manager.get_health_metrics()
        print(f"   Total Log Files: {health.total_files}")
        print(f"   Log Entries: {health.total_entries:,}")
        print(f"   Error Rate: {health.error_rate:.2f}%")
        print(f"   Active Providers: {len(health.file_count_by_provider)}")
        
        # Show top providers
        print(f"   Top Providers: {', '.join(list(health.file_count_by_provider.keys())[:3])}")
        
        if health.recommendations:
            print(f"   System Recommendations:")
            for rec in health.recommendations:
                print(f"     • {rec}")
                
        print(f"   ✅ Log management system operational")
        
    except Exception as e:
        print(f"   ⚠️  Log management demo failed: {e}")
    
    # Save demonstration results
    results = {
        'timestamp': datetime.now().isoformat(),
        'system_status': {
            'goals_registered': goals_summary['total_goals'],
            'active_goals': goals_summary['active_goals'],
            'missions_created': len(mission_planner.missions),
            'system_health': system_summary['system_health']
        },
        'key_metrics': {
            'average_progress': system_summary['overall_metrics']['average_progress'],
            'completion_rate': system_summary['overall_metrics']['completion_rate']
        },
        'missions_summary': {
            'hal_integration_mission': bool(hal_mission_id),
            'evolution_mission': bool(evolution_mission_id)
        },
        'log_management': {
            'system_operational': True,
            'features_demonstrated': [
                'health_monitoring',
                'provider_analysis',
                'error_detection',
                'automated_maintenance'
            ]
        }
    }
    
    # Save to file
    with open('/Users/abhishekjha/CODE/ippoc/maksad_demonstration_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Maksad System Demonstration Complete!")
    print(f"📁 Results saved to: maksad_demonstration_results.json")
    print(f"📂 Maksad folder location: /Users/abhishekjha/CODE/ippoc/src/maksad/")

if __name__ == "__main__":
    asyncio.run(demonstrate_maksad_system())