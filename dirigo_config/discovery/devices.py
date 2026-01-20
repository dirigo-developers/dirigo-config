from typing import Dict, List
from importlib.metadata import entry_points

from dirigo.hw_interfaces.hw_interface import Device


DIRIGO_DEVICE_PREFIX = "dirigo.devices."


class EntryPointNotFound(LookupError):
    pass


class EntryPointNotUnique(LookupError):
    pass


class EntryPointInvalidType(TypeError):
    pass


def discover_kinds_and_groups() -> Dict[str, str]:
    """
    Discover device kinds from entry point groups that start with 'dirigo.devices.'.

    Returns:
        kind -> group
    Example:
        "digitizer" -> "dirigo.devices.digitizers"
        "line_camera" -> "dirigo.devices.line_cameras"
    """
    eps = entry_points()
    groups = sorted(getattr(eps, "groups", []))

    out: Dict[str, str] = {}
    for g in groups:
        if not g.startswith(DIRIGO_DEVICE_PREFIX):
            continue
        kind = g[len(DIRIGO_DEVICE_PREFIX):]  # e.g. "digitizer"
        out[kind] = g
    return out


def discover_entry_point_names(group: str) -> List[str]:
    """
    Return sorted entry point names for a given group.
    """
    items = list(entry_points().select(group=group))
   
    return sorted({ep.name for ep in items})


def load_device_class(group: str, name: str) -> type[Device]:
    """
    Load the entry point object for (group, name).
    """
    matches = list(entry_points().select(group=group, name=name))

    if not matches:
        raise EntryPointNotFound(f"No entry point found for group={group!r}, name={name!r}")
    
    if len(matches) > 1:
        # Name collisions shouldn't happen within a group, but if they do,
        # you want to fail loudly rather than pick arbitrarily.
        raise EntryPointNotUnique(
            f"Multiple entry points found for group={group!r}, name={name!r}: "
            + ", ".join(repr(ep.value) for ep in matches)
        )
    
    obj = matches[0].load()

    if not isinstance(obj, type):
        raise EntryPointInvalidType(
            f"Entry point {group!r}:{name!r} loaded {type(obj)!r}, expected a class."
        )

    if not issubclass(obj, Device):
        raise EntryPointInvalidType(
            f"Entry point {group!r}:{name!r} loaded {obj.__module__}.{obj.__name__}, "
            f"which is not a subclass of Device."
        )

    return obj