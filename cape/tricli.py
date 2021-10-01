r"""
:mod:`cape.tricli`: Interfaces to ``.tri`` and related files
==============================================================

This module includes functions to interface with triangulated surface
files and provides interfaces accessible from the command line.

Many of these functions perform conversions, for example
:func:`uh3d2tri` reads a UH3D file and converts it to Cart3D ``.tri``
format.
"""

# Standard library modules
import os
import sys

# Third-party modules
import numpy as np

# Local imprts
from . import argread
from . import text as textutils
from .tri import Tri
from .config import ConfigXML, ConfigMIXSUR, ConfigJSON


# Help message for "uh3d2tri"
HELP_UH3D2TRI = r"""
``cape-uh3d2tri``: Convert UH3D triangulation to Cart3D format
===============================================================

Convert a ``.uh3d`` file to a Cart3D triangulation format.

:Usage:

    .. code-block:: console
    
        $ cape-uh3d2tri UH3D [OPTIONS]
        $ cape-uh3d2tri UH3D TRI [OPTIONS]
        $ cape-uh3d2tri [OPTIONS]

:Inputs:
    * *UH3D*: Name of input '.uh3d' file
    * *TRI*: Name of output '.tri' file
    
:Options:
    -h, --help
        Display this help message and exit
        
    -i UH3D
        Use *UH3D* as input file
        
    -o TRI
        Use *TRI* as name of created output file
       
    -c CONFIGFILE
        Use file *CONFIGFILE* to map component ID numbers; guess type
        based on file name

    --xml XML
        Use file *XML* as config file with XML format

    --json JSON
        Use file *JSON* as JSON-style surface config file

    --mixsur MIXSUR
        Use file *MIXSUR* to label surfaces assuming ``mixsur`` or
        ``usurp`` input file format

    --ascii
        Write *TRI* as an ASCII file (default)
        
    --binary, --bin
        Write *TRI* as an unformatted Fortran binary file
        
    --byteorder BO, --endian BO
        Override system byte order using either 'big' or 'little'
        
    --bytecount PREC
        Use a *PREC* of 4 for single- or 8 for double-precision
        
    --xtol XTOL
        Truncate nodal coordinates within *XTOL* of x=0 plane to zero
        
    --ytol YTOL
        Truncate nodal coordinates within *YTOL* of y=0 plane to zero
        
    --ztol ZTOL
        Truncate nodal coordinates within *ZTOL* of z=0 plane to zero

    --dx DX
        Translate all nodes by *DX* in *x* direction

    --dy DY
        Translate all nodes by *DY* in *y* direction

    --dz DZ
        Translate all nodes by *DZ* in *z* direction
    
If the name of the output file is not specified, it will just add '.tri'
as the extension to the input (deleting '.uh3d' if possible).

:Versions:
    * 2014-06-12 ``@ddalle``: Version 1.0
    * 2015-10-09 ``@ddalle``: Version 1.1
        - Add tolerances and ``Config.xml`` processing
        - Add *dx*, *dy*, *dz* translation options
"""

HELP_TRI2UH3D = r"""
``cape-tri2uh3d``: Convert Cart3D Triangulation to UH3D Format
===================================================================

Convert a Cart3D triangulation ``.tri`` file to a UH3D file.  The most
common purpose for this task is to inspect triangulations with moving
bodies with alternative software such as ANSA.

:Usage:
    .. code-block:: console
    
        $ cape-tri2uh3d TRI [OPTIONS]
        $ cape-tri2uh3d TRI UH3D [OPTIONS]
        $ cape-tri2uh3d -i TRI [-o UH3D] [OPTIONS]

:Inputs:
    * *TRI*: Name of output ``.tri`` file
    * *UH3D*: Name of input ``.uh3d`` file

:Options:
    -h, --help
        Display this help message and exit

    -i TRI
        Use *TRI* as name of created output file

    -o UH3D
        Use *UH3D* as input file
       
    -c CONFIGFILE
        Use file *CONFIGFILE* to map component ID numbers; guess type
        based on file name

    --xml XML
        Use file *XML* as config file with XML format

    --json JSON
        Use file *JSON* as JSON-style surface config file

    --mixsur MIXSUR
        Use file *MIXSUR* to label surfaces assuming ``mixsur`` or
        ``usurp`` input file format

If the name of the output file is not specified, the script will just
add ``.uh3d`` as the extension to the input (deleting ``.tri`` if
possible).

:Versions:
    * 2015-04-17 ``@ddalle``: Version 1.0
    * 2017-04-06 ``@ddalle``: Version 1.1: JSON and MIXSUR config files
"""

# Main function
def Tri2UH3D(*a, **kw):
    r"""Convert a UH3D triangulation file to Cart3D tri format
    
    :Call:
        >>> tri2uh3d(ftri, **kw)
        >>> tri2uh3d(ftri, fuh3d, **kw)
        >>> Tri2UH3D(i=ftri, o=fuh3d, **kw)
    :Inputs:
        *ftri*: :class:`str`
            Name of input file
        *fuh3d*: :class:`str`
            Name of output file
        *c*: :class:`str`
            Surface config file, guess type from file name 
        *json*: {``None``} | :class:`str`
            JSON surface config file 
        *mixsur*: {``None``} | :class:`str`
            MIXSUR/USURP surface config file 
        *xml*: {``None``} | :class:`str`
            XML surface config file
        *h*: ``True`` | {``False``}
            Display help and exit if ``True``
    :Versions:
        * 2015-04-17 ``@ddalle``: Version 1.0
        * 2021-10-01 ``@ddalle``: Version 2.0
    """
    # Get input file name
    ftri = _get_i(*a, **kw)
    # Get output file name
    fuh3d = _get_o(ftri, "tri", "uh3d", **kw)
    # Read TRI file
    tri = Tri(ftri)
    # Read Config file
    cfg = _read_config(*a, **kw)
    # Apply configuration if requested
    if cfg is not None:
        tri.ApplyConfig(cfg)
    # Write the UH3D file
    tri.WriteUH3D(fuh3d)


def uh3d2tri(*a, **kw):
    r"""Convert a UH3D triangulation file to Cart3D ``.tri`` format
    
    :Call:
        >>> uh3d2tri(uh3d, tri, c=None, **kw)
        >>> uh3d2tri(i=uh3d, o=tri, c=None, **kw)
    :Inputs:
        *uh3d*: :class:`str`
            Name of input file
        *tri*: :class:`str`
            Name of output file (defaults to value of *uh3d* but with
            ``.tri`` as the extension in the place of ``.uh3d``)
        *c*: :class:`str`
            (Optional) name of configuration file to apply
        *ascii*: {``True``} | ``False``
            Write *tri* as an ASCII file (default)
        *binary*: ``True`` | {``False``}
            Write *tri* as an unformatted Fortran binary file
        *byteorder*: {``None``} | ``"big"`` | ``"little"``
            Override system byte order using either 'big' or 'little'
        *bytecount*: {``4``} | ``8``
            Use a *PREC* of 4 for single- or 8 for double-precision 
        *xtol*: {``None``} | :class:`float`
            Tolerance for *x*-coordinates to be truncated to zero
        *ytol*: {``None``} | :class:`float`
            Tolerance for *y*-coordinates to be truncated to zero
        *ztol*: {``None``} | :class:`float`
            Tolerance for *z*-coordinates to be truncated to zero
        *dx*: {``None``} | :class:`float`
            Distance to translate all nodes in *x* direction
        *dy*: {``None``} | :class:`float`
            Distance to translate all nodes in *y* direction
        *dz*: {``None``} | :class:`float`
            Distance to translate all nodes in *z* direction
    :Versions:
        * 2014-06-12 ``@ddalle``: Version 1.0
        * 2015-10-09 ``@ddalle``: Version 1.1; ``Config.xml`` and *ytol*
        * 2016-08-18 ``@ddalle``: Version 1.2; Binary output option
    """
    # Get the input file name
    fuh3d = _get_i(*a, **kw)
    # Read in the UH3D file.
    tri = Tri(uh3d=fuh3d)
    # Get file extension
    ext = tri.GetOutputFileType(**kw)
    # Default file name
    if ext == 'ascii':
        # ASCII file: use ".tri"
        ftri = _get_o(fuh3d, "uh3d", "tri", *a, **kw)
    else:
        # Binary file: use ".i.tri"
        ftri = _got_o(fuh3d, "uh3d", "i.tri", *a, **kw)
    # Read configuration if possible
    cfg = _read_config(*a, **kw)
    # Apply configuration if requested
    if cfg is not None:
        tri.ApplyConfig(cfg)
    # Check for tolerances
    xtol = kw.get('xtol')
    ytol = kw.get('ytol')
    ztol = kw.get('ztol')
    # Apply tolerances
    if xtol is not None:
        tri.Nodes[abs(tri.Nodes[:,0])<=float(xtol), 0] = 0.0
    if ytol is not None:
        tri.Nodes[abs(tri.Nodes[:,1])<=float(ytol), 1] = 0.0
    if ztol is not None:
        tri.Nodes[abs(tri.Nodes[:,2])<=float(ztol), 2] = 0.0
    # Check for nudges
    dx = kw.get('dx')
    dy = kw.get('dy')
    dz = kw.get('dz')
    # Apply nudges
    if dx is not None:
        tri.Nodes[:,0] += float(dx)
    if dy is not None:
        tri.Nodes[:,1] += float(dy)
    if dz is not None:
        tri.Nodes[:,2] += float(dz)
    # Get write options
    tri.Write(ftri, **kw)
    

def main_uh3d2tri():
    r"""CLI for :func:`uh3d2tri`

    :Call:
        >>> main_uh3d2tri()
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    _main(uh3d2tri)


def main_tri2uh3d():
    r"""CLI for :func:`tri2uh3d`

    :Call:
        >>> main_tri2uh3d()
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    _main(tri2uh3d)


def _main(func):
    r"""Command-line interface template

    :Call:
        >>> _main(func)
    :Inputs:
        *func*: **callable**
            API function to call after processing args
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    # Process the command-line interface inputs.
    a, kw = argread.readkeys(sys.argv)
    # Check for a help option.
    if kw.get('h', False) or kw.get("help", False):
        print(textutils.markdown(HELP_UH3D2TRI))
        return
    # Run the main function.
    func(*a, **kw)
    

# Process first arg OR -i option
def _get_i(*a, **kw):
    r"""Process input file name

    :Call:
        >>> fname_in = _get_i(*a, **kw)
        >>> fname_in = _get_i(fname)
        >>> fname_in = _get_i(i=None)
    :Inputs:
        *a[0]*: :class:`str`
            Input file name specified as first positional arg
        *i*: :class:`str`
            Input file name as kwarg; supersedes *a*
    :Outputs:
        *fname_in*: :class:`str`
            Input file name
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    # Get the input file name
    if len(a) == 0:
        # Defaults
        fname_in = None
    else:
        # Use the first general input
        fname_in = a[0]
    # Prioritize a "-i" input
    fname_in = kw.get('i', fname_in)
    # Must have a file name.
    if fname_in is None:
        # Required input.
        raise ValueError("Required at least 1 arg or 'i' kwarg")
    # Output
    return fname_in


# Process second arg OR -o option OR default
def _get_o(fname_in, ext1, ext2, *a, **kw):
    r"""Process output file name

    :Call:
        >>> fname_out = _get_o(fname_in, ext1, ext2, *a, **kw)
    :Inputs:
        *fname_in*: :class:`str`
            Input file name
        *ext1*: :class:`str`
            Expected file extension for *fname_in*
        *ext2*: :class:`str`
            Default file extension for *fname_out*
        *a[1]*: :class:`str`
            Output file name specified as first positional arg
        *o*: :class:`str`
            Output file name as kwarg; supersedes *a*
    :Outputs:
        *fname_out*: :class:`str`
            Output file name
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    # Strip *ext1* as starter for default
    if fname_in.endswith(ext1):
        # Strip expected file extension
        fname_out = fname_in[:-len(ext1)]
    else:
        # Use current file name since extension not found
        fname_out = fname_in + "."
    # Add supplied *ext2* extension for output
    fname_out = fname_out + ext2
    # Get the output file name
    if len(a) >= 2:
        fname_out = a[1]
    # Prioritize a "-o" input.
    fname_out = kw.get('o', fname_out)
    # Output
    return fname_out
        

# Determine best CONFIG file and read it
def _read_config(*a, **kw):
    r"""Read best-guess surface config file

    :Call:
        >>> cfg = _read_config(*a, **kw)
    :Inputs:
        *c*: {``None``} | :class:`str`
            Config file, type determined from file name
        *json*: {``None``} | :class:`str`
            JSON config file name
        *mixsur*: {``None``} | :class:`str`
            ``mixsur``\ /``usurp`` config file name
        *xml*: {``None``} | :class:`str`
            XML config file name
    :Outputs:
        *cfg*: :class:`ConfigXML` or similar
            Configuration instance
    :Versions:
        * 2021-10-01 ``@ddalle``: Version 1.0
    """
    # Configuration
    fcfg = kw.get('c')
    fxml = kw.get("xml")
    fjson = kw.get("json")
    fmxsr = kw.get("mixsur")
    # Check options for best config format
    if fxml:
        # Directly-specified XML config
        return ConfigXML(fxml)
    if fjson:
        # Directly-specified JSON config
        return ConfigJSON(fjson)
    if fmxsr:
        # Directly-specified MIXSUR config
        return ConfigMIXSUR(fmxsr)
    # Check options for format guessed from file name
    if fcfg:
        # Guess type based on extension
        if fcfg.endswith("json"):
            # Probably a JSON config
            return ConfigJSON(fcfg)
        elif fcfg.startswith("mixsur") or fcfg.endswith(".i"):
            # Likely a MIXSUR/OVERINT input file
            return ConfigMIXSUR(fcfg)
        else:
            # Default to XML
            return ConfigXML(fcfg)
    # Check for some defaults
    if os.path.isfile("Config.xml"):
        # Use that
        return ConfigXML("Config.xml")

