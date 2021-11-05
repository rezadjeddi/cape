#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
:mod:`cape.pykes.case`: Kestrel individual-case module
=======================================================

This module provides interfaces to run a single case of Kestrel from
the case folder. It also provides tools such as :func:`GetCurrentIter`,
which determines how many cases have been run.

The functions of this module expect to be run from a Kestrel case folder
created by :mod:`cape.pykes`.

"""

# Standard library
import glob
import os
import shutil
import sys

# Third-party


# Local imports
from . import cmdgen
from .. import argread
from .. import text as textutils
from .jobxml import JobXML
from ..cfdx import bin
from ..cfdx import case as cc
from ..cfdx import queue
from ..tnakit import fileutils
from .options.runcontrol import RunControl



# Help message for CLI
HELP_RUN_KESTREL = r"""
``run_kestrel.py``: Run Kestrel for one phase
================================================

This script determines the appropriate phase to run for an individual
case (e.g. if a restart is appropriate, etc.), sets that case up, and
runs it.

:Call:
    
    .. code-block:: console
    
        $ run_kestrel.py [OPTIONS]
        $ python -m cape.pykes run [OPTIONS]
        
:Options:
    
    -h, --help
        Display this help message and quit

:Versions:
    * 2021-10-21 ``@ddalle``: Version 1.0
"""


# Template file names
XML_FILE = "kestrel.xml"
XML_FILE_GLOB = "kestrel.[0-9]*.xml"
XML_FILE_TEMPLATE = "kestrel.%02i.xml"
LOG_FILE = os.path.join("log", "perIteration.log")
STDOUT_FILE = "kestrel.out"


# --- Execution ----
def run_kestrel():
    r"""Setup and run the appropriate Kestrel command

    This function runs one phase, but may restart the case by recursing
    if settings prescribe it.

    :Call:
        >>> run_kestrel()
    :Versions:
        * 2021-10-21 ``@ddalle``: Version 0.1; started
    """
    # Process arguments
    a, kw = argread.readkeys(sys.argv)
    # Check for help argument.
    if kw.get('h') or kw.get('help'):
        # Display help and exit
        print(textutils.markdown(HELP_RUN_KESTREL))
        return
    # Start RUNNING and initialize timer
    tic = cc.init_timer()
    # Read settings
    rc = read_case_json()
    # Get phase number
    j = get_phase(rc)
    # Write the start time
    write_starttime(tic, rc, j)
    # Prepare files
    prepare_files(rc, j)
    # Prepare environment
    cc.PrepareEnvironment(rc, j)
    # Run appropriate commands
    run_phase(rc, j)
    # Clean up files
    finalize_files(rc, j)
    # Remove the RUNNING file
    if os.path.isfile("RUNNING"):
        os.remove("RUNNING")


def run_phase(rc, j):
    r"""Run one pass of one phase

    :Call:
        >>> run_phase(rc, j)
    :Inputs:
        *rc*: :class:`RunControl`
            Options interface from ``case.json``
        *j*: :class:`int`
            Phase number
    :Versions:
        * 2021-11-02 ``@ddalle``: Version 1.0
    """
    # Count number of times this phase has been run previously.
    nprev = len(glob.glob("run.%02i.*" % j))
    # Read XML file
    xml = read_xml(rc, j)
    # Get job name
    job_name = xml.get_job_name()
    # Get the last iteration number
    n = get_current_iter()
    # Number of requested iters for the end of this phase
    nj = rc.get_PhaseIters(j)
    # Mesh generation and verification status
    if j == 0 and n is None:
        # Run *intersect* and *verify*
        cc.CaseIntersect(rc, job_name, n)
        cc.CaseVerify(rc, job_name, n)
        # Create volume mesh if necessary
        cc.CaseAFLR3(rc, proj=job_name, n=n)
        # Check for mesh-only phase
        if nj is None:
            # Create an output file to indicate completion
            open("run.00.0", 'w').close()
            return
    # Prepare for restart if that's appropriate
    set_restart_iter(rc)
    # Save initial iteration number, but replacing ``None``
    if n is None:
        n0 = 0
    else:
        n0 = n
    # Check if we should run this phase
    if nprev == 0 or n0 < nj:
        # Get the ``csi`` command
        cmdi = cmdgen.csi(rc, j)
        # Run the command
        bin.callf(cmdi, f="kestrel.out")
        # Check new iteration number
        n1 = get_current_iter()
        # Check for lack of progress
        if n1 <= n0:
            raise SystemError(
                "Running phase %i did not advance iteration count" % j)
    else:
        # No new iterations
        n1 = n0
    # Check if last phase
    if j >= rc.get_PhaseSequence(-1):
        # Check iteration number
        if n1 >= rc.get_LastIter():
            return


def start_case():
    r"""Start a case by either submitting it or calling locally
    
    :Call:
        >>> start_case()
    :Versions:
        * 2021-11-05 ``@ddalle``: Version 1.0
    """
    # Get the config
    rc = read_case_json()
    # Determine the run index.
    i = get_phase(rc)
    # Check qsub status.
    if rc.get_sbatch(i):
        # Get the name of the PBS file
        fpbs = get_pbsscript(i)
        # Submit the Slurm case
        pbs = queue.psbatch(fpbs)
        return pbs
    elif rc.get_qsub(i):
        # Get the name of the PBS file.
        fpbs = get_pbsscript(i)
        # Submit the case.
        pbs = queue.pqsub(fpbs)
        return pbs
    else:
        # Simply run the case. Don't reset modules either.
        run_kestrel()


# --- File management ---
def prepare_files(rc, j=None):
    r"""Prepare files appropriate to run phase *j*

    :Call:
        >>> prepare_files(rc, j=None)
    :Inputs:
        *rc*: :class:`RunControl`
            Options interface from ``case.json``
        *j*: {``None``} | :class:`int`
            Phase number
    :Versions:
        * 2021-11-02 ``@ddalle``: Version 1.0
    """
    # Get phase number if needed
    if j is None:
        j = get_phase(rc)
    # XML file names
    fxml0 = XML_FILE
    fxmlj = XML_FILE_TEMPLATE % j
    # Check for "kestrel.xml" file
    if os.path.isfile(fxml0) or os.path.islink(fxml0):
        os.remove(fxml0)
    # Check for *j*
    if not os.path.isfile(fxmlj):
        raise OSError("Couldn't find file '%s'" % fxmlj)
    # Link "kestrel.02.xml" to "kestrel.xml", for example
    os.symlink(fxmlj, fxml0)


def finalize_files(rc, j=None):
    r"""Clean up files after running one cycle of phase *j*
    
    :Call:
        >>> finalize_files(rc, j=None)
    :Inputs:
        *rc*: :class:`RunControl`
            Options interface from ``case.json``
        *j*: {``None``} | :class:`int`
            Phase number
    :Versions:
        * 2021-11-05 ``@ddalle``: Version 1.0
    """
    # Get phase number if necessary
    if j is None:
        # Get locally
        j = get_phase(rc)
    # Read XML file
    xml = read_xml(rc, j)
    # Get the project name
    jobname = xml.get_job_name()
    # Get the last iteration number
    n = get_current_iter()
    # Don't use ``None`` for this
    if n is None:
        n = 0
    # Name of history file
    fhist = "run.%02i.%i" % (j, n)
    # Assuming that worked, move the temp output file.
    if os.path.isfile(STDOUT_FILE):
        # Copy the file
        shutil.copy(STDOUT_FILE, fhist)
    else:
        # Create an empty file
        open(fhist, 'w').close()


def set_restart_iter(rc):
    pass


# --- STATUS functions ---
def get_phase(rc):
    r"""Determine the phase number based on files in folder
    
    :Call:
        >>> j = get_phase(rc)
    :Inputs:
        *rc*: :class:`RunControl`
            Case *RunControl* options
    :Outputs:
        *j*: :class:`int`
            Most appropriate phase number for a (re)start
    :Versions:
        * 2021-10-21 ``@ddalle``: Version 1.0
    """
    # Get the iteration from which a restart would commence
    n = None
    # Start with phase 0 if ``None``
    if n is None:
        return rc.get_PhaseSequence(0)
    # Get last phase number
    j = rc.get_PhaseSequence(-1)
    # Special check for --skeleton cases
    if len(glob.glob("run.%02i.*" % j)) > 0:
        # Check iteration count
        if n >= rc.get_PhaseIters(j):
            return j
    # Loop through phases
    for j in rc.get_PhaseSequence():
        # Target iterations for this phase
        nt = rc.get_PhaseIters(j)
        # Check output files
        if len(glob.glob("run.%02i.*" % j)) == 0:
            # This phase has not been run
            return j
        # Check the iteration- numbers
        if nt is None:
            # Don't check null phases
            pass
        elif n < nt:
            # Case has been run but hasn't reached target
            return j
    # Case completed; just return the last phase
    return j


def get_current_iter():
    r"""Get the most recent iteration number

    :Call:
        >>> n = get_current_iter()
    :Outputs:
        *n*: :class:`int` | ``None``
            Last iteration number
    :Versions:
        * 2021-11-05 ``@ddalle``: Version 1.0
    """
    # Check if log file exists
    if not os.path.isfile(LOG_FILE):
        return None
    # Otherwise open file to read last line
    lines = fileutils.tail(LOG_FILE, n=1)
    # Attempt to unpack it
    if len(lines) == 0:
        # File exists but is empty
        return 0
    # Unpack singleton list of lines
    line, = lines
    # Trey to get iteration number
    try:
        # First entry should be iteration number
        return int(line.split()[0])
    except ValueError:
        # Some other tailing line; probably no iterations yet
        return 0


# --- Case settings ---
def read_case_json():
    r"""Read *RunControl* settings from ``case.json``
    
    :Call:
        >>> rc = read_case_json()
    :Outputs:
        *rc*: :class:`cape.pykes.options.runcontrol.RunControl`
            Case run control settings
    :Versions:
        * 2021-10-21 ``@ddalle``: Version 1.0
    """
    return cc.read_case_json(RunControl)


def read_xml(rc=None, j=None):
    r"""Read Kestrel ``.xml`` control file for one phase

    :Call:
        >>> xml = read_xml(rc=None, j=None)
    :Inputs:
        *rc*: {``None``} | :class:`RunControl`
            Options interface from ``case.json``
        *j*: {``None``} | :class:`int`
            Phase number
    :Outputs:
        *xml*: :class:`JobXML`
            XML control file interface
    :Versions:
        * 2021-11-02 ``@ddalle``: Version 1.0
    """
    # Read "case.json" if needed
    if rc is None:
        rc = read_case_json()
    # Automatic phase option
    if j is None and rc is not None:
        j = get_phase(rc)
    # Check for folder w/o "case.json"
    if j is None:
        if os.path.isfile(XML_FILE):
            # Use currently-linked file
            return JobXML(XML_FILE)
        else:
            # Look for template files
            xmlglob = glob.glob(XML_FILE_GLOB)
            # Sort it
            xmlglob.sort()
            # Use the last one
            return JobXML(xmlglob[-1])
    # Get specified version
    return JobXML(XML_FILE_TEMPLATE % j)


# Function to determine which PBS script to call
def get_pbsscript(j=None):
    r"""Determine the file name of the PBS script to call

    This is a compatibility function for cases that do or do not have
    multiple PBS scripts in a single run directory

    :Call:
        >>> fpbs = get_pbsscript(j=None)
    :Inputs:
        *j*: {``None``} | :class:`int`
            Phase number
    :Outputs:
        *fpbs*: :class:`str`
            Name of PBS script to call
    :Versions:
        * 2021-11-05 ``@ddalle``: Version 1.0
    """
    # Form the full file name, e.g. run_cart3d.00.pbs
    if j is not None:
        # Create the name.
        fpbs = "run_kestrel.%02i.pbs" % j
        # Check for the file.
        if os.path.isfile(fpbs):
            # This is the preferred option if it exists.
            return fpbs
        else:
            # File not found; use basic file name
            return "run_kestrel.pbs"
    else:
        # Do not search for numbered PBS script if *i* is None
        return "run_kestrel.pbs"


# --- Timers ---
def write_starttime(tic, rc, j, fname="pykes_start.dat"):
    r"""Write the start time from *tic*
    
    :Call:
        >>> write_starttime(tic, rc, j, fname="pykes_start.dat")
    :Inputs:
        *tic*: :class:`datetime.datetime`
            Time to write into data file
        *rc*: :class:`RunControl`
            Options interface
        *j*: :class:`int`
            Phase number
        *fname*: {``"pykes_start.dat"``} | :class:`str`
            Name of file containing run start times
    :Versions:
        * 2021-10-21 ``@ddalle``: Version 1.0
    """
    # Call the function from :mod:`cape.cfdx.case`
    cc.WriteStartTimeProg(tic, rc, j, fname, "run_kestrel.py")


