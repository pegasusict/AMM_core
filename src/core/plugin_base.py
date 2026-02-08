from abc import ABC
from typing import ClassVar, Optional
import re

from .enums import PluginType, StageType, TaskType
from Singletons import Logger
from config import Config


class PluginBase(ABC):
    """Base class for all AMM plugins."""

    plugin_type: ClassVar[Optional[PluginType]] = None
    name: ClassVar[Optional[str]] = None
    stage_type: ClassVar[Optional[StageType]] = None
    stage_name: ClassVar[Optional[str]] = None
    task_type: ClassVar[Optional[TaskType]] = None
    description: ClassVar[Optional[str]] = None
    version: ClassVar[Optional[str]] = None
    author: ClassVar[Optional[str]] = None
    depends: ClassVar[list[str]] = []
    exclusive: ClassVar[Optional[bool]] = None
    heavy_io: ClassVar[Optional[bool]] = None


    _name_filter = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")
    _description_filter = re.compile(r"^[a-zA-Z ][a-zA-Z0-9_ .,!?]*$")
    _version_filter = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

    def __init__(self) -> None:
        self.config = Config.get_sync()
        self.logger = Logger()

    @classmethod
    def _validate_classvars(cls) -> None:
        """Validates all ClassVar fields. Raises ValueError with helpful message."""
        errors:list[str] = []
        if not cls._verify_plugin_type():
            errors.append("plugin_type must be a PluginType") # pyright: ignore[reportUnknownMemberType]
        if not cls._verify_name_var(cls.name):
            errors.append("name must be a valid identifier (see name rules)") # pyright: ignore[reportUnknownMemberType]
        if not cls._verify_description_var(cls.description):
            errors.append("description invalid or missing") # pyright: ignore[reportUnknownMemberType]
        if not cls._verify_description_var(cls.author):
            errors.append("author invalid or missing") # pyright: ignore[reportUnknownMemberType]
        if not cls._verify_version():
            errors.append("version must follow semver X.Y.Z") # pyright: ignore[reportUnknownMemberType]
        dep_ok, dep_err = cls._verify_depends()
        if not dep_ok:
            errors.append(f"depends invalid: {dep_err}") # pyright: ignore[reportUnknownMemberType]
        if cls.plugin_type == PluginType.PROCESSOR or cls.plugin_type == PluginType.TASK:
            if not cls._verify_task_type():
                errors.append("Plugin must define a valid TaskType") # pyright: ignore[reportUnknownMemberType]
            if not cls._validate_bool(cls.exclusive):
                errors.append("exclusive must be a boolean") # pyright: ignore[reportUnknownMemberType]
            if not cls._validate_bool(cls.heavy_io):
                errors.append("heavy_io must be a boolean") # pyright: ignore[reportUnknownMemberType]
        if cls.plugin_type == PluginType.TASK:
            if not cls._verify_name_var(cls.stage_name):
                errors.append("TASK plugin must define a valid stage_name") # pyright: ignore[reportUnknownMemberType]
            if not cls._verify_stage_type():
                errors.append("TASK plugin must define a valid StageType") # pyright: ignore[reportUnknownMemberType]

        if errors:
            raise ValueError(f"Plugin class validation failed for {cls.__name__}: " + "; ".join(errors))

    @classmethod
    def _validate_bool(cls, var: object) -> bool:
        """validates wether a variable is of type boolean."""
        return isinstance(var, bool)


    @classmethod
    def _verify_depends(cls) -> tuple[bool, str]:
        """Validates depends: must be a list of valid name strings (or empty)."""
        if cls.plugin_type == PluginType.TASK or cls.plugin_type is PluginType.PROCESSOR:
            if not isinstance(cls.depends, list): # type: ignore
                return False, "depends must be a list"
            for item in cls.depends:
                if not isinstance(item, str) or not cls._name_filter.match(item): # type: ignore
                    return False, f"invalid dependency name: {item!r}"
        return True, ""

    @classmethod
    def _verify_plugin_type(cls) -> bool:
        """Validates PluginType."""
        return isinstance(cls.plugin_type, PluginType)

    @classmethod
    def _verify_task_type(cls) -> bool:
        """Validates TaskType."""
        if cls.plugin_type == PluginType.TASK:
            return isinstance(cls.task_type, TaskType)
        return True

    @classmethod
    def _verify_stage_type(cls) -> bool:
        """Validates StageType."""
        if cls.plugin_type == PluginType.TASK:
            return isinstance(cls.stage_type, StageType)
        return True

    @classmethod
    def _verify_name_var(cls, var: Optional[str]) -> bool:
        """Validates name or given variable against name filter.
        e.g. stage_name, depends.item"""
        if not isinstance(var, str):
            return False
        return cls._name_filter.match(var) is not None

    @classmethod
    def _verify_description_var(cls, var: Optional[str]) -> bool:
        """Validates description or given variable against description filter.
        e.g. author"""
        if not isinstance(var, str):
            return False
        return cls._description_filter.match(var) is not None

    @classmethod
    def _verify_version(cls) -> bool:
        """Validates version against version filter."""
        return cls._version_filter.match(cls.version) is not None # type: ignore
