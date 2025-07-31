# guardrails/action_guardrail.py

import yaml
import logging
from typing import Dict, Any

# --- Constants ---
RULES_FILE_PATH = "config/rules.yaml"

class ActionGuardrail:
    """
    A guardrail to validate agent actions against a predefined set of rules.
    """
    def __init__(self, logger: logging.Logger):
        """
        Initializes the ActionGuardrail by loading the rules from the YAML file.
        """
        self.logger = logger
        try:
            with open(RULES_FILE_PATH, 'r') as f:
                self.rules = yaml.safe_load(f)
            self.logger.info(f"Successfully loaded action rules from {RULES_FILE_PATH}")
        except FileNotFoundError:
            self.logger.error(f"CRITICAL: Rules file not found at {RULES_FILE_PATH}. Action guardrail will block all actions.")
            self.rules = {} # Start with empty rules to prevent crashes
        except yaml.YAMLError as e:
            self.logger.error(f"CRITICAL: Error parsing YAML rules file: {e}. Action guardrail will block all actions.")
            self.rules = {}

    def is_action_illegal(self, action: Dict[str, Any]) -> bool:
        """
        Checks if a proposed agent action violates any of the loaded rules.

        Args:
            action (Dict[str, Any]): A dictionary describing the action,
                                     e.g., {'tool': 'file_reader', 'parameters': {'path': '/etc/passwd'}}

        Returns:
            bool: True if the action is illegal, False otherwise.
        """
        tool_name = action.get("tool")
        parameters = action.get("parameters", {})

        if not tool_name:
            self.logger.warning("Action blocked: 'tool' not specified in the action.")
            return True

        # 1. Check if the tool is in the overall list of allowed tools
        allowed_tools = self.rules.get("allowed_tools", [])
        if tool_name not in allowed_tools:
            self.logger.warning(f"Action blocked: Tool '{tool_name}' is not in the list of allowed tools.")
            return True

        # 2. Check for tool-specific rules
        tool_rules = self.rules.get("tool_rules", {}).get(tool_name)
        if not tool_rules:
            # If no specific rules exist for this tool, and it was in the allowed list, it's permitted.
            self.logger.info(f"Action permitted: Tool '{tool_name}' is allowed and has no specific rules.")
            return False

        # --- Apply specific rules for known tools ---

        # Rule for 'file_reader'
        if tool_name == "file_reader":
            return self._validate_file_reader(parameters, tool_rules)

        # Rule for 'database_query'
        if tool_name == "database_query":
            return self._validate_database_query(parameters, tool_rules)

        # If we reach here, the tool is allowed and has passed all its specific checks
        self.logger.info(f"Action permitted: Tool '{tool_name}' passed all specific rule checks.")
        return False

    def _validate_file_reader(self, parameters: Dict[str, Any], rules: Dict[str, Any]) -> bool:
        """Validates actions for the 'file_reader' tool."""
        filepath = parameters.get("path")
        if not filepath:
            self.logger.warning("Action 'file_reader' blocked: Missing 'path' parameter.")
            return True

        # Check for disallowed file extensions
        disallowed_extensions = rules.get("disallowed_extensions", [])
        if any(filepath.endswith(ext) for ext in disallowed_extensions):
            self.logger.warning(f"Action 'file_reader' blocked: Access to file with disallowed extension '{filepath}'.")
            return True

        # Check if the path is within an allowed directory
        allowed_paths = rules.get("allowed_paths", [])
        if not any(filepath.startswith(p) for p in allowed_paths):
            self.logger.warning(f"Action 'file_reader' blocked: Path '{filepath}' is not in an allowed directory.")
            return True

        return False # Path is valid

    def _validate_database_query(self, parameters: Dict[str, Any], rules: Dict[str, Any]) -> bool:
        """Validates actions for the 'database_query' tool."""
        query = parameters.get("query", "").upper() # Convert to uppercase for case-insensitive check
        if not query:
            self.logger.warning("Action 'database_query' blocked: Missing 'query' parameter.")
            return True

        # Check for forbidden SQL keywords
        forbidden_keywords = rules.get("forbidden_keywords", [])
        if any(keyword in query for keyword in forbidden_keywords):
            self.logger.warning(f"Action 'database_query' blocked: Query contains a forbidden keyword.")
            return True

        return False # Query is valid

# --- Example Usage for direct testing ---
if __name__ == "__main__":
    from utils.logger import setup_logger
    test_logger = setup_logger()

    guardrail = ActionGuardrail(logger=test_logger)

    print("\n--- [Testing Action Guardrail] ---")

    # Test cases
    legal_action_1 = {"tool": "web_search", "parameters": {"query": "latest AI news"}}
    legal_action_2 = {"tool": "file_reader", "parameters": {"path": "/data/public/report.txt"}}
    
    illegal_action_tool = {"tool": "shell_executor", "parameters": {"command": "rm -rf /"}}
    illegal_action_path = {"tool": "file_reader", "parameters": {"path": "/etc/shadow"}}
    illegal_action_ext = {"tool": "file_reader", "parameters": {"path": "/data/public/config.yaml"}}
    illegal_action_sql = {"tool": "database_query", "parameters": {"query": "DROP TABLE users;"}}

    print(f"Test 1 (Legal Search): {legal_action_1}\n>>> Illegal? {guardrail.is_action_illegal(legal_action_1)}\n")
    print(f"Test 2 (Legal File Read): {legal_action_2}\n>>> Illegal? {guardrail.is_action_illegal(legal_action_2)}\n")
    print(f"Test 3 (Disallowed Tool): {illegal_action_tool}\n>>> Illegal? {guardrail.is_action_illegal(illegal_action_tool)}\n")
    print(f"Test 4 (Disallowed Path): {illegal_action_path}\n>>> Illegal? {guardrail.is_action_illegal(illegal_action_path)}\n")
    print(f"Test 5 (Disallowed Extension): {illegal_action_ext}\n>>> Illegal? {guardrail.is_action_illegal(illegal_action_ext)}\n")
    print(f"Test 6 (Disallowed SQL): {illegal_action_sql}\n>>> Illegal? {guardrail.is_action_illegal(illegal_action_sql)}\n")