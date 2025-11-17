# src/core/decorators.py
from typing import Type, Callable
from .registry import registry

def register_audioutil() -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        registry.register_audioutil(cls)
        return cls
    return decorator

def register_task() -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        registry.register_task(cls)
        return cls
    return decorator

def register_processor() -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        registry.register_processor(cls)
        return cls
    return decorator

def register_stage(stage_type) -> Callable[[Type], Type]:
    def decorator(cls: Type) -> Type:
        # optional: allow custom stage classes
        registry.register_stage(getattr(cls, "name", cls.__name__).lower(), {"stage_type": stage_type, "description": getattr(cls, "description", None)})
        return cls
    return decorator
