"""
linter.py

Provides pre-conversion analysis for Scratch projects.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class Linter:
    """
    Analyzes a Scratch project to identify potential issues and provide statistics.
    """

    def __init__(self, project_json: Dict[str, Any]):
        self.project_json = project_json
        self.results = {
            "stats": {
                "targets": 0,
                "blocks": 0,
                "variables": 0,
                "lists": 0,
                "costumes": 0,
                "sounds": 0
            },
            "warnings": [],
            "extensions": []
        }

    def analyze(self) -> Dict[str, Any]:
        """Runs the full analysis and returns the results."""
        if not 'targets' in self.project_json:
            return self.results

        self.results["extensions"] = self.project_json.get('extensions', [])
        
        for target in self.project_json['targets']:
            self._analyze_target(target)

        self._check_project_wide()
        
        return self.results

    def _analyze_target(self, target: Dict[str, Any]):
        """Analyzes a single target (Sprite or Stage)."""
        self.results["stats"]["targets"] += 1
        self.results["stats"]["variables"] += len(target.get('variables', {}))
        self.results["stats"]["lists"] += len(target.get('lists', {}))
        self.results["stats"]["costumes"] += len(target.get('costumes', []))
        self.results["stats"]["sounds"] += len(target.get('sounds', []))

        blocks = target.get('blocks', {})
        self.results["stats"]["blocks"] += len(blocks)

        for block_id, block in blocks.items():
            if not isinstance(block, dict):
                continue
            self._analyze_block(block, target['name'])

    def _analyze_block(self, block: Dict[str, Any], target_name: str):
        """Analyzes a single block for potential issues."""
        opcode = block.get('opcode', '')

        # Warn about potentially slow loops
        if opcode in ('control_forever', 'control_repeat', 'control_repeat_until'):
            # Check if it's an empty loop or very simple loop
            pass # Potential future check: empty loops that might hang without yield

        # Warn about unsupported or problematic blocks
        if opcode == 'videoSensing_whenMotionGreaterThan':
            self.results["warnings"].append({
                "type": "compatibility",
                "message": f"Sprite '{target_name}' uses Video Sensing which has limited support.",
                "target": target_name
            })
        
        if opcode.startswith('music_'):
             self.results["warnings"].append({
                "type": "compatibility",
                "message": f"Sprite '{target_name}' uses Music blocks which have limited support.",
                "target": target_name
            })

    def _check_project_wide(self):
        """Checks for project-wide issues."""
        if self.results["stats"]["blocks"] > 5000:
             self.results["warnings"].append({
                "type": "performance",
                "message": "Project has a large number of blocks (>5000), which may impact conversion time and performance."
            })
        
        for ext in self.results["extensions"]:
            if ext not in ('pen',): # List known well-supported extensions
                self.results["warnings"].append({
                    "type": "extension",
                    "message": f"Project uses extension '{ext}' which may not be fully supported."
                })

def lint_project(project_json: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to lint a project."""
    linter = Linter(project_json)
    return linter.analyze()
