# -*- coding: utf-8; -*-
#
# Copyright (c) 2016 Álan Crístoffer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import importlib.machinery
import os
import sys

# path to the drivers folder
__modules_path = os.path.dirname(os.path.realpath(__file__))
# additional added paths
__modules_path_user = []
# tries to load every file in the drivers folder
__modules = (__load_driver(__modules_path + '/' + driver)
             for driver in os.listdir(__modules_path))
# filters out the False elements, leaving only valid drivers
__modules = (d for d in __modules if d)
# only installed drivers that are available in this platform
__available = None
# counts the number of drivers loaded. The number is appended to driver name
# to avoid collision
__count = 0


def add_path(path):
    global __modules_path_user
    global __modules
    global __available
    __modules_path_user.append(path)
    path = [__modules_path, *__modules_path_user]
    fs = [d + '/' + f for d in path for f in os.listdir(d)]
    __modules = (__load_driver(driver) for driver in fs)
    __modules = (d for d in __modules if d)
    __available = None


def remove_path(path):
    global __modules_path_user
    global __modules
    global __available
    __modules_path_user = [x for x in __modules_path_user if x != path]
    path = [__modules_path, *__modules_path_user]
    fs = [d + '/' + f for d in path for f in os.listdir(d)]
    __modules = (__load_driver(driver) for driver in fs)
    __modules = (d for d in __modules if d)
    __available = None


def clear_path():
    global __modules_path_user
    global __modules
    global __available
    __modules_path_user = []
    fs = [d + '/' + f for d in [__modules_path] for f in os.listdir(d)]
    __modules = (__load_driver(driver) for driver in fs)
    __modules = (d for d in __modules if d)
    __available = None


def available_drivers():
    """Returns a list of available drivers names.
    """
    global __modules
    global __available

    if type(__modules) is not list:
        __modules = list(__modules)

    if not __available:
        __available = [d.ahioDriverInfo.NAME
                       for d in __modules
                       if d.ahioDriverInfo.AVAILABLE]

    return __available


def driver_info(name):
    """Returns driver metadata.

    Returns a class which static properties contains metadata from the
    driver, such as name and availability.

    @returns a subclass from `ahio.abstract_driver.AbstractahioDriverInfo` with
    metadata from the driver.
    """
    driver = __locate_driver_named(name)
    return driver.ahioDriverInfo if driver else None


def new_driver_object(name):
    """Instantiates a new object of the named driver.

    The API used by the returned object can be seen in
    `ahio.abstract_driver.AbstractDriver`

    @returns a Driver object from the required type of None if it's not
    available
    """
    driver = __locate_driver_named(name)
    return driver.Driver() if driver else None


def __load_driver(name):
    """Tries to load the driver named @arg name.

    A driver is considered valid if it has a ahioDriverInfo object. It should
    however implement all APIs described in `ahio.abstract_driver`, as they'll
    be needed to use the driver.

    @returns the driver package, or False if it failed.
    """
    global __count
    try:
        dname = os.path.basename(name).replace('.py', '')
        mod_name = 'ahio.drivers.%s%d' % (dname, __count)
        loader = importlib.machinery.SourceFileLoader(mod_name, name)
        driver = loader.load_module()
        __count += 1
        return driver if hasattr(driver, 'ahioDriverInfo') else False
    except Exception:
        return False


def __locate_driver_named(name):
    """Searchs __modules for a driver named @arg name.

    @returns the package for driver @arg name or None if one can't be found.
    """
    global __modules

    if type(__modules) is not list:
        __modules = list(__modules)

    ms = [d for d in __modules if d.ahioDriverInfo.NAME == name]
    if not ms:
        return None
    return ms[0]
