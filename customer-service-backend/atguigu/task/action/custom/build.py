import importlib
import pkgutil

from atguigu.task.action.registry import ActionRegistry


def register_custom_actions(registry:ActionRegistry):
    package = importlib.import_module("atguigu.task.action.custom")
    for _,module_name,is_pkg in pkgutil.iter_modules(package.__path__,prefix=f"{package.__name__}."):
        if is_pkg:
            continue
        module = importlib.import_module(f"{module_name}")
        pass
