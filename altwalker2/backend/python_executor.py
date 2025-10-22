"""Python Test Executor

Direct test execution without AltWalker dependency.
Loads and executes Python test code.
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TestExecutionException(Exception):
    """Exception raised for test execution errors."""

    pass


class PythonTestExecutor:
    """Executor for Python test code.

    Loads test modules and executes test methods.
    """

    def __init__(self, tests_path: str):
        """Initialize test executor.

        Args:
            tests_path: Path to tests directory or module
        """
        self.tests_path = Path(tests_path)
        self.test_module = None
        self.test_class = None

    def load(self):
        """Load the test module."""
        try:
            # Add tests directory to sys.path
            test_dir = (
                self.tests_path.parent if self.tests_path.is_file() else self.tests_path
            )
            # if str(test_dir) not in sys.path:
            #     sys.path.insert(0, str(test_dir))

            # # Get module name
            # if self.tests_path.is_file():
            #     module_name = self.tests_path.stem
            # else:
            #     # Look for test.py or __init__.py
            #     if (self.tests_path / "test.py").exists():
            #         # Import as "tests.test" where tests is the directory name
            #         module_name = f"{self.tests_path.name}.test"
            #         print(
            #             f"3DEBUG [EXECUTOR]: Found test.py, module name: {module_name}"
            #         )
            #     elif (self.tests_path / "__init__.py").exists():
            #         module_name = self.tests_path.name
            #         print(
            #             f"2DEBUG [EXECUTOR]: Found __init__.py, module name: {module_name}"
            #         )
            #     else:
            #         raise TestExecutionException(
            #             f"1No test module found in {self.tests_path}"
            #         )

            print(f"aDEBUG [EXECUTOR]: test_dir added to sys.path: {test_dir}")
            # print(f"bDEBUG [EXECUTOR]: Attempting to import module: {module_name}")

            # Import module
            # self.test_module = importlib.import_module(module_name)
            # logger.info(f"Loaded test module: {module_name}")

            # Try to find test class (common pattern: ModelName class)
            # Look for classes that might contain test methods
            from backend.test import ModelName

            # for attr_name in dir(self.test_module):
            #     attr = getattr(self.test_module, attr_name)
            # if (
            #     isinstance(attr, type)
            #     and not attr_name.startswith("_")
            #     and attr_name != "TestExecutionException"
            # ):
            self.test_class = ModelName
        # break

        except Exception as e:
            raise TestExecutionException(f"Failed to load tests: {e}")

    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single test step.

        Args:
            step: Step dictionary with name, id, modelName, data, etc.

        Returns:
            Result dictionary with output, data, error, etc.
        """
        step_name = step.get("name", "")
        step_data = step.get("data", {})

        result = {
            "id": step.get("id"),
            "output": "",
            "data": step_data,
        }

        try:
            # Skip fixture steps (beforeStep, afterStep, etc.)
            if step.get("type") == "fixture":
                # Still try to execute if method exists
                pass

            # Find and execute the test method
            if self.test_class:
                # Create instance
                test_instance = self.test_class()

                # Set data if available
                if hasattr(test_instance, "data"):
                    test_instance.data = step_data

                # Execute the method
                if hasattr(test_instance, step_name):
                    method = getattr(test_instance, step_name)
                    method()
                    logger.debug(f"Executed: {step_name}")
                else:
                    logger.warning(f"Method not found: {step_name}")

            elif self.test_module:
                # Try module-level function
                if hasattr(self.test_module, step_name):
                    func = getattr(self.test_module, step_name)
                    func()
                    logger.debug(f"Executed: {step_name}")
                else:
                    logger.warning(f"Function not found: {step_name}")

        except Exception as e:
            logger.error(f"Error executing {step_name}: {e}")
            result["error"] = {
                "message": str(e),
                "trace": "",
            }

        return result

    def kill(self):
        """Cleanup executor resources."""
        # Remove from sys.modules if needed
        if self.test_module and hasattr(self.test_module, "__name__"):
            module_name = self.test_module.__name__
            if module_name in sys.modules:
                del sys.modules[module_name]

        self.test_module = None
        self.test_class = None
