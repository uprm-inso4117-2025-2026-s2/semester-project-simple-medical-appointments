from pathlib import Path
from pytest_bdd import scenarios

scenarios(str(Path(__file__).parent / "features" / "admin_operations.feature"))
scenarios(str(Path(__file__).parent / "features" / "access_control.feature"))
