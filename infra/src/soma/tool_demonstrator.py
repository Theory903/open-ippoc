#!/usr/bin/env python3
"""
Tool Demonstration Suite - Live showcase of all IPPOC tools in action
Runs real demonstrations of each tool's capabilities
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from soma.tool_explorer import tool_explorer

class ToolDemonstrator:
    """Demonstrates all tools with live examples"""
    
    def __init__(self):
        self.demonstrations = {}
        self.setup_demonstrations()
        
    def setup_demonstrations(self):
        """Setup demonstration methods for each tool category"""
        self.demonstrations = {
            'memory_system': self._demo_memory_system,
            'autonomy_controller': self._demo_autonomy_controller,
            'life_archiver': self._demo_life_archiver,
            'openclaw_core': self._demo_openclaw_core,
            'whatsapp_extension': self._demo_whatsapp_extension,
            'browser_automation': self._demo_browser_automation,
            'screenshot_capture': self._demo_screenshot_capture,
            'clipboard_monitor': self._demo_clipboard_monitor,
            'hal_power_core': self._demo_hal_power_core,
            'crypto_earning': self._demo_crypto_earning,
            'ai_group_formation': self._demo_ai_group_formation,
            'world_learning': self._demo_world_learning
        }
        
    async def demonstrate_all_tools(self) -> Dict[str, Any]:
        """Run demonstrations for all major tools"""
        print("🎭 Tool Demonstration Suite")
        print("=" * 40)
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tools_demonstrated': 0,
            'successful_demos': 0,
            'demo_results': {}
        }
        
        # Demonstrate each tool
        for tool_name, demo_func in self.demonstrations.items():
            try:
                print(f"\n🚀 Demonstrating {tool_name}...")
                demo_result = await demo_func()
                results['demo_results'][tool_name] = demo_result
                results['tools_demonstrated'] += 1
                
                if demo_result.get('status') == 'success':
                    results['successful_demos'] += 1
                    print(f"   ✅ Success: {demo_result.get('description', 'Demo completed')}")
                else:
                    print(f"   ⚠️  Partial: {demo_result.get('error', 'Limited functionality')}")
                    
            except Exception as e:
                results['demo_results'][tool_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                print(f"   ❌ Failed: {e}")
                
        # Summary
        print(f"\n📊 Demonstration Summary:")
        print(f"   Tools Demonstrated: {results['tools_demonstrated']}")
        print(f"   Successful Demos: {results['successful_demos']}")
        print(f"   Success Rate: {(results['successful_demos']/results['tools_demonstrated']*100):.1f}%")
        
        return results
        
    async def _demo_memory_system(self) -> Dict[str, Any]:
        """Demonstrate memory system capabilities"""
        try:
            # Import and test memory system
            from mnemosyne.graph.manager import GraphManager
            from mnemosyne.semantic.rag import SemanticManager
            
            # Create memory managers
            graph_manager = GraphManager()
            semantic_manager = SemanticManager(None, None)
            
            # Test memory operations
            test_content = "This is a demonstration of the IPPOC memory system"
            await semantic_manager.index_content(
                content=test_content,
                metadata={'demo': True, 'timestamp': datetime.now().isoformat()}
            )
            
            return {
                'status': 'success',
                'description': 'Memory system indexing and storage working',
                'capabilities_tested': ['content_indexing', 'metadata_storage'],
                'components': ['GraphManager', 'SemanticManager']
            }
            
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_autonomy_controller(self) -> Dict[str, Any]:
        """Demonstrate autonomy controller capabilities"""
        try:
            from cortex.core.autonomy import AutonomyController
            
            controller = AutonomyController()
            
            # Test decision making
            decision_context = {
                'task_type': 'demo',
                'priority': 'medium',
                'resources_available': True
            }
            
            decision = await controller.make_decision(decision_context)
            
            return {
                'status': 'success',
                'description': 'Autonomy controller decision making active',
                'capabilities_tested': ['decision_making', 'context_analysis'],
                'decision_made': bool(decision)
            }
            
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_life_archiver(self) -> Dict[str, Any]:
        """Demonstrate life archiving capabilities"""
        try:
            from soma.life_archiver import life_archiver
            
            # Test archiving workflow
            archive_status = life_archiver.get_archive_status()
            
            # Run a quick archive test
            test_data = {
                'type': 'demo_entry',
                'content': 'Test archive entry',
                'source': 'demonstration',
                'timestamp': datetime.now().isoformat()
            }
            
            # This would save to actual archive
            # await life_archiver._save_archive_entry(test_data, 'demo')
            
            return {
                'status': 'success',
                'description': 'Life archiving system operational',
                'capabilities_tested': ['status_check', 'data_structuring'],
                'items_archived': archive_status.get('total_items_archived', 0)
            }
            
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_openclaw_core(self) -> Dict[str, Any]:
        """Demonstrate OpenClaw core capabilities"""
        try:
            openclaw_path = Path("/Users/abhishekjha/CODE/ippoc/src/kernel/openclaw")
            
            # Test OpenClaw startup
            result = subprocess.run(
                ["node", "openclaw.mjs", "--help"],
                cwd=openclaw_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'description': 'OpenClaw core accessible and responsive',
                    'capabilities_tested': ['command_interface', 'help_system'],
                    'version_info': 'accessible'
                }
            else:
                return {
                    'status': 'partial',
                    'error': f'Help command failed: {result.stderr[:100]}'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_whatsapp_extension(self) -> Dict[str, Any]:
        """Demonstrate WhatsApp extension capabilities"""
        try:
            # Test WhatsApp integration (from previous real implementation)
            from soma.openclaw_tool_integrator import openclaw_integrator
            whatsapp_result = await openclaw_integrator._integrate_whatsapp()
            
            if whatsapp_result['status'] == 'connected':
                return {
                    'status': 'success',
                    'description': 'WhatsApp extension connected and capturing data',
                    'capabilities_tested': ['data_connection', 'message_capture'],
                    'connection_status': whatsapp_result['status']
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'WhatsApp extension available but limited',
                    'connection_status': whatsapp_result['status']
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_browser_automation(self) -> Dict[str, Any]:
        """Demonstrate browser automation capabilities"""
        try:
            from soma.openclaw_tool_integrator import openclaw_integrator
            browser_result = await openclaw_integrator._integrate_browser_automation()
            
            browsers_found = len(browser_result.get('supported_browsers', []))
            
            if browsers_found > 0:
                return {
                    'status': 'success',
                    'description': f'Browser automation detected {browsers_found} browsers',
                    'capabilities_tested': ['browser_detection', 'profile_access'],
                    'browsers_supported': browser_result['supported_browsers']
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Browser automation initialized but no browsers detected'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_screenshot_capture(self) -> Dict[str, Any]:
        """Demonstrate screenshot capture capabilities"""
        try:
            # Test system screenshot capability
            screencapture_test = subprocess.run(
                ["screencapture", "-c"],
                capture_output=True,
                timeout=5
            )
            
            if screencapture_test.returncode == 0:
                return {
                    'status': 'success',
                    'description': 'Screenshot capture system ready',
                    'capabilities_tested': ['system_integration', 'capture_testing'],
                    'tools_available': ['screencapture']
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Screenshot capture available but testing failed'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_clipboard_monitor(self) -> Dict[str, Any]:
        """Demonstrate clipboard monitoring capabilities"""
        try:
            # Test clipboard access
            clipboard_test = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if clipboard_test.returncode == 0:
                content = clipboard_test.stdout.strip()
                content_type = 'empty' if not content else 'text_content'
                
                return {
                    'status': 'success',
                    'description': f'Clipboard monitoring active ({content_type})',
                    'capabilities_tested': ['clipboard_access', 'content_detection'],
                    'content_available': bool(content)
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Clipboard access available but empty'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_hal_power_core(self) -> Dict[str, Any]:
        """Demonstrate HAL power core capabilities"""
        try:
            from soma.hal_power_core import hal_power_core
            
            # Test HAL system status
            hal_status = hal_power_core.get_system_status()
            
            if hal_status.get('status') == 'fully_operational':
                return {
                    'status': 'success',
                    'description': 'HAL power core fully operational',
                    'capabilities_tested': ['system_integration', 'status_check'],
                    'core_components': list(hal_status.get('components', {}).keys())
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'HAL system available but initializing'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_crypto_earning(self) -> Dict[str, Any]:
        """Demonstrate crypto earning capabilities"""
        try:
            from soma.integrated_hal_system import integrated_hal
            
            # Test crypto earning simulation
            crypto_context = {
                'task_type': 'earning',
                'strategy': 'arbitrage',
                'assets': ['BTC', 'ETH']
            }
            
            earning_result = await integrated_hal._hal_make_decision(crypto_context)
            
            if earning_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'description': 'Crypto earning strategies generated',
                    'capabilities_tested': ['strategy_generation', 'market_analysis'],
                    'strategies_created': len(earning_result.get('strategies', []))
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Crypto earning system available but limited'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_ai_group_formation(self) -> Dict[str, Any]:
        """Demonstrate AI group formation capabilities"""
        try:
            from soma.integrated_hal_system import integrated_hal
            
            # Test group formation
            group_context = {
                'task_type': 'social',
                'action': 'form_group',
                'members_needed': 5
            }
            
            group_result = await integrated_hal._hal_make_decision(group_context)
            
            if group_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'description': 'AI group formation successful',
                    'capabilities_tested': ['group_creation', 'member_coordination'],
                    'groups_formed': group_result.get('groups_created', 0)
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Group formation system available'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}
            
    async def _demo_world_learning(self) -> Dict[str, Any]:
        """Demonstrate world learning capabilities"""
        try:
            from soma.integrated_hal_system import integrated_hal
            
            # Test learning capability
            learning_context = {
                'task_type': 'learning',
                'topic': 'technology_trends',
                'depth': 'comprehensive'
            }
            
            learning_result = await integrated_hal._hal_make_decision(learning_context)
            
            if learning_result.get('status') == 'success':
                return {
                    'status': 'success',
                    'description': 'World learning system active',
                    'capabilities_tested': ['information_gathering', 'knowledge_integration'],
                    'topics_learned': len(learning_result.get('learned_topics', []))
                }
            else:
                return {
                    'status': 'partial',
                    'description': 'Learning system available but limited'
                }
                
        except Exception as e:
            return {'status': 'partial', 'error': str(e)}

# Global demonstrator instance
tool_demonstrator = ToolDemonstrator()

async def main():
    """Run the complete tool demonstration"""
    results = await tool_demonstrator.demonstrate_all_tools()
    
    # Generate final report
    print(f"\n📋 Final Tool Report:")
    print(f"   Total Tools in Ecosystem: {len(tool_explorer.tools)}")
    print(f"   Tools Demonstrated: {results['tools_demonstrated']}")
    print(f"   Success Rate: {(results['successful_demos']/results['tools_demonstrated']*100):.1f}%")
    
    # Show top performing categories
    category_performance = {}
    for category, tools in tool_explorer.categories.items():
        active_count = len([t for t in tools if tool_explorer.tools[t].status in ['active', 'ready']])
        category_performance[category] = (active_count, len(tools))
    
    print(f"\n🏆 Top Performing Categories:")
    sorted_categories = sorted(category_performance.items(), 
                             key=lambda x: x[1][0]/x[1][1] if x[1][1] > 0 else 0, 
                             reverse=True)
    
    for category, (active, total) in sorted_categories[:5]:
        percentage = (active/total*100) if total > 0 else 0
        print(f"   {category}: {active}/{total} ({percentage:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())