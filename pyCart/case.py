"""
Case Control Module: :mod:`pyCart.case`
=======================================

This module contains the important function :func:`case.run_flowCart`, which
actually runs `flowCart` or `aero.csh`, along with the utilities that support
it.

For instance, it contains function to determine how many iterations have been
run, what the working folder is (e.g. ``.``, ``adapt00``, etc.), and what
command-line options to run.

:Versions:
    * 2015-09-07 ``@ddalle``: First documentation
"""

# Reused classes
from cape.case import PrepareEnvironment
# Import options class
from options.runControl import RunControl
# Interface for writing commands
from . import cmd, queue, manage, bin
# Point sensors
from . import pointSensor

# Need triangulations for cases with `intersect` and for averaging
from .tri import Tri, Triq

# Read the local JSON file.
import json
# File control
import os, resource, glob, shutil
# Basic numerics
from numpy import nan, isnan


# Function to setup and call the appropriate flowCart file.
def run_flowCart(verify=False, isect=False):
    """
    Setup and run the appropriate `flowCart`, `mpi_flowCart` command
    
    :Call:
        >>> pyCart.case.run_flowCart(verify=False, isect=False)
    :Inputs:
        *verify*: :class:`bool`
            Whether or not to run `verify` before running `flowCart`
        *isect*: :class:`bool`
            Whether or not to run `intersect` before running `flowCart`
    :Versions:
        * 2014-10-02 ``@ddalle``: First version
        * 2014-12-18 ``@ddalle``: Added :func:`TarAdapt` call after run
    """
    # Check for RUNNING file.
    if os.path.isfile('RUNNING'):
        # Case already running
        raise IOError('Case already running!')
    # Touch the running file.
    os.system('touch RUNNING')
    # Get the settings.
    rc = ReadCaseJSON()
    # Run intersect and verify
    IntersectCase(isect=isect)
    VerifyCase(verify=verify)
    # Determine the run index.
    i = GetPhaseNumber(rc)
    # Create a restart file if appropriate.
    if not rc.get_Adaptive(i):
        # Automatically determine the best check file to use.
        SetRestartIter()
    # Delete any input file.
    if os.path.isfile('input.cntl') or os.path.islink('input.cntl'):
        os.remove('input.cntl')
    # Create the correct input file.
    os.symlink('input.%02i.cntl' % i, 'input.cntl')
    # Extra prep for adaptive --> non-adaptive
    if (i>0) and (not rc.get_Adaptive(i)) and (os.path.isdir('BEST')
            and (not os.path.isfile('history.dat'))):
        # Go to the best adaptive result.
        os.chdir('BEST')
        # Find all *.dat files and Mesh files
        fglob = glob.glob('*.dat') + glob.glob('Mesh.*')
        # Go back up one folder.
        os.chdir('..')
        # Copy all the important files.
        for fname in fglob:
            # Check for the file.
            if os.path.isfile(fname): continue
            # Copy the file.
            shutil.copy('BEST/'+fname, fname)
    # Convince aero.csh to use the *new* input.cntl
    if (i>0) and (rc.get_Adaptive(i)) and (rc.get_Adaptive(i-1)):
        # Go to the best adaptive result.
        os.chdir('BEST')
        # Check for an input.cntl file
        if os.path.isfile('input.cntl'):
            # Move it to a representative name.
            os.rename('input.cntl', 'input.%02i.cntl' % (i-1))
        # Go back up.
        os.chdir('..')
        # Copy the new input file.
        shutil.copy('input.%02i.cntl' % i, 'BEST/input.cntl')
    # Check for flowCart vs. mpi_flowCart
    if not rc.get_MPI(i):
        # Get the number of threads, which may be irrelevant.
        nProc = rc.get_nProc()
        # Set it.
        os.environ['OMP_NUM_THREADS'] = str(nProc)
    # Prepare environment variables (other than OMP_NUM_THREADS)
    PrepareEnvironment(rc, i)
    # Get rid of linked Tecplot files
    if os.path.islink('Components.i.plt'): os.remove('Components.i.plt')
    if os.path.islink('Components.i.dat'): os.remove('Components.i.dat')
    if os.path.islink('cutPlanes.plt'):    os.remove('cutPlanes.plt')
    if os.path.islink('cutPlanes.dat'):    os.remove('cutPlanes.dat')
    # Check for adaptive runs.
    if rc.get_Adaptive(i):
        # Delete the existing aero.csh file
        if os.path.islink('aero.csh'): os.remove('aero.csh')
        # Create a link to this run.
        os.symlink('aero.%02i.csh' % i, 'aero.csh')
        # Call the aero.csh command
        if i > 0 or GetCurrentIter() > 0:
            # Restart case.
            cmdi = ['./aero.csh', 'restart']
        elif rc.get_jumpstart():
            # Initial case
            cmdi = ['./aero.csh', 'jumpstart']
        else:
            # Initial case and create grid
            cmdi = ['./aero.csh']
        # Run the command.
        bin.callf(cmdi, f='flowCart.out')
    elif rc.get_it_avg(i):
        # Check how many iterations by which to offset the count.
        if rc.get_unsteady(i):
            # Get the number of previous unsteady steps.
            n = GetUnsteadyIter()
        else:
            # Get the number of previous steady steps.
            n = GetSteadyIter()
        # Initialize triq.
        if rc.get_clic(i): triq = Triq('Components.i.tri', n=0)
        # Initialize point sensor
        PS = pointSensor.CasePointSensor()
        # Requested iterations
        it_fc = rc.get_it_fc(i)
        # Start and end iterations
        n0 = n
        n1 = n + it_fc
        # Loop through iterations.
        for j in range(it_fc):
            # flowCart command automatically accepts *it_avg*; update *n*
            if j==0 and rc.get_it_start(i)>0:
                # Save settings.
                it_avg = rc.get_it_avg()
                # Startup iterations
                rc.set_it_avg(rc.get_it_start(i))
                # Increase reference for averaging.
                n0 += rc.get_it_start(i)
                # Modified command
                cmdi = cmd.flowCart(fc=rc, i=i, n=n)
                # Reset averaging settings
                rc.set_it_avg(it_avg)
            else:
                # Normal stops every *it_avg* iterations.
                cmdi = cmd.flowCart(fc=rc, i=i, n=n)
            # Run the command for *it_avg* iterations.
            bin.callf(cmdi, f='flowCart.out')
            # Automatically determine the best check file to use.
            SetRestartIter()
            # Get new iteration count.
            if rc.get_unsteady(i):
                # Get the number of previous unsteady steps.
                n = GetUnsteadyIter()
            else:
                # Get the number of previous steady steps.
                n = GetSteadyIter()
            # Process triq files
            if rc.get_clic(i):
                # Read the triq file
                triqj = Triq('Components.i.triq')
                # Weighted average
                triq.WeightedAverage(triqj)
            # Update history
            PS.UpdateIterations()
            # Check for completion
            if (n>=n1) or (j+1==it_fc): break
            # Clean some checkpoint files.
            if rc.get_unsteady(i):
                os.remove('check.%06i.td' % n)
            else:
                os.remove('check.%05i' % n)
                os.remove('checkDT.%05i' % n)
        # Write the averaged triq file
        if rc.get_clic(i):
            triq.Write('Components.%i.%i.%i.triq' % (j+1, n0+1, n))
        # Write the point sensor history file.
        try: PS.WriteHist()
        except Exception: pass
    else:
        # Check how many iterations by which to offset the count.
        if rc.get_unsteady(i):
            # Get the number of previous unsteady steps.
            n = GetUnsteadyIter()
        else:
            # Get the number of previous steady steps.
            n = GetSteadyIter()
        # Call flowCart directly.
        cmdi = cmd.flowCart(fc=rc, i=i, n=n)
        # Run the command.
        bin.callf(cmdi, f='flowCart.out')
    # Remove the RUNNING file.
    if os.path.isfile('RUNNING'): os.remove('RUNNING')
    # Clean up the folder as appropriate.
    # Tar visualization files.
    if rc.get_unsteady(i):
        manage.TarViz(rc)
    # Tar old adaptation folders.
    if rc.get_Adaptive(i):
        manage.TarAdapt(rc)
    # Last reported iteration number
    n = GetHistoryIter()
    # Check status
    if n % 1 != 0:
        # Ended with a failed unsteady cycle!
        f = open('FAIL', 'w')
        # Write the failure type.
        f.write('# Ended with failed unsteady cycle at iteration:\n')
        f.write('%13.6f\n' % n)
        # Quit
        f.close()
        return
    # First and last reported residual
    L1i = GetFirstResid()
    L1f = GetCurrentResid()
    # Check for bad (large or NaN) values.
    if isnan(L1f) or L1f/(0.1+L1i)>1.0e+6:
        # Exploded.
        f = open('FAIL', 'w')
        # Write the failure type.
        f.write('# Bombed at iteration %.6f with residual %.2E.\n' % (n, L1f))
        f.write('%13.6f\n' % n)
        # Quit
        f.close()
        return
    # Check for a hard-to-detect failure present in the output file.
    if CheckFailed():
        # Some other failure
        f = open('FAIL', 'w')
        # Copy the last line of flowCart.out
        f.write('# %s' % bin.tail('flowCart.out'))
        # Quit
        f.close()
        return
    # Get the new restart iteration.
    n = GetCheckResubIter()
    # Assuming that worked, move the temp output file.
    os.rename('flowCart.out', 'run.%02i.%i' % (i, n))
    # Check for TecPlot files to save.
    if os.path.isfile('cutPlanes.plt'):
        os.rename('cutPlanes.plt', 'cutPlanes.%05i.plt' % n)
    if os.path.isfile('Components.i.plt'):
        os.rename('Components.i.plt', 'Components.%05i.plt' % n)
    if os.path.isfile('cutPlanes.dat'):
        os.rename('cutPlanes.dat', 'cutPlanes.%05i.dat' % n)
    if os.path.isfile('Components.i.dat'):
        os.rename('Components.i.dat', 'Components.%05i.dat' % n)
    # Clear check files as appropriate.
    manage.ClearCheck(rc.get_nCheckPoint(i))
    # Check current iteration count.
    if n >= rc.get_LastIter():
        return
    # Run full restart command, including qsub if appropriate
    StartCase(i)
    
    

# Function to intersect geometry if appropriate
def IntersectCase(isect=False):
    """Run `intersect` to combine geometries if appropriate
    
    :Call:
        >>> IntersectCase(isect=False)
    :Inputs:
        *isect*: :class:`bool`
            Whether or not to run `intersect` before running `flowCart`
    :Versions:
        * 2015-09-07 ``@ddalle``: Split from :func:`run_flowCart`
    """
    # Check for intersect status.
    if not isect: return
    # Check for initial run
    if GetRestartIter() != 0: return
    # Check for triangulation file.
    if os.path.isfile('Components.i.tri'):
        # Note this.
        print("File 'Components.i.tri' already exists; aborting intersect.")
        return
    # Run intersect.
    bin.intersect('Components.tri', 'Components.o.tri')
    # Read the original triangulation.
    tric = Tri('Components.c.tri')
    # Read the intersected triangulation.
    trii = Tri('Components.o.tri')
    # Read the pre-intersection triangulation.
    tri0 = Tri('Components.tri')
    # Map the Component IDs.
    trii.MapCompID(tric, tri0)
    # Write the triangulation.
    trii.Write('Components.i.tri')
    
# Function to verify if requested
def VerifyCase(verify=False):
    """Run `verify` to check triangulation if appropriate
    
    :Call:
        >>> VerifyCase(verify=False)
    :Inputs:
        *verify*: :class:`bool``
            Whether or not to run `verify` before running `flowCart`
    :Versions:
        * 2015-09-07 ``@ddalle``: Split from :func:`run_flowCart`
    """
    # Check for verify
    if not verify: return
    # Check for initial run
    if GetRestartIter() != 0: return
    # Run it.
    bin.verify('Components.i.tri')

# Function to call script or submit.
def StartCase(i0=None):
    """Start a case by either submitting it or calling with a system command
    
    :Call:
        >>> pyCart.case.StartCase(i0=None)
    :Inputs:
        *i0*: :class:`int` | ``None``
            Run sequence index of the previous run
    :Versions:
        * 2014-10-06 ``@ddalle``: First version
        * 2015-11-08 ``@ddalle``: Added resubmit/continue functionality
    """
    # Get the config.
    rc = ReadCaseJSON()
    # Determine the run index.
    i = GetPhaseNumber(rc)
    # Check qsub status.
    if not rc.get_qsub(i):
        # Run the case.
        run_flowCart()
    elif i == 0:
        # Submit first case
        # Get the name of the PBS file.
        fpbs = GetPBSScript(i)
        # Submit the case.
        pbs = queue.pqsub(fpbs)
        return pbs
    elif rc.get_Resubmit(i):
        # Check for continuance
        if (i0 is None) or (i>i0) or (not rc.get_Continue(i)):
            # Get the name of the PBS file.
            fpbs = GetPBSScript(i)
            # Submit the case.
            pbs = queue.pqsub(fpbs)
            return pbs
        else:
            # Continue on the same job
            run_flowCart()
    else:
        # Simply run the case. Don't reset modules either.
        run_flowCart()
        
# Function to delete job and remove running file.
def StopCase():
    """Stop a case by deleting its PBS job and removing :file:`RUNNING` file
    
    :Call:
        >>> pyCart.case.StopCase()
    :Versions:
        * 2014-12-27 ``@ddalle``: First version
    """
    # Get the job number.
    jobID = queue.pqjob()
    # Try to delete it.
    queue.qdel(jobID)
    # Check if the RUNNING file exists.
    if os.path.isfile('RUNNING'):
        # Delete it.
        os.remove('RUNNING')
        
# Function to check output file for some kind of failure.
def CheckFailed():
    """Check the :file:`flowCart.out` file for a failure
    
    :Call:
        >>> q = pyCart.case.CheckFailed()
    :Outputs:
        *q*: :class:`bool`
            Whether or not the last line of `flowCart.out` contains 'fail'
    :Versions:
        * 2015-01-02 ``@ddalle``: First version
    """
    # Check for the file.
    if os.path.isfile('flowCart.out'):
        # Read the last line.
        if 'fail' in bin.tail('flowCart.out', 1):
            # This is a failure.
            return True
        else:
            # Normal completed run.
            return False
    else:
        # No flowCart.out file
        return False

# Function to determine which PBS script to call
def GetPBSScript(i=None):
    """Determine the file name of the PBS script to call
    
    This is a compatibility function for cases that do or do not have multiple
    PBS scripts in a single run directory
    
    :Call:
        >>> fpbs = pyCart.case.GetPBSScript(i=None)
    :Inputs:
        *i*: :class:`int`
            Phase number
    :Outputs:
        *fpbs*: :class:`str`
            Name of PBS script to call
    :Versions:
        * 2014-12-01 ``@ddalle``: First version
    """
    # Form the full file name, e.g. run_cart3d.00.pbs
    if i is not None:
        # Create the name.
        fpbs = 'run_cart3d.%02i.pbs' % i
        # Check for the file.
        if os.path.isfile(fpbs):
            # This is the preferred option if it exists.
            return fpbs
        else:
            # File not found; use basic file name
            return 'run_cart3d.pbs'
    else:
        # Do not search for numbered PBS script if *i* is None
        return 'run_cart3d.pbs'
    

# Function to read the local settings file.
def ReadCaseJSON():
    """Read `flowCart` settings for local case
    
    :Call:
        >>> rc = pyCart.case.ReadCaseJSON()
    :Outputs:
        *rc*: :class:`pyCart.options.runControl.RunControl`
            Options interface for run
    :Versions:
        * 2014-10-02 ``@ddalle``: First version
    """
    # Read the file, fail if not present.
    f = open('case.json')
    # Read the settings.
    opts = json.load(f)
    # Close the file.
    f.close()
    # Convert to a RunControl object.
    rc = RunControl(**opts)
    # Output
    return rc
    

# Function to get the most recent check file.
def GetSteadyIter():
    """Get iteration number of most recent steady check file
    
    :Call:
        >>> n = pyCart.case.GetSteadyIter()
    :Outputs:
        *n*: :class:`int`
            Index of most recent check file
    :Versions:
        * 2014-10-02 ``@ddalle``: First version
        * 2014-11-28 ``@ddalle``: Renamed from :func:`GetRestartIter`
    """
    # List the check.* files.
    fch = glob.glob('check.*[0-9]') + glob.glob('BEST/check.*')
    # Initialize iteration number until informed otherwise.
    n = 0
    # Loop through the matches.
    for fname in fch:
        # Get the integer for this file.
        i = int(fname.split('.')[-1])
        # Use the running maximum.
        n = max(i, n)
    # Output
    return n
    
# Function to get the most recent time-domain check file.
def GetUnsteadyIter():
    """Get iteration number of most recent unsteady check file
    
    :Call:
        >>> n = pyCart.case.GetUnsteadyIter()
    :Outputs:
        *n*: :class:`int`
            Index of most recent check file
    :Versions:
        * 2014-11-28 ``@ddalle``: First version
    """
    # Check for td checkpoints
    fch = glob.glob('check.*.td')
    # Initialize unsteady count
    n = 0
    # Loop through matches.
    for fname in fch:
        # Get the integer for this file.
        i = int(fname.split('.')[1])
        # Use the running maximum.
        n = max(i, n)
    # Output.
    return n
    
# Function to get total iteration number
def GetRestartIter():
    """Get total iteration number of most recent check file
    
    This is the sum of the most recent steady iteration and unsteady iteration.
    
    :Call:
        >>> n = pyCart.case.GetRestartIter()
    :Outputs:
        *n*: :class:`int`
            Index of most recent check file
    :Versions:
        * 2014-11-28 ``@ddalle``: First version
    """
    # Get the unsteady iteration number based on available check files.
    ntd = GetUnsteadyIter()
    # Check for an unsteady iteration number.
    if ntd:
        # If there's an unsteady iteration, use that step directly.
        return ntd
    else:
        # Use the steady-state iteration number.
        return GetSteadyIter()
    
# Function to get total iteration number
def GetCheckResubIter():
    """Get total iteration number of most recent check file
    
    This is the sum of the most recent steady iteration and unsteady iteration.
    
    :Call:
        >>> n = pyCart.case.GetRestartIter()
    :Outputs:
        *n*: :class:`int`
            Index of most recent check file
    :Versions:
        * 2014-11-28 ``@ddalle``: First version
        * 2014-11-29 ``@ddalle``: This was renamed from :func:`GetRestartIter`
    """
    # Get the two numbers
    nfc = GetSteadyIter()
    ntd = GetUnsteadyIter()
    # Output
    return nfc + ntd
    
    
# Function to set up most recent check file as restart.
def SetRestartIter(n=None, ntd=None):
    """Set a given check file as the restart point
    
    :Call:
        >>> pyCart.case.SetRestartIter(n=None, ntd=None)
    :Inputs:
        *n*: :class:`int`
            Restart iteration number, defaults to most recent available
        *ntd*: :class:`int`
            Unsteady iteration number
    :Versions:
        * 2014-10-02 ``@ddalle``: First version
        * 2014-11-28 ``@ddalle``: Added time-accurate compatibility
    """
    # Check the input.
    if n   is None: n = GetSteadyIter()
    if ntd is None: ntd = GetUnsteadyIter()
    # Remove the current restart file if necessary.
    if os.path.isfile('Restart.file') or os.path.islink('Restart.file'):
        os.remove('Restart.file')
    # Quit if no check point.
    if n == 0 and ntd == 0:
        return None
    # Create a link to the most appropriate file.
    if os.path.isfile('check.%06i.td' % ntd):
        # Restart from time-accurate check point
        os.symlink('check.%06i.td' % ntd, 'Restart.file')
    elif os.path.isfile('BEST/check.%05i' % n):
        # Restart file in adaptive folder
        os.symlink('BEST/check.%05i' % n, 'Restart.file')
    elif os.path.isfile('check.%05i' % n):
        # Restart file in current folder
        os.symlink('check.%05i' % n, 'Restart.file')
    
    
# Function to chose the correct input to use from the sequence.
def GetPhaseNumber(rc):
    """Determine the appropriate input number based on results available
    
    :Call:
        >>> i = pyCart.case.GetPhaseNumber(rc)
    :Inputs:
        *rc*: :class:`pyCart.options.runControl.RunControl`
            Options interface for `flowCart`
    :Outputs:
        *i*: :class:`int`
            Most appropriate phase number for a restart
    :Versions:
        * 2014-10-02 ``@ddalle``: First version
    """
    # Get the run index.
    n = GetCheckResubIter()
    # Loop through possible input numbers.
    for j in range(rc.get_nSeq()):
        # Get the actual run number
        i = rc.get_PhaseSequence(j)
        # Check for output files.
        if len(glob.glob('run.%02i.*' % i)) == 0:
            # This run has not been completed yet.
            return i
        # Check the iteration number.
        if n < rc.get_PhaseIters(j):
            # This case has been run, but hasn't reached the min iter cutoff
            return i
    # Case completed; just return the last value.
    return i
    
# Function to read last line of 'history.dat' file
def GetHistoryIter(fname='history.dat'):
    """Get the most recent iteration number from a :file:`history.dat` file
    
    :Call:
        >>> n = pyCart.case.GetHistoryIter(fname='history.dat')
    :Inputs:
        *fname*: :class:`str`
            Name of file to read
    :Outputs:
        *n*: :class:`float`
            Last iteration number
    :Versions:
        * 2014-11-24 ``@ddalle``: First version
    """
    # Check the file beforehand.
    if not os.path.isfile(fname):
        # No history
        return 0
    # Check the file.
    try:
        # Try to tail the last line.
        txt = bin.tail(fname)
        # Try to get the integer.
        return float(txt.split()[0])
    except Exception:
        # If any of that fails, return 0
        return 0
        
# Get last residual from 'history.dat' file
def GetHistoryResid(fname='history.dat'):
    """Get the last residual in a :file:`history.dat` file
    
    :Call:
        >>> L1 = pyCart.case.GetHistoryResid(fname='history.dat')
    :Inputs:
        *fname*: :class:`str`
            Name of file to read
    :Outputs:
        *L1*: :class:`float`
            Last L1 residual
    :Versions:
        * 2015-01-02 ``@ddalle``: First version
    """
    # Check the file beforehand.
    if not os.path.isfile(fname):
        # No history
        return nan
    # Check the file.
    try:
        # Try to tail the last line.
        txt = bin.tail(fname)
        # Try to get the integer.
        return float(txt.split()[3])
    except Exception:
        # If any of that fails, return 0
        return nan
        

# Function to check if last line is unsteady
def CheckUnsteadyHistory(fname='history.dat'):
    """Check if the current history ends with an unsteady iteration

    :Call:
        >>> q = pyCart.case.CheckUnsteadyHistory(fname='history.dat')
    :Inputs:
        *fname*: :class:`str`
            Name of file to read
    :Outputs:
        *q*: :class:`float`
            Whether or not the last iteration of *fname* has a '.' in it
    :Versions:
        * 2014-12-17 ``@ddalle``: First version
    """
    # Check the file beforehand.
    if not os.path.isfile(fname):
        # No history
        return False
    # Check the file's contents.
    try:
        # Try to tail the last line.
        txt = bin.tail(fname)
        # Check for a dot.
        return ('.' in txt.split()[0])
    except Exception:
        # Something failed; invalid history
        return False

    
# Function to get the most recent working folder
def GetWorkingFolder():
    """Get the most recent working folder, either '.' or 'adapt??/'
    
    This function must be called from the top level of a case run directory.
    
    :Call:
        >>> fdir = pyCart.case.GetWorkingFolder()
    :Outputs:
        *fdir*: :class:`str`
            Name of the most recently used working folder with a history file
    :Versions:
        * 2014-11-24 ``@ddalle``: First version
    """
    # Try to get iteration number from working folder.
    n0 = GetCurrentIter()
    # Initialize working directory.
    fdir = '.'
    # Implementation of returning to adapt after startup turned off
    if os.path.isfile('history.dat') and not os.path.islink('history.dat'):
        return fdir
    # Check for adapt?? folders
    for fi in glob.glob('adapt??'):
        # Attempt to read it.
        ni = GetHistoryIter(os.path.join(fi, 'history.dat'))
        # Check it.
        if ni >= n0:
            # Current best estimate of working directory.
            fdir = fi
    # Output
    return fdir
       
# Function to get most recent adaptive iteration
def GetCurrentResid():
    """Get the most recent iteration including unsaved progress

    Iteration numbers from time-accurate restarts are corrected to match the
    global iteration numbering.

    :Call:
        >>> L1 = pyCart.case.GetCurrentResid()
    :Outputs:
        *L1*: :class:`float`
            Last L1 residual
    :Versions:
        * 2015-01-02 ``@ddalle``: First version
    """
    # Get the working folder.
    fdir = GetWorkingFolder()
    # Get the residual.
    return GetHistoryResid(os.path.join(fdir, 'history.dat'))

# Function to get first recent adaptive iteration
def GetFirstResid():
    """Get the first iteration

    :Call:
        >>> L1 = pyCart.case.GetFirstResid()
    :Outputs:
        *L1*: :class:`float`
            First L1 residual
    :Versions:
        * 2015-07-22 ``@ddalle``: First version
    """
    # Get the working folder.
    fdir = GetWorkingFolder()
    # File name
    fname = os.path.join(fdir, 'history.dat')
    # Check the file beforehand.
    if not os.path.isfile(fname):
        # No history
        return nan
    # Check the file.
    try:
        # Try to open the file.
        f = open(fname, 'r')
        # Initialize line.
        txt = '#'
        # Read the lines until it's not a comment.
        while txt.startswith('#'):
            # Read the next line.
            txt = f.readline()
        # Try to get the integer.
        return float(txt.split()[3])
    except Exception:
        # If any of that fails, return 0
        return nan
    
# Function to get most recent L1 residual
def GetCurrentIter():
    """Get the residual of the most recent iteration including unsaved progress

    :Call:
        >>> n = pyCart.case.GetCurrentIter()
    :Outputs:
        *n*: :class:`int`
            Most recent index written to :file:`history.dat`
    :Versions:
        * 2014-11-28 ``@ddalle``: First version
    """
    # Try to get iteration number from working folder.
    ntd = GetHistoryIter()
    # Check it.
    if ntd and (not CheckUnsteadyHistory()):
        # Don't read adapt??/ history
        return ntd
    # Initialize adaptive iteration number
    n0 = 0
    # Check for adapt?? folders
    for fi in glob.glob('adapt??'):
        # Attempt to read it.
        ni = GetHistoryIter(os.path.join(fi, 'history.dat'))
        # Check it.
        if ni > n0:
            # Update best estimate.
            n0 = ni
    # Output the total.
    return n0 + ntd
    
# Link best file based on name and glob
def LinkFromGlob(fname, fglb, isplit=-2, csplit='.'):
    """Link the most recent file to a basic unmarked file name
    
    The function will attempt to map numbered or adapted file names using the
    most recent iteration or adaptation.  The following gives examples of links
    that could be created using ``Components.i.plt`` for *fname* and
    ``Components.[0-9]*.plt`` for *fglb*.
    
        * ``Components.i.plt`` (no link)
        * ``Components.01000.plt`` --> ``Components.i.plt``
        * ``adapt03/Components.i.plt`` --> ``Components.i.plt``
    
    :Call:
        >>> pyCart.case.LinkFromGlob(fname, fglb, isplit=-2, csplit='.')
    :Inputs:
        *fname*: :class:`str`
            Name of unmarked file, like ``Components.i.plt``
        *fglb*: :class:`str`
            Glob for marked file names
        *isplit*: :class:`int`
            Which value of ``f.split()`` to use to get index number
        *csplit*: :class:`str`
            Character on which to split to find indices, usually ``'.'``
    :Versions:
        * 2015-11-20 ``@ddalle``: First version
    """
    # Check for already-existing regular file.
    if os.path.isfile(fname) and not os.path.islink(fname): return
    # Remove the link if necessary.
    if os.path.isfile(fname) or os.path.islink(fname):
        os.remove(fname)
    # Get the working directory.
    fdir = GetWorkingFolder()
    # Check it.
    if fdir == '.':
        # List files that match the requested glob.
        fglob = glob.glob(fglb)
        # Check for empty glob.
        if len(fglob) == 0: return
        # Get indices from those files.
        n = [int(f.split(csplit)[isplit]) for f in fglob]
        # Extract file with maximum index.
        fsrc = fglob[n.index(max(n))]
    else:
        # File from the working folder (if it exists)
        fsrc = os.path.join(fdir, fname)
        # Check for the file.
        if not os.path.isfile(fsrc):
            # Get the adaptation number of the working folder
            nadapt = int(fdir[-2:])
            # Try the previous adaptation file.
            fdir = 'adapt%02i' % (nadapt-1)
            # Use that folder.
            fsrc = os.path.join(fdir, fname)
        # Check for the file again.
        if not os.path.isfile(fsrc): return
    # Create the link if possible
    if os.path.isfile(fsrc): os.symlink(fsrc, fname)
            
    
# Link best tecplot files
def LinkPLT():
    """Link the most recent Tecplot files to fixed file names
    
    Uses file names :file:`Components.i.plt` and :file:`cutPlanes.plt`
    
    :Call:
        >>> pyCart.case.LinkPLT()
    :Versions:
        * 2015-03-10 ``@ddalle``: First version
        * 2015-11-20 ``@ddalle``: Delegate work and support ``*.dat`` files
    """
    # Surface file
    LinkFromGlob('Components.i.plt', 'Components.[0-9]*.plt', -2)
    LinkFromGlob('Components.i.dat', 'Components.[0-9]*.dat', -2)
    LinkFromGlob('cutPlanes.plt',    'cutPlanes.[0-9]*.plt', -2)
    LinkFromGlob('cutPlanes.dat',    'cutPlanes.[0-9]*.dat', -2)
            
    
