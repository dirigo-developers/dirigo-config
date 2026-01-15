from importlib.metadata import PackageNotFoundError, version

CONFIGURATOR_DIST_NAME = "dirigo-config"


def configurator_version() -> str:
    """Return the installed version of the configurator package."""
    return version(CONFIGURATOR_DIST_NAME)


def generated_by_string() -> str:
    """
    Human-readable provenance string.

    Example:
        "dirigo-config 0.1.0"
    """
    try:
        v = configurator_version()
        return f"{CONFIGURATOR_DIST_NAME} {v}"
    except PackageNotFoundError:
        # if this package is not installed yet
        return f"{CONFIGURATOR_DIST_NAME} (uninstalled)"
    