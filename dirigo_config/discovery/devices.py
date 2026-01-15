from typing import Dict, List

from importlib.metadata import entry_points



DIRIGO_DEVICE_PREFIX = "dirigo.devices."


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
    eps = entry_points()
    # modern API
    if hasattr(eps, "select"):
        items = list(eps.select(group=group))
    else:
        # older fallback
        items = list(eps.get(group, []))  # type: ignore[attr-defined]
    return sorted({ep.name for ep in items})

