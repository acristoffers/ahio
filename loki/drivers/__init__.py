import importlib.machinery
import os
import sys


def __locate_driver_named(name):
    """Searchs __modules for a driver named @arg name.

    @returns the package for driver @arg name or None if one can't be found.
    """
    ms = [d for d in __modules if d.LokiDriverInfo.NAME == name]
    if not ms:
        return None
    return ms[0]


def new_driver_object(name):
    """Instantiates a new object of the named driver.

    The API used by the returned object can be seen in
    `loki.abstract_driver.AbstractDriver`

    @returns a Driver object from the required type of None if it's not
    available
    """
    driver = __locate_driver_named(name)
    return driver.Driver() if driver else None


def driver_info(name):
    """Returns driver metadata.

    Returns a class which static properties contains metadata from the
    driver, such as name and availability.

    @returns a subclass from `loki.abstract_driver.AbstractLokiDriverInfo` with
    metadata from the driver.
    """
    driver = __locate_driver_named(name)
    return driver.LokiDriverInfo if driver else None


def __load_driver(name):
    """Tries to load the driver named @arg name.

    A driver is considered valid if it has a LokiDriverInfo object. It should
    however implement all APIs described in `loki.abstract_driver`, as they'll
    be needed to use the driver.

    @returns the driver package, or False if it failed.
    """
    try:
        mod_name = 'loki.drivers.' + name.replace('.py', '')
        driver_path = __modules_path + '/' + name
        loader = importlib.machinery.SourceFileLoader(mod_name, driver_path)
        driver = loader.load_module()
        return driver if hasattr(driver, 'LokiDriverInfo') else False
    except Exception:
        return False

# path to the drivers folder
__modules_path = os.path.dirname(os.path.realpath(__file__))
# tries to load every file in the drivers folder
__modules = [__load_driver(driver) for driver in os.listdir(__modules_path)]
# filters out the False elements, leaving only valid drivers
__modules = [d for d in __modules if d]
# all installed drivers, even if not usable in this platform
installed = [driver.LokiDriverInfo.NAME for driver in __modules]
# only installed drivers that are available in this platform
available = [d.LokiDriverInfo.NAME
             for d in __modules
             if d.LokiDriverInfo.AVAILABLE]
