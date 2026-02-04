# brain/gateway/proprioception_scanner.py
# @cognitive - Dynamic Skill Discovery & Proprioception Mapping
# Prevents IPPOC from hallucinating tools that OpenClaw already provides

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import TS bridge for enhanced skill discovery
try:
    from cortex.gateway.ts_bridge import get_ts_bridge, initialize_bridge
    _TS_BRIDGE_AVAILABLE = True
except ImportError:
    _TS_BRIDGE_AVAILABLE = False

@dataclass
class SkillDefinition:
    """Represents an OpenClaw skill with its capabilities"""
    name: str
    description: str
    category: str
    intent_match: List[str]
    energy_cost: float  # Lower cost = preferred over hallucinated solutions
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]

class ProprioceptionScanner:
    """
    The "Muscle Memory Scanner" - Discovers OpenClaw skills and maps them 
    to IPPOC's motor cortex to prevent hallucination.
    """
    
    def __init__(self, openclaw_root: str = "src/kernel/openclaw"):
        self.openclaw_root = Path(openclaw_root)
        self.skills_root = self.openclaw_root / "skills"
        self.discovered_skills: Dict[str, SkillDefinition] = {}
        self.skill_index: Dict[str, List[str]] = {}  # intent -> [skill_names]
        
    async def scan_skills(self) -> Dict[str, SkillDefinition]:
        """
        Crawls the skills directory and extracts muscle definitions.
        Enhanced with TypeScript adapter integration for comprehensive discovery.
        """
        if not self.skills_root.exists():
            raise FileNotFoundError(f"OpenClaw skills directory not found: {self.skills_root}")
            
        print(f"[Proprioception] Scanning OpenClaw skills at {self.skills_root}")
        
        # 1. Scan filesystem skills (traditional method)
        fs_skills = await self._scan_filesystem_skills()
        
        # 2. Query TypeScript adapter for additional skills
        ts_skills = await self._query_ts_skills()
        
        # 3. Merge and deduplicate
        all_skills = {**fs_skills, **ts_skills}
        self.discovered_skills = all_skills
        
        # 4. Build indexes
        for skill in self.discovered_skills.values():
            self._index_skill_intents(skill)
            
        print(f"[Proprioception] Discovered {len(self.discovered_skills)} total skills ({len(fs_skills)} filesystem + {len(ts_skills)} TypeScript)")
        return self.discovered_skills
    
    async def _scan_filesystem_skills(self) -> Dict[str, SkillDefinition]:
        """Scan traditional filesystem-based skills"""
        skills = {}
        
        for skill_dir in self.skills_root.iterdir():
            if not skill_dir.is_dir():
                continue
                
            skill_name = skill_dir.name
            skill_md_path = skill_dir / "SKILL.md"
            
            if not skill_md_path.exists():
                print(f"[Proprioception] Warning: No SKILL.md found for {skill_name}")
                continue
                
            try:
                definition = self._parse_skill_md(skill_md_path, skill_name)
                skills[skill_name] = definition
                print(f"[Proprioception] Registered FS skill: {skill_name} (Cost: {definition.energy_cost})")
            except Exception as e:
                print(f"[Proprioception] Error parsing {skill_name}: {e}")
                continue
                
        return skills
    
    async def _query_ts_skills(self) -> Dict[str, SkillDefinition]:
        """Query TypeScript adapter for dynamically registered skills"""
        skills = {}
        
        if not _TS_BRIDGE_AVAILABLE:
            print("[Proprioception] TS bridge not available, skipping dynamic skill discovery")
            return skills
            
        try:
            # Initialize TS bridge
            bridge = get_ts_bridge()
            if not await bridge.initialize():
                print("[Proprioception] TS bridge initialization failed")
                return skills
                
            # Get available skills from TS adapter
            ts_skills_data = await bridge.get_openclaw_skills()
            
            for skill_name, skill_info in ts_skills_data.items():
                try:
                    # Convert TS skill info to our format
                    definition = SkillDefinition(
                        name=skill_name,
                        description=skill_info.get("description", f"OpenClaw skill: {skill_name}"),
                        category=self._classify_skill(skill_name, skill_info, skill_info.get("description", "")),
                        intent_match=skill_info.get("patterns", [skill_name]),
                        energy_cost=float(skill_info.get("energy_cost", 1.0)),
                        parameters=skill_info.get("parameters", {}),
                        metadata=skill_info.get("metadata", {})
                    )
                    skills[skill_name] = definition
                    print(f"[Proprioception] Registered TS skill: {skill_name} (Cost: {definition.energy_cost})")
                except Exception as e:
                    print(f"[Proprioception] Error processing TS skill {skill_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[Proprioception] TS skill discovery failed: {e}")
            
        return skills
    
    def _parse_skill_md(self, md_path: Path, skill_name: str) -> SkillDefinition:
        """Parse SKILL.md to extract structured skill definition"""
        content = md_path.read_text(encoding='utf-8')
        
        # Extract YAML frontmatter if present
        metadata = {}
        description = ""
        parameters = {}
        energy_cost = 1.0  # Default cost
        
        # Simple parser for the structured format
        lines = content.split('\n')
        in_yaml = False
        yaml_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Handle YAML frontmatter
            if line == '---' and not in_yaml:
                in_yaml = True
                continue
            elif line == '---' and in_yaml:
                in_yaml = False
                # Parse YAML
                try:
                    yaml_content = '\n'.join(yaml_lines)
                    metadata = yaml.safe_load(yaml_content) or {}
                except:
                    pass
                continue
                
            if in_yaml:
                yaml_lines.append(line)
                continue
                
            # Extract description (first substantial paragraph)
            if line and not description and not line.startswith('#') and not line.startswith('|'):
                description = line
                
            # Extract parameters table
            if '| Parameter' in line or '| Param' in line:
                # Parse parameter table
                param_section = []
                for param_line in lines[lines.index(line):]:
                    if param_line.strip().startswith('|') and '---' not in param_line:
                        param_section.append(param_line)
                    elif param_section and not param_line.strip().startswith('|'):
                        break
                        
                parameters = self._parse_parameters_table(param_section)
                
        # Determine category and cost based on skill type
        category = self._classify_skill(skill_name, metadata, description)
        energy_cost = self._calculate_energy_cost(category, parameters)
        
        # Extract intent matching patterns
        intent_match = self._extract_intent_patterns(skill_name, description, metadata)
        
        return SkillDefinition(
            name=skill_name,
            description=description or f"OpenClaw skill: {skill_name}",
            category=category,
            intent_match=intent_match,
            energy_cost=energy_cost,
            parameters=parameters,
            metadata=metadata
        )
    
    def _parse_parameters_table(self, table_lines: List[str]) -> Dict[str, Any]:
        """Parse markdown table of parameters"""
        params = {}
        if len(table_lines) < 3:  # Need header, separator, and at least one row
            return params
            
        # Skip header and separator
        for line in table_lines[2:]:
            parts = [part.strip() for part in line.split('|')[1:-1]]  # Remove outer pipes
            if len(parts) >= 2:
                param_name = parts[0].strip('`*')
                param_desc = parts[1] if len(parts) > 1 else ""
                params[param_name] = {"description": param_desc}
                
        return params
    
    def _classify_skill(self, name: str, metadata: Dict, description: str) -> str:
        """Classify skill into categories for energy cost calculation"""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        # High-level categorization
        if any(keyword in name_lower for keyword in ['coding', 'code', 'program', 'dev']):
            return "development"
        elif any(keyword in name_lower for keyword in ['github', 'git', 'repo']):
            return "version_control"
        elif any(keyword in name_lower for keyword in ['browser', 'web', 'scrape']):
            return "web_browsing"
        elif any(keyword in name_lower for keyword in ['shell', 'cli', 'terminal']):
            return "system_execution"
        elif any(keyword in name_lower for keyword in ['chat', 'discord', 'slack', 'telegram']):
            return "communication"
        elif any(keyword in name_lower for keyword in ['file', 'fs', 'filesystem']):
            return "file_operations"
        elif any(keyword in name_lower for keyword in ['search', 'find', 'lookup']):
            return "information_retrieval"
        else:
            return "general_tool"
    
    def _calculate_energy_cost(self, category: str, parameters: Dict) -> float:
        """Calculate energy cost - lower cost skills are preferred over hallucinations"""
        base_costs = {
            "system_execution": 0.1,      # Very cheap - direct system calls
            "file_operations": 0.2,       # Cheap - local file operations
            "web_browsing": 0.3,          # Moderate - network requests
            "information_retrieval": 0.4, # Moderate - search operations
            "communication": 0.5,         # Higher - external service calls
            "version_control": 0.6,       # Higher - git operations
            "development": 0.8,           # Expensive - coding tasks
            "general_tool": 0.5           # Default moderate cost
        }
        
        cost = base_costs.get(category, 0.5)
        
        # Adjust based on complexity
        if len(parameters) > 5:
            cost += 0.2  # More complex = higher cost
        if any('background' in param.lower() for param in parameters):
            cost += 0.3  # Background processes are expensive
            
        return round(cost, 2)
    
    def _extract_intent_patterns(self, name: str, description: str, metadata: Dict) -> List[str]:
        """Extract semantic patterns for intent matching"""
        patterns = []
        
        # From skill name
        patterns.extend(name.split('-'))
        patterns.extend(name.split('_'))
        
        # From description keywords
        desc_words = description.lower().split()
        key_verbs = ['manage', 'create', 'edit', 'delete', 'search', 'find', 'run', 'execute']
        key_nouns = ['file', 'code', 'task', 'project', 'document', 'data', 'user', 'system']
        
        patterns.extend([word for word in desc_words if word in key_verbs + key_nouns])
        
        # From metadata if available
        if 'openclaw' in metadata and 'emoji' in metadata['openclaw']:
            emoji = metadata['openclaw']['emoji']
            patterns.append(emoji)
            
        return list(set(patterns))  # Remove duplicates
    
    def _index_skill_intents(self, skill: SkillDefinition):
        """Build reverse index for fast intent->skill lookup"""
        for pattern in skill.intent_match:
            if pattern not in self.skill_index:
                self.skill_index[pattern] = []
            self.skill_index[pattern].append(skill.name)
    
    def get_available_skills(self) -> List[str]:
        """Return list of all discovered skill names"""
        return list(self.discovered_skills.keys())
    
    def find_matching_skills(self, intent_description: str) -> List[SkillDefinition]:
        """
        Find skills that match an intent description.
        Used by the planner to prevent hallucination.
        """
        matches = []
        intent_lower = intent_description.lower()
        
        # Direct pattern matching
        for pattern, skill_names in self.skill_index.items():
            if pattern.lower() in intent_lower:
                for skill_name in skill_names:
                    if skill_name in self.discovered_skills:
                        matches.append(self.discovered_skills[skill_name])
        
        # Fuzzy matching for broader concepts
        broad_matches = self._fuzzy_match_intent(intent_lower)
        matches.extend(broad_matches)
        
        # Remove duplicates and sort by energy cost
        unique_matches = []
        seen = set()
        for skill in matches:
            if skill.name not in seen:
                unique_matches.append(skill)
                seen.add(skill.name)
                
        return sorted(unique_matches, key=lambda s: s.energy_cost)
    
    def _fuzzy_match_intent(self, intent: str) -> List[SkillDefinition]:
        """Broad semantic matching for intent classification"""
        matches = []
        
        # Category-based matching
        category_keywords = {
            "development": ["code", "program", "develop", "build", "compile"],
            "web_browsing": ["browse", "search web", "scrape", "crawl"],
            "system_execution": ["run", "execute", "command", "shell"],
            "file_operations": ["file", "read", "write", "move", "copy"],
            "communication": ["message", "chat", "send", "communicate"],
            "version_control": ["git", "commit", "branch", "push", "pull"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in intent for keyword in keywords):
                # Find skills in this category
                for skill in self.discovered_skills.values():
                    if skill.category == category:
                        matches.append(skill)
                        
        return matches
    
    def to_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert discovered skills to IPPOC Tool definitions.
        This gets injected into the orchestrator.
        """
        tool_defs = {}
        
        for skill_name, skill in self.discovered_skills.items():
            tool_defs[f"openclaw_{skill_name}"] = {
                "name": f"openclaw_{skill_name}",
                "domain": "body",  # All OpenClaw skills are body tools
                "description": skill.description,
                "energy_cost": skill.energy_cost,
                "parameters": list(skill.parameters.keys()),
                "skill_ref": skill_name,  # Reference back to original skill
                "category": skill.category
            }
            
        return tool_defs
    
    def export_proprioception_map(self, output_path: str = "data/proprioception_map.json"):
        """Export the complete proprioception map for debugging"""
        import json
        from pathlib import Path
        
        map_data = {
            "skills": {name: {
                "description": skill.description,
                "category": skill.category,
                "energy_cost": skill.energy_cost,
                "parameters": skill.parameters,
                "intent_match": skill.intent_match
            } for name, skill in self.discovered_skills.items()},
            "index": self.skill_index,
            "generated_at": __import__('datetime').datetime.now().isoformat()
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(map_data, f, indent=2)
            
        print(f"[Proprioception] Map exported to {output_path}")

# Global scanner instance
_scanner: Optional[ProprioceptionScanner] = None

def get_scanner() -> ProprioceptionScanner:
    global _scanner
    if _scanner is None:
        _scanner = ProprioceptionScanner()
    return _scanner

async def scan_and_register_skills():
    """
    Bootstrap function called during system startup.
    Discovers skills and registers them with the orchestrator.
    """
    scanner = get_scanner()
    skills = await scanner.scan_skills()
    
    # Export for debugging
    scanner.export_proprioception_map()
    
    return skills