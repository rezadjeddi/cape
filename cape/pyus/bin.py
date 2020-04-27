#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
:mod:`cape.pyus.bin`: US3D binary interface module
=====================================================

This module provides an interface to the various US3D executables and
other command-line utilities from :mod:`cape.bin`.  However, due to some
of the subtleties of how the main US3D executables are called,
:func:`cape.pyus.case.RunPhase` constructs the commands to run US3D
from :mod:`cape.pyfun.cmd` locally and runs them using
:func:`cape.bin.callf`.

:See also:
    * :mod:`cape.cfdx.bin`
    * :mod:`cape.cfdx.cmd`
    * :mod:`cape.pyus.cmd`

"""

# CAPE modules
import cape.cfdx.bin as cbin

# Local modules
from . import cmd


# Execute ``us3d-prepar``
def us3d_prepar(opts, i=0, **kw):
    r"""Run US3D executable ``us3d-prepar``
    
    :Call:
        >>> ierr = bin.us3d_prepar(opts, i=0)
        >>> ierr = bin.us3d_prepar(**kw)
    :Inputs:
        *opts*: :class:`cape.pyus.options.Options`
            Global or "RunControl" pyUS options
        *i*: :class:`int`
            Phase number
        *grid*: {``"pyus.case"``} | :class:`str`
            Name of input Fluent mesh
        *output*: {``None``} | :class:`str`
            Name of output HDF5 grid (``"grid.h5"``)
        *conn*: {``None``} | :class:`str`
            Name of output connectivity file (``"conn.h5"``)
    :Outputs:
        *ierr*: :class:`list`\ [:class:`str`]
            Exit statys
    :Versions:
        * 2020-04-20 ``@ddalle``: First version
    """
    # Get command
    cmdi = cmd.us3d_prepar(opts, i=i, **kw)
    # Get verbosity option
    if opts:
        # Specified from "RunControl" section
        v = opts.get_Verbose(i)
    else:
        # Default is ``True``
        v = True
    # Check override
    v = kw.get("v", v)
    # Execute the command
    return cbin.callf(cmdi, f="us3d-prepar.out", v=v)


# Execute ``us3d-genbc``
def us3d_genbc(opts, i=0, **kw):
    r"""Run US3D executable ``us3d-genbc``
    
    :Call:
        >>> cmdi = cmd.us3d_genbc(opts, i=0)
        >>> cmdi = cmd.us3d_genbc(**kw)
    :Inputs:
        *opts*: :class:`cape.pyus.options.Options`
            Global or "RunControl" pyUS options
        *i*: :class:`int`
            Phase number
        *grid*: {``"grid.h5"``} | :class:`str`
            Name of prepared US3D grid
    :Outputs:
        *cmdi*: :class:`list`\ [:class:`str`]
            Command split into a list of strings
    :Versions:
        * 20120-04-27 ``@ddalle``: First version
    """
    # Get command
    cmdi = cmd.us3d_genbc(opts, i=i, **kw)
    # Get verbosity option
    if opts:
        # Specified from "RunControl" section
        v = opts.get_Verbose(i)
    else:
        # Default is ``True``
        v = True
    # Check override
    v = kw.get("v", v)
    # Execute the command
    return cbin.callf(cmdi, f="us3d-genbc.out", v=v)
    
