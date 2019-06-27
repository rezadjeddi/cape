"""
:mod:`pyUS.options.Report`: pyUS Report Options
===================================================

This module provides options for creating automated reports for pyUS results.
Although there are some subfigure types that are unique to pyUS, all of the
methods in the :class:`pyUS.options.Report.Report` class are inherited from
:mod:`cape` version.

See the :ref:`JSON Report <cape-json-Report>` section for the list of available
figures and subfigures (along with other options).

:See Also:
    * :mod:`cape.options.Report`
    * :mod:`cape.report`
    * :mod:`pyUS.report`
"""


# Import options-specific utilities
from .util import rc0, getel

# Import template module
import cape.options.Report

# Class for Report settings
class Report(cape.options.Report):
    """Dictionary-based interface for automated reports
    
    :Call:
        >>> opts = Report(**kw)
    :Versions:
        * 2015-09-28 ``@ddalle``: Subclassed to CAPE
    """
    
    pass
# class Report


