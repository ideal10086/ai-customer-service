import importlib
import pkgutil
import inspect

from atguigu.task.action.base import Action
from atguigu.task.action.builtin.action_listen import ActionListen
from atguigu.task.action.builtin.action_response import ActionResponse
from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.runner import ActionRunner


def register_builtin_actions(action_runner:ActionRunner):
    action_runner.registry.register(ActionResponse())
    action_runner.registry.register(ActionListen())


def register_custom_actions(action_runner:ActionRunner):
    # 1.扫描包
    package = importlib.import_module("atguigu.task.action.custom")
    # 2.遍历包下的所有模块
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__, prefix=f"{package.__name__}."):
        if is_pkg:
            continue
        # 3.导入模块
        module = importlib.import_module(module_name)
        # 4.遍历模块下的所有类
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # 5.过滤掉非Action类
            if not issubclass(obj, Action) or obj is Action:
                continue
            # 6.过滤掉非当前模块的类
            if obj.__module__ != module.__name__:
                continue
            # 7.注册Action
            action_runner.registry.register(obj())


def build_action_runner() -> ActionRunner:
    action_runner = ActionRunner(ActionRegistry())
    # 注册内置Action
    register_builtin_actions(action_runner)
    # 注册用户自定义Action
    register_custom_actions(action_runner)
    return action_runner
