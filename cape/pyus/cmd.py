#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
:mod:`cape.pyus.cmd`: Create commands for US3D executables
=============================================================

This module creates system commands as lists of strings for executable
binaries or scripts for FUN3D.  The main US3D executables are

    * ``us3d-prepar``: Convert Fluent grid to proper format
    * ``us3d-genbc``: Generate boundary condition inputs from grid
    * ``us3d``: Execute US3D flow solver

Commands are created in the form of a list of strings.  This is the
format used in the built-in module :mod:`subprocess` and also with
:func:`cape.bin.calli`. As a very simple example, the system command
``"ls -lh"`` becomes the list ``["ls", "-lh"]``.

These commands also include prefixes such as ``mpiexec`` if necessary.
The decision to use ``mpiexec`` or not is based on the keyword input
``"MPI"``.  For example, two versions of the command returned by
:func:`us3d` could be

    .. code-block:: python
    
        ["mpiexec", "-np", "240", "us3d"]
        ["mpiexec", "-np", "1", "us3d-prepar" "--grid", "pyus.cas"]

:See also:
    * :mod:`cape.cfdx.cmd`
    * :mod:`cape.cfdx.bin`
    * :mod:`cape.pyus.bin`
    * :mod:`cape.pyus.options.runControl`

"""

# Options for the binaries
from .options import runControl, getel


# Function to create ``nodet`` or ``nodet_mpi`` command
def nodet(opts=None, i=0, **kw):
    r"""Interface to FUN3D binary ``nodet`` or ``nodet_mpi``
    
    :Call:
        >>> cmdi = cmd.nodet(opts, i=0)
        >>> cmdi = cmd.nodet(**kw)
    :Inputs:
        *opts*: :class:`pyFun.options.Options`
            Global pyFun options interface or "RunControl" interface
        *i*: :class:`int`
            Phase number
        *animation_freq*: :class:`int`
            Output frequency
    :Outputs:
        *cmdi*: :class:`list` (:class:`str`)
            Command split into a list of strings
    :Versions:
        * 2015-11-24 ``@ddalle``: First version
    """
    # Check for options input
    if opts is not None:
        # Get values for run configuration
        n_mpi  = opts.get_MPI(i)
        nProc  = opts.get_nProc(i)
        mpicmd = opts.get_mpicmd(i)
        # Get dictionary of command-line inputs
        if "nodet" in opts:
            # pyFun.options.runControl.RunControl instance
            cli_nodet = opts["nodet"]
        elif "RunControl" in opts and "nodet" in opts["RunControl"]:
            # pyFun.options.Options instance
            cli_nodet = opts["RunControl"]["nodet"]
        else:
            # No command-line arguments
            cli_nodet = {}
    else:
        # Get values from keyword arguments
        n_mpi  = kw.get("MPI", False)
        nProc  = kw.get("nProc", 1)
        mpicmd = kw.get("mpicmd", "mpiexec")
        # Form other command-line argument dictionary
        cli_nodet = kw
        # Remove above options
        if "MPI"    in cli_nodet: del cli_nodet["MPI"]
        if "nProc"  in cli_nodet: del cli_nodet["nProc"]
        if "mpicmd" in cli_nodet: del cli_nodet["mpicmd"]
    # Form the initial command.
    if n_mpi:
        # Use the ``nodet_mpi`` command
        cmdi = [mpicmd, '-np', str(nProc), 'nodet_mpi']
    else:
        # Use the serial ``nodet`` command
        cmdi = ['nodet']
    # Check for "--adapt" flag
    if kw.get("adapt"):
        # That should be the only command-line argument
        cmdi.append("--adapt")
        return cmdi
    # Loop through command-line inputs
    for k in cli_nodet:
        # Get the value
        v = cli_nodet[k]
        # Check the type
        if v == True:
            # Just an option with no value
            cmdi.append('--'+k)
        elif v == False or v is None:
            # Do not use.
            pass
        else:
            # Select option for this phase
            vi = getel(v, i)
            # Append the option and value
            cmdi.append('--'+k)
            cmdi.append(str(vi))
    # Output
    return cmdi


# Function to execute ``us3d-prepar``
def us3d_prepar(opts=None, i=0, **kw):
    r"""Interface to US3D executable ``us3d-prepar``
    
    :Call:
        >>> cmdi = cmd.us3d_prepar(opts, i=0)
        >>> cmdi = cmd.us3d_prepar(**kw)
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
        *cmdi*: :class:`list`\ [:class:`str`]
            Command split into a list of strings
    :Versions:
        * 2016-04-28 ``@ddalle``: First version
    """
    # Check for options input
    if opts is not None:
        # Downselect to "RunControl" section if necessary
        if "RunControl" in opts:
            opts = opts["RunControl"]
        # Downselect to "dual" section if necessary
        if "dual" in opts:
            # Get values for run configuration
            n_mpi  = opts.get_MPI(i)
            mpicmd = opts.get_mpicmd(i)
        else:
            # Use defaults
            n_mpi  = runControl.rc0('MPI')
            mpicmd = runControl.rc0('mpicmd')
    else:
        # Use defaults
        n_mpi  = runControl.rc0('MPI')
        mpicmd = runControl.rc0('mpicmd')
    # Process keyword overrides
    n_mpi  = kw.get('MPI',    n_mpi)
    mpicmd = kw.get('mpicmd', mpicmd)
    # Process CLI options
    grid = "pyus.cas"
    fout = None
    conn = None
    # Process keyword overrides
    grid = kw.get("grid", grid)
    fout = kw.get("output", fout)
    conn = kw.get("conn", conn)
    # Form the initial command
    if n_mpi:
        # Use MPI
        cmdi = [mpicmd, "-np", "1", "us3d-prepar"]
    else:
        # Serial
        cmdi = ["us3d-prepar"]
    # Process known options
    if grid:
        cmdi.extend(["--grid", grid])
    if fout:
        cmdi.extend(["--output", fout])
    if conn:
        cmdi.extend(["--conn", conn])
    # Output
    return cmdi

