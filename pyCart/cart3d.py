"""
Cart3D setup module: :mod:`pyCart.cart3d`
=========================================

This module provides tools to quickly setup basic Cart3D runs from a small set
of input files.  Alternatively, the methods and classes can be used to help
setup a problem that is too complex or customized to conform to standardized
script libraries.
"""

# Basic numerics
import numpy as np
# Configuration file processor
import json
# File system and operating system management
import os, shutil
import subprocess as sp

# pyCart settings class
from . import options
# pyCart queue itnerface
from . import queue
# Cart3D binary interfaces
from . import bin
# Run directory module
from . import case

# Functions and classes from other modules
from trajectory import Trajectory
from post       import LoadsDat

# Import specific file control classes
from inputCntl   import InputCntl
from aeroCsh     import AeroCsh
from preSpecCntl import PreSpecCntl
from config      import Config

# Import triangulation
from tri import Tri

# Import history modules.
#import aero
import history

# Get the root directory of the module.
_fname = os.path.abspath(__file__)

# Saved folder names
PyCartFolder = os.path.split(_fname)[0]
TemplateFodler = os.path.join(PyCartFolder, "templates")


# Function to automate minor changes to docstrings to make them pyCart.Cart3d
def _upgradeDocString(docstr, fromclass):
    """
    Upgrade docstrings from a certain subclass to make them look like
    :class:`pyCart.cart3d.Cart3d` docstrings.
    
    :Call:
        >>> doc3d = _upgradDocString(docstr, fromclass)
        
    :Inputs:
        *docstr*: :class:`str`
            Docstring (e.g. ``x.__doc__``) from some other method
        *fromclass*: :class:`str`
            Name of class of the original docstring (e.g. ``type(x).__name__``)
            
    :Outputs:
        *doc3d*: :class:`str`
            Docstring with certain substitutions, e.g. ``x.`` --> ``cart3d.``
            
    :Versions:
        * 2014.07.28 ``@ddalle``: First version
    """
    # Check the input class.
    if fromclass in ['Trajectory']:
        # Replacements in the :Call: area
        docstr = docstr.replace(">>> x.", ">>> cart3d.")
        docstr = docstr.replace("= x.", "= cart3d.")
        # Replacements in variable names
        docstr = docstr.replace('*x*', '*cart3d*')
        # Class name
        docstr = docstr.replace('trajectory.Trajectory', 'cart3d.Cart3d')
        docstr = docstr.replace('trajectory class', 'control class')
    # Output
    return docstr

#<!--
# ---------------------------------
# I consider this portion temporary

# Get the umask value.
umask = 0027
# Get the folder permissions.
fmask = 0777 - umask
dmask = 0777 - umask

# Change the umask to a reasonable value.
os.umask(umask)

# ---------------------------------
#-->

    
# Class to read input files
class Cart3d(object):
    """
    Class for handling global options and setup for Cart3D.
    
    This class is intended to handle all settings used to describe a group
    of Cart3D cases.  For situations where it is not sufficiently
    customized, it can be used partially, e.g., to set up a Mach/alpha sweep
    for each single control variable setting.
    
    The settings are read from a JSON file, which is robust and simple to
    read, but has the disadvantage that there is no support for comments.
    Hopefully the various names are descriptive enough not to require
    explanation.
    
    Defaults are read from the file ``$PYCART/settings/pyCart.default.json``.
    
    :Call:
        >>> cart3d = pyCart.Cart3d(fname="pyCart.json")
    :Inputs:
        *fname*: :class:`str`
            Name of pyCart input file
    :Outputs:
        *cart3d*: :class:`pyCart.cart3d.Cart3d`
            Instance of the pyCart control class
    :Data members:
        *cart3d.opts*: :class:`dict`
            Dictionary of options for this case (directly from *fname*)
        *cart3d.x*: :class:`pyCart.trajectory.Trajectory`
            Values and definitions for variables in the run matrix
        *cart3d.RootDir*: :class:`str`
            Absolute path to the root directory
    :Versions:
        * 2014.05.28 ``@ddalle``  : First version
        * 2014.06.03 ``@ddalle``  : Renamed class `Cntl` --> `Cart3d`
        * 2014.06.30 ``@ddalle``  : Reduced number of data members
        * 2014.07.27 ``@ddalle``  : `cart3d.Trajectory` --> `cart3d.x`
    """
    
    # Initialization method
    def __init__(self, fname="pyCart.json"):
        """Initialization method for :mod:`pyCart.cart3d.Cart3d`"""
        
        # Apply missing settings from defaults.
        opts = options.Options(fname=fname)
        
        # Save all the options as a reference.
        self.opts = opts
        
        # Import modules
        self.ImportModules()
        
        # Process the trajectory.
        self.x = Trajectory(**opts['Trajectory'])
        
        # Read the input files.
        self.InputCntl = InputCntl(self.opts.get_InputCntl())
        self.AeroCsh   = AeroCsh(self.opts.get_AeroCsh())
        
        # Save the current directory as the root.
        self.RootDir = os.getcwd()
        
        
    # Output representation
    def __repr__(self):
        """Output representation for the class."""
        # Display basic information from all three areas.
        return "<pyCart.Cart3d(nCase=%i, tri='%s')>" % (
            self.x.nCase,
            self.opts.get_TriFile())
        
    # Function to import user-specified options
    def ImportModules(self):
        """Import user-defined modules, if any
        
        :Call:
            >>> cart3d.ImportModules()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
        :Versions:
            * 2014.10.08 ``@ddalle``: First version
        """
        # Get Modules.
        lmod = self.opts.get("Modules", [])
        # Ensure list.
        if not lmod:
            # Empty --> empty list
            lmod = []
        elif type(lmod).__name__ != "list":
            # Single string
            lmod = [lmod]
        # Loop through modules.
        for imod in lmod:
            # Status update
            print("Importing module '%s'." % imod)
            # Load the module by its name
            exec('self.%s = __import__("%s")' % (imod, imod))
        
    # Function to prepare the triangulation for each grid folder
    def ReadTri(self):
        """Read initial triangulation file(s)
        
        :Call:
            >>> cart3d.ReadTri()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
        :Versions:
            * 2014-08-30 ``@ddalle``: First version
        """
        # Only read triangulation if not already present.
        try:
            self.tri
            return
        except Exception:
            pass
        # Get the list of tri files.
        ftri = self.opts.get_TriFile()
        # Status update.
        print("  Reading tri file(s) from root directory.")
        # Go to root folder safely.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Read them.
        if type(ftri).__name__ == 'list':
            # Read the initial triangulation.
            tri = Tri(ftri[0])
            # Loop through the remaining tri files.
            for f in ftri[1:]:
                # Append the file.
                tri.Add(Tri(f))
        else:
            # Just read the triangulation file.
            tri = Tri(ftri)
        # Save it.
        self.tri = tri
        # Check for a config file.
        os.chdir(self.RootDir)
        self.tri.config = Config(self.opts.get_ConfigFile())
        # Return to original location.
        os.chdir(fpwd)
        
        
    # Function to plot most recent results.
    def Plot(self, comp, C, nRow=None, nCol=None, **kw):
        """Plot force, moment, and/or residual history for all cases
        
        :Call:
            >>> h = cart3d.Plot(comp, C, nRow=None, nCol=None, **kw)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *comp*: :class:`str`
                Name of component to plot
            *C*: :class:`list` (:class:`str`)
                List of coefficients to plot
            *nRow*: :class:`int`
                Number of rows of subplots to make
            *nCol*: :class:`int`
                Number of columns of subplots to make
            *n*: :class:`int`
                Only show the last *n* iterations
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d0*: :class:`float`
                Default delta to use
            *d*: :class:`dict`
                Dictionary of deltas for each component
            *tag*: :class:`str` 
                Tag to put in upper corner, for instance case number and name
            *restriction*: :class:`str`
                Type of data, e.g. ``"SBU - ITAR"`` or ``"U/FOUO"``
        :Outputs:
            *h*: :class:`list` (:class:`dict`)
                List of dictionaries of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Check for the aero module.
        try:
            # Mindlessly check if Python recognizes the name.
            aero
        except NameError:
            # Import the aero module.
            import aero
        # Go to root folder safely.
        fpwd = os.getcwd()
        # Get the case names.
        fruns = self.x.GetFullFolderNames()
        # Default number of rows and cols.
        if (nCol is None):
            # Make it up.
            if len(C) == 4:
                # 2x2 plot
                nRow = 2
                nCol = 2
            else:
                # Nx1 plot
                nRow = len(C)
                nCol = 1
        elif (nRow is None):
            # Assume the number of cols is correct.
            nRow = int(np.ceil(float(len(C))/nCol))
        # Initialize output.
        h = []
        # Loop through runs.
        for i in range(len(fruns)):
            # Get the folder name.
            frun = fruns[i]
            # Go to the folder.
            os.chdir(self.RootDir)
            os.chdir(frun)
            # Make a new figure.
            aero.plt.figure()
            # Read the aerodata and extract the single component.
            FM = aero.Aero([comp])[comp]
            # Tag the run.
            kw['tag'] = 'Case %i: %s\nComponent=%s' % (i, frun, comp)
            # Set up the plot.
            h.append(FM.Plot(nRow, nCol, C, **kw))
        # Return to original location.
        os.chdir(fpwd)
        # Output
        return h
        
        
    # Function to display current status
    def DisplayStatus(self, **kw):
        """Display current status for all cases
        
        This prints case names, current iteration numbers, and so on.
        
        :Call:
            >>> cart3d.DisplayStatus(j=False)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *j*: :class:`bool`
                Whether or not to display job ID numbers
        :Versions:
            * 2014.10.04 ``@ddalle``: First version
        """
        self.SubmitJobs(c=True, j=kw.get('j',False))
        
    # Master interface function
    def SubmitJobs(self, **kw):
        """Check jobs and prepare or submit jobs if necessary
        
        :Call:
            >>> cart3d.SubmitJobs(**kw)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *c*: :class:`bool`
                If ``True``, only display status; do not submit new jobs
            *j*: :class:`bool`
                Whether or not to display job ID numbers
        :Versions:
            * 2014.10.05 ``@ddalle``: First version
        """
        # Get flag that tells pycart only to check jobs.
        qCheck = kw.get('c', False)
        # Get flag to show job IDs
        qJobID = kw.get('j', False)
        # Maximum number of jobs
        nSubMax = int(kw.get('n', 10))
        # Get the qstat info (safely; do not raise an exception).
        jobs = queue.qstat(u=kw.get('u',os.environ['USER']))
        # Initialize number of submitted jobs
        nSub = 0
        # Get the case names.
        fruns = self.x.GetFullFolderNames()
        # Maximum length of one of the names
        lrun = max([len(frun) for frun in fruns])
        # Print the right number of '-' chars
        f = '-'; s = ' '
        # Create the string stencil.
        if qJobID:
            # Print status with job numbers.
            stncl = ('%%-%is ' * 6) % (4, lrun, 7, 11, 3, 7)
            # Print header row.
            print(stncl % ("Case", "Config/Run Directory", "Status", 
                "Iterations", "Que", "Job ID"))
            # Print "---- --------" etc.
            print(f*4 + s + f*lrun + s + f*7 + s + f*11 + s + f*3 + s + f*7)
        else:
            # Print status without job numbers.
            stncl = ('%%-%is ' * 5) % (4, lrun, 7, 11, 3)
            # Print header row.
            print(stncl % ("Case", "Config/Run Directory", "Status", 
                "Iterations", "Que"))
            # Print "---- --------" etc.
            print(f*4 + s + f*lrun + s + f*7 + s + f*11 + s + f*3)
        # Initialize dictionary of statuses.
        total = {'PASS':0, 'PASS*':0, '---':0, 'INCOMP':0,
            'RUN':0, 'DONE':0, 'QUEUE':0}
        # Loop through the runs.
        for i in range(self.x.nCase):
            # Extract case
            frun = fruns[i]
            # Check status.
            sts = self.CheckCaseStatus(i, jobs)
            # Get active job number.
            jobID = self.GetPBSJobID(i)
            # Append.
            total[sts] += 1
            # Get the current number of iterations
            n = self.CheckCase(i)
            # Switch on whether or not case is set up.
            if n is None:
                # Case is not prepared.
                itr = "/"
                que = "."
            else:
                # Case is prepared and might be running.
                # Get last iteration.
                nMax = self.GetLastIter(i)
                # Iteration string
                itr = "%i/%i" % (n, nMax)
                # Check the queue.
                if jobID in jobs:
                    # Get whatever the qstat command said.
                    que = jobs[jobID]["R"]
                else:
                    # Not found by qstat (or not a jobID at all)
                    que = "."
            # Print info
            if qJobID and jobID in jobs:
                # Print job number.
                print(stncl % (i, frun, sts, itr, que, jobID))
            elif qJobID:
                # Print blank job number.
                print(stncl % (i, frun, sts, itr, que, ""))
            else:
                # No job number.
                print(stncl % (i, frun, sts, itr, que))
            # Check status.
            if qCheck or nSub >= nSubMax: continue
            # If submitting is allowed, check the job status.
            if sts in ['---', 'INCOMP']:
                # Prepare the job.
                self.PrepareCase(i)
                # Start (submit or run) case
                self.StartCase(i)
                # Increase job number
                nSub += 1
        # Extra line.
        print("")
        # State how many jobs submitted.
        if nSub:
            print("Submitted or ran %i job(s).\n" % nSub)
        # Status summary
        fline = ""
        for key in total:
            # Check for any cases with the status.
            if total[key]:
                # At least one with this status.
                fline += ("%s=%i, " % (key,total[key]))
        # Print the line.
        if fline: print(fline)
        
    # Function to start a case: submit or run
    def StartCase(self, i):
        """Start a case by either submitting it 
        
        This function checks whether or not a case is submittable.  If so, the
        case is submitted via :func:`pyCart.queue.pqsub`, and otherwise the
        case is started using a system call.
        
        It is assumed that the case has been prepared.
        
        :Call:
            >>> pbs = cart3d.StartCase(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of the case to check (0-based)
        :Outputs:
            *pbs*: :class:`int` or ``None``
                PBS job ID if submitted successfully
        :Versions:
            * 2014.10.06 ``@ddalle``: First version
        """
        # Check status.
        if self.CheckCase(i) is None:
            # Case not ready
            return
        elif self.CheckRunning(i):
            # Case already running!
            return
        # Safely go to root directory.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get case name and go to the folder.
        frun = self.x.GetFullFolderNames(i)
        os.chdir(frun)
        # Print status.
        print("     Starting case '%s'." % frun)
        # Start the case by either submitting or calling it.
        pbs = case.StartCase()
        # Display the PBS job ID if that's appropriate.
        if pbs:
            print("     Submitted job: %i" % pbs)
        # Go back.
        os.chdir(fpwd)
        # Output
        return pbs
            
    # Function to determine if case is PASS, ---, INCOMP, etc.
    def CheckCaseStatus(self, i, jobs={}):
        """Determine the current status of a case
        
        :Call:
            >>> sts = cart3d.CheckCaseStatus(i, jobs={})
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of the case to check (0-based)
            *jobs*: :class:`dict`
                Information on each job, ``jobs[jobID]`` for each submitted job
        :Versions:
            * 2014.10.04 ``@ddalle``: First version
            * 2014.10.06 ``@ddalle``: Checking queue status
        """
        # Current iteration count
        n = self.CheckCase(i)
        # Try to get a job ID.
        jobID = self.GetPBSJobID(i)
        # Check if the case is prepared.
        if n is None:
            # Nothing prepared.
            sts = "---"
        else:
            # Check if the case is running.
            if self.CheckRunning(i):
                # Case currently marked as running.
                sts = "RUN"
            else:
                # Get maximum iteration count.
                nMax = self.GetLastIter(i)
                # Check current count.
                if jobID in jobs:
                    # It's in the queue, but apparently not running.
                    if jobs[jobID]['R'] == "R":
                        # Job running according to the queue
                        sts = "RUN"
                    else:
                        # It's in the queue.
                        sts = "QUEUE"
                elif n >= nMax:
                    # Not running and sufficient iterations completed.
                    sts = "DONE"
                else:
                    # Not running and iterations remaining.
                    sts = "INCOMP"
        # Check if the case is marked as PASS
        if self.x.PASS[i]:
            # Check for cases marked but that can't be done.
            if sts == "DONE":
                # Passed!
                sts = "PASS"
            else:
                # Funky
                sts = "PASS*"
        # Output
        return sts
            
        
    # Function to check if the mesh for case i exists
    def CheckMesh(self, i):
        """Check if the mesh for case *i* is prepared.
        
        :Call:
            >>> q = cart3d.CheckMesh(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of the case to check (0-based)
        :Outputs:
            *q*: :class:`bool`
                Whether or not the mesh for case *i* is prepared
        :Versions:
            * 2014.09.29 ``@ddalle``: First version
        """
        # Check input.
        if type(i).__name__ != "int":
            raise TypeError(
                "Input to :func:`Cart3d.CheckMesh()` must be :class:`int`.")
        # Get the group name.
        fgrp = self.x.GetGroupFolderNames(i)
        # Initialize with "pass" setting.
        q = True
        # Remember current location.
        fpwd = os.getcwd()
        # Go to root folder.
        os.chdir(self.RootDir)
        # Check if the folder exists.
        if (not os.path.isdir(fgrp)):
            os.chdir(fpwd)
            return False
        # Go to the group folder.
        os.chdir(fgrp)
        # Check for group mesh.
        if not self.opts.get_GroupMesh():
            # Get the case name.
            frun = self.x.GetFolderNames(i)
            # Check if it's there.
            if (not os.path.isdir(frun)):
                os.chdir(fpwd)
                return False
            # Go to the folder.
            os.chdir(frun)
        # Go to working folder. ('.' or 'adapt??/')
        os.chdir(case.GetWorkingFolder())
        # Check for the surface file.
        if not os.path.isfile('Components.i.tri'): q = False
        # Check for which mesh file to look for.
        if q and self.opts.get_mg() > 0:
            # Look for the multigrid mesh
            if not os.path.isfile('Mesh.mg.c3d'): q = False
        else:
            # Look for the original mesh
            if not os.path.isfile('Mesh.c3d'): q = False
        # Return to original folder.
        os.chdir(fpwd)
        # Output.
        return q
        
    # Prepare the mesh for case i (if necessary)
    def PrepareMesh(self, i):
        """Prepare the mesh for case *i* if necessary.
        
        :Call:
            >>> q = cart3d.PrepareMesh(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of the case to check (0-based)
        :Versions:
            * 2014.09.29 ``@ddalle``: First version
        """
        # ---------
        # Case info
        # ---------
        # Get the case name.
        frun = self.x.GetFullFolderNames(i)
        # Get name of group.
        fgrp = self.x.GetGroupFolderNames(i)
        # Check the mesh.
        if self.CheckMesh(i):
            return None
        # ------------------
        # Folder preparation
        # ------------------
        # Remember current location.
        fpwd = os.getcwd()
        # Go to root folder.
        os.chdir(self.RootDir)
        # Check for the group folder and make it if necessary.
        if not os.path.isdir(fgrp):
            os.mkdir(fgrp, dmask)
        # Check for groups with common meshes
        if self.opts.get_GroupMesh():
            # Get the group index.
            j = self.x.GetGroupIndex(i)
            # Status update
            print("  Group name: '%s' (index %i)" % (fgrp,j))
            # Go there.
            os.chdir(fgrp)
        else:
            # Check if the run folder exists.
            if not os.path.isdir(frun):
                os.mkdir(frun, dmask)
            # Status update.
            print("  Case name: '%s' (index %i)" % (frun,i))
            # Go there.
            os.chdir(frun)
        # ----------
        # Copy files
        # ----------
        # Get the name of the configuration file.
        fxml = os.path.join(self.RootDir, self.opts.get_ConfigFile())
        fpre = os.path.join(self.RootDir, self.opts.get_preSpecCntl())
        fc3d = os.path.join(self.RootDir, self.opts.get_inputC3d())
        # Copy the config file.
        if os.path.isfile(fxml):
            shutil.copyfile(fxml, 'Config.xml')
        # Copy the preSpec file.
        if os.path.isfile(fpre):
            shutil.copyfile(fpre, 'preSpec.c3d.cntl')
        # Copy the cubes input file.
        if os.path.isfile(fc3d):
            shutil.copyfile(fc3d, 'input.c3d')
        # ------------------
        # Triangulation prep
        # ------------------
        # Status update
        print("  Preparing surface triangulation...")
        # Read the mesh.
        self.ReadTri()
        # Copy the original mesh.
        self.tri0 = self.tri.Copy()
        # Get function for rotations, etc.
        keys = self.x.GetKeysByType('TriFunction')
        # Get the list of functions.
        funcs = [self.x.defns[key]['Function'] for key in keys] 
        # Loop through the functions.
        for (key, func) in zip(keys, funcs):
            # Apply it.
            exec("%s(self,%s,i=%i)" % (func, getattr(self.x,key)[i], i))
        # Write the tri file.
        self.tri.Write('Components.i.tri')
        # --------------------
        # Volume mesh creation
        # --------------------
        # Run autoInputs if necessary.
        if self.opts.get_r():
            # Run autoInputs
            bin.autoInputs(self)
        # Read the resulting preSpec.c3d.cntl file
        self.PreSpecCntl = PreSpecCntl('preSpec.c3d.cntl')
        # Bounding box control...
        self.PreparePreSpecCntl()
        # Run cubes.
        bin.cubes(self)
        # Run mgPrep
        bin.mgPrep(self)
        # Reset the mesh to the original.
        self.tri = self.tri0
        # Return to original folder.
        os.chdir(fpwd)
        
    # Check a case.
    def CheckCase(self, i):
        """Check current status of run *i*
        
        :Call:
            >>> n = cart3d.CheckCase(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of the case to check (0-based)
        :Outputs:
            *n*: :class:`int` or ``None``
                Number of completed iterations or ``None`` if not set up
        :Versions:
            * 2014.09.27 ``@ddalle``: First version
        """
         # Check input.
        if type(i).__name__ != "int":
            raise TypeError(
                "Input to :func:`Cart3d.CheckCase()` must be :class:`int`.")
        # Get the group name.
        frun = self.x.GetFullFolderNames(i)
        # Remember current location.
        fpwd = os.getcwd()
        # Go to root folder.
        os.chdir(self.RootDir)
        # Initialize iteration number.
        n = 0
        # Check if the folder exists.
        if (not os.path.isdir(frun)): n = None
        # Check that test.
        if n is not None:
            # Go to the group folder.
            os.chdir(frun)
            # Check for the surface file.
            if not os.path.isfile('Components.i.tri'): n = None
            # Input file.
            if not os.path.isfile('input.00.cntl'): n=None
            # Settings file.
            if not os.path.isfile('case.json'): n=None
            # Check for which mesh file to look for.
            if os.path.isdir('adapt00') or os.path.islink('BEST'):
                # Mesh file is gone; but it exists somewhere else
                pass
            elif self.opts.get_mg() > 0:
                # Look for the multigrid mesh
                if not os.path.isfile('Mesh.mg.c3d'): n = None
            else:
                # Look for the original mesh
                if not os.path.isfile('Mesh.c3d'): n = None
        # Output if None
        if n is None:
            # Go back to starting point.
            os.chdir(fpwd)
            # Quit.
            return None
        # Get working directory
        fwork = case.GetWorkingDirectory()
        # Get the iteration number.
        n = case.GetHistoryIter(os.path.join(fwork, 'history.dat'))
        # Return to original folder.
        os.chdir(fpwd)
        # Output.
        return n
        
        
    # Prepare a case.
    def PrepareCase(self, i):
        """Prepare case for running if necessary
        
        :Call:
            >>> n = cart3d.PrepareCase(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Index of case to analyze
        :Versions:
            * 2014-09-30 ``@ddalle``: First version
        """
        # Prepare the mesh.
        self.PrepareMesh(i)
        # Get the existing status.
        n = self.CheckCase(i)
        # Quit if prepared.
        if n is not None: return None
        # Get the run name.
        frun = self.x.GetFullFolderNames(i)
        # Save current location.
        fpwd = os.getcwd()
        # Go to root folder.
        os.chdir(self.RootDir)
        # Check for the run directory.
        if not os.path.isdir(frun): os.mkdir(frun, dmask)
        # Go there.
        os.chdir(frun)
        # Write the conditions to a simple JSON file.
        self.x.WriteConditionsJSON(i)
        # Different processes for GroupMesh and CaseMesh
        if self.opts.get_GroupMesh():
            # Copy the required files.
            for fname in ['input.c3d', 'Mesh.c3d.Info', 'Config.xml']:
                # Source path.
                fsrc = os.path.join('..', fname)
                # Check for the file.
                if os.path.isfile(fsrc):
                    # Copy it.
                    shutil.copy(fsrc, fname)
            # Create links that are available.
            for fname in ['Components.i.tri', 'Mesh.c3d', 'Mesh.mg.c3d',
                    'Mesh.R.c3d']:
                # Source path.
                fsrc = os.path.join(os.path.abspath('..'), fname)
                # Remove the file if it's present.
                if os.path.isfile(fname):
                    os.remove(fname)
                # Check for the file.
                if os.path.isfile(fsrc):
                    # Create a symlink.
                    os.symlink(fsrc, fname)
        else:
            # Get the name of the configuration and input files.
            fxml = os.path.join(self.RootDir, self.opts.get_ConfigFile())
            fpre = os.path.join(self.RootDir, self.opts.get_preSpecCntl())
            fc3d = os.path.join(self.RootDir, self.opts.get_inputC3d())
            # Copy the config file.
            if os.path.isfile(fxml):
                shutil.copy(fxml, 'Config.xml')
            # Copy the preSpec file.
            if os.path.isfile(fpre):
                shutil.copy(fpre, 'preSpec.c3d.cntl')
            # Copy the input.c3d file.
            if os.path.isfile(fc3d):
                shutil.copy(fc3d, 'input.c3d')
        # Get function for setting boundary conditions, etc.
        keys = self.x.GetKeysByType('CaseFunction')
        # Get the list of functions.
        funcs = [self.x.defns[key]['Function'] for key in keys] 
        # Loop through the functions.
        for (key, func) in zip(keys, funcs):
            # Apply it.
            exec("%s(self,%s,i=%i)" % (func, getattr(self.x,key)[i], i))
        # Write the input.cntl and aero.csh file(s).
        self.PrepareInputCntl(i)
        self.PrepareAeroCsh(i)
        # Write a JSON file with the flowCart settings.
        f = open('case.json', 'w')
        # Dump the flowCart settings.
        json.dump(self.opts['flowCart'], f, indent=1)
        # Close the file.
        f.close()
        # Write the PBS script.
        self.WritePBS(i)
        # Return to original location.
        os.chdir(fpwd)
        
    # Get last iter
    def GetLastIter(self, i):
        """Get minimum required iteration for a given run to be completed
        
        :Call:
            >>> nIter = cart3d.GetLastIter(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Run index
        :Outputs:
            *nIter*: :class:`int`
                Number of iterations required for case *i*
        :Versions:
            * 2014.10.03 ``@ddalle``: First version
        """
        # Check the case
        if self.CheckCase(i) is None:
            return None
        # Safely go to root directory.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get the case name.
        frun = self.x.GetFullFolderNames(i)
        # Go there.
        os.chdir(frun)
        # Read the local case.json file.
        fc = case.ReadCaseJSON()
        # Return to original location.
        os.chdir(fpwd)
        # Output
        return fc.get_LastIter()
        
    # Get PBS name
    def GetPBSName(self, i):
        """Get PBS name for a given case
        
        :Call:
            >>> lbl = cart3d.GetPBSName(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Run index
        :Outputs:
            *lbl*: :class:`str`
                Short name for the PBS job, visible via `qstat`
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        # Extract the trajectory.
        x = self.x
        # Initialize label.
        lbl = ''
        # Loop through keys.
        for k in x.keys[0:]:
            # Skip it if not part of the label.
            
            # Check for strings.
            if x.defns[k]['Value'] == 'float':
                # Use two decimals for first key.
                if k == x.keys[0]:
                    # Gets two decimals
                    slbl = '%s%.2f'
                else:
                    # Single-decimal
                    slbl = '%s%.1f'
                # Append to the label with only one decimal
                lbl += (slbl % (x.abbrv[k], getattr(x,k)[i]))
            elif x.defns[k]['Value'] == 'int':
                # Append to the label.
                lbl += ('%s%i' % (x.abbrv[k], getattr(x,k)[i]))
        # Check length.
        if len(lbl) > 15:
            # 16-char limit (or is it 15?)
            lbl = lbl[:15]
        # Output
        return lbl
        
    # Get PBS job ID if possible
    def GetPBSJobID(self, i):
        """Get PBS job number if one exists
        
        :Call:
            >>> pbs = cart3d.GetPBSJobID(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Run index
        :Outputs:
            *pbs*: :class:`int` or ``None``
                Most recently reported job number for case *i*
        :Versions:
            * 2014.10.06 ``@ddalle``: First version
        """
        # Check the case.
        if self.CheckCase(i) is None: return None
        # Go to the root folder
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get the run name.
        frun = self.x.GetFullFolderNames(i)
        # Go there.
        os.chdir(frun)
        # Check for a "jobID.dat" file.
        if os.path.isfile('jobID.dat'):
            # Read the file.
            try:
                # Open the file and read the first line.
                line = open('jobID.dat').readline()
                # Get the job ID.
                pbs = int(line.split()[0])
            except Exception:
                # Unsuccessful reading for some reason.
                pbs = None
        else:
            # No file.
            pbs = None
        # Return to original directory.
        os.chdir(fpwd)
        # Output
        return pbs
        
    # Check if a case is running.
    def CheckRunning(self, i):
        """Check if a case is currently running
        
        :Call:
            >>> q = cart3d.CheckRunning(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Run index
        :Outputs:
            *q*: :class:`bool`
                If ``True``, case has :file:`RUNNING` file in it
        :Versions:
            * 2014.10.03 ``@ddalle``: First version
        """
        # Safely go to root.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get run name
        frun = self.x.GetFullFolderNames(i)
        # Check for folder.
        if not os.path.isfile(os.path.join(frun, 'RUNNING')):
            # No file (or possibly no folder)
            return False
        else:
            # File exists.
            return True
        
        
    # Write the PBS script.
    def WritePBS(self, i):
        """Write the PBS script for a given case
        
        :Call:
            >>> cart3d.WritePBS(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of control class containing relevant parameters
            *i*: :class:`int`
                Run index
        :Versions:
            * 2014.09.30 ``@ddalle``: First version
        """
        # Get the case name.
        frun = self.x.GetFullFolderNames(i)
        # Remember current location.
        fpwd = os.getcwd()
        # Go to the root directory.
        os.chdir(self.RootDir)
        # Make folder if necessary.
        if not os.path.isdir(frun): os.mkdir(frun, dmask)
        # Go to the folder.
        os.chdir(frun)
        
        # Initialize the PBS script.
        f = open('run_cart3d.pbs', 'w')
        # Get the shell path (must be bash)
        sh = self.opts.get_PBS_S()
        # Write to script both ways.
        f.write('#!%s\n' % sh)
        f.write('#PBS -S %s\n' % sh)
        # Get the shell name.
        lbl = self.GetPBSName(i)
        # Write it to the script
        f.write('#PBS -N %s\n' % lbl)
        # Get the rerun status.
        PBS_r = self.opts.get_PBS_r()
        # Write if specified.
        if PBS_r: f.write('#PBS -r %s\n' % PBS_r)
        # Get the option for combining STDIO/STDOUT
        PBS_j = self.opts.get_PBS_j()
        # Write if specified.
        if PBS_j: f.write('#PBS -j %s\n' % PBS_j)
        # Get the number of nodes, etc.
        nnode = self.opts.get_PBS_select()
        ncpus = self.opts.get_PBS_ncpus()
        nmpis = self.opts.get_PBS_mpiprocs()
        smodl = self.opts.get_PBS_model()
        # Form the -l line.
        line = '#PBS -l select=%i:ncpus=%i' % (nnode, ncpus)
        # Add other settings
        if nmpis: line += (':mpiprocs=%i' % nmpis)
        if smodl: line += (':model=%s' % smodl)
        # Write the line.
        f.write(line + '\n')
        # Get the walltime.
        t = self.opts.get_PBS_walltime()
        # Write it.
        f.write('#PBS -l walltime=%s\n' % t)
        # Check for a group list.
        PBS_W = self.opts.get_PBS_W()
        # Write if specified.
        if PBS_W: f.write('#PBS -W %s\n' % PBS_W)
        # Get the queue.
        PBS_q = self.opts.get_PBS_q()
        # Write it.
        if PBS_q: f.write('#PBS -q %s\n\n' % PBS_q)
        
        # Go to the working directory.
        f.write('# Go to the working directory.\n')
        f.write('cd %s\n\n' % os.getcwd())
        
        # Write a header for the shell commands.
        f.write('# Additional shell commands\n')
        # Loop through the shell commands.
        for line in self.opts.get_ShellCmds():
            # Write it.
            f.write('%s\n' % line)
        
        # Simply call the advanced interface.
        f.write('\n# Call the flow_cart/mpi_flowCart/aero.csh interface.\n')
        f.write('run_flowCart.py')
        
        # Close the file.
        f.close()
        # Return.
        os.chdir(fpwd)
        
    # Function to prepare "input.cntl" files
    def PreparePreSpecCntl(self):
        """
        Prepare and write :file:`preSpec.c3d.cntl` according to the current
        settings and in the current folder.
        
        :Call:
            >>> cart3d.PreparePreSpecCntl()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Versions:
            * 2014.10.08 ``@ddalle``: First version
        """
        # Loop through BBoxes
        for BBox in self.opts.get_BBox():
            # Safely get number of refinements.
            n = BBox.get("n", 7)
            # Filter the type.
            if "compID" in BBox:
                # Bounding box specified relative to a component.
                xlim = self.tri.GetCompBBox(**BBox)
            else:
                # Bounding box coordinates given.
                xlim = BBox.get("xlim")
            # Check for degeneracy.
            if (not n) or (xlim is None): continue
            # Add the bounding box.
            self.PreSpecCntl.AddBBox(n, xlim)
        # Loop through the XLevs
        for XLev in self.opts.get_XLev():
            # Safely extract info from the XLev.
            n = XLev.get("n", 0)
            compID = XLev.get("compID", [])
            # Process it into a list of integers (if not already).
            compID = self.tri.config.GetCompID(compID)
            # Check for degeneracy.
            if (not n) or (not compID): continue
            # Add an XLev line.
            self.PreSpecCntl.AddXLev(n, compID)
        # Write the file.
        self.PreSpecCntl.Write('preSpec.c3d.cntl')
        
    # Function to archive 'adaptXX/' folders (except for newest)
    def TarAdapt(self):
        """Tar ``adaptNN/`` folders except for most recent one
        
        :Call:
            >>> cart3d.TarAdapt()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Versions:
            * 2014-11-14 ``@ddalle``: First version
        """
        # Save current path.
        fpwd = os.getcwd()
        # Get folder names.
        fruns = self.x.GetFullFolderNames()
        # Loop through folders.
        for frun in fruns:
            # Go to folder.
            os.chdir(self.RootDir)
            os.chdir(frun)
            # Manage the directory.
            manage.TarAdapt()
        # Go back to original directory.
        os.chdir(fpwd)
    
    # Function to prepare "input.cntl" files
    def PrepareInputCntl(self, i):
        """
        Write :file:`input.cntl` for run case *i* in the appropriate folder
        and with the appropriate settings.
        
        :Call:
            >>> cart3d.PrepareInputCntl(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
            *i*: :class:`int`
                Run index
        :Versions:
            * 2014.06.04 ``@ddalle``: First version
            * 2014.06.06 ``@ddalle``: Low-level functionality for grid folders
            * 2014.09.30 ``@ddalle``: Changed to write only a single case
        """
        # Extract trajectory.
        x = self.x
        # Process the key types.
        KeyTypes = [x.defns[k]['Type'] for k in x.keys]
        # Set the options.
        self.InputCntl.SetCFL(self.opts.get_cfl())
        
        # Set the flight conditions.
        # Mach number
        for k in x.GetKeysByType('Mach'):
            self.InputCntl.SetMach(getattr(x,k)[i])
        # Angle of attack
        if 'alpha' in KeyTypes:
            # Find out which 
            k = x.keys[KeyTypes.index('alpha')]
            # Set the value.
            self.InputCntl.SetAlpha(getattr(x,k)[i])
        # Sideslip angle
        if 'beta' in KeyTypes:
            # Find out which key it is.
            k = x.keys[KeyTypes.index('beta')]
            # Set the value.
            self.InputCntl.SetBeta(getattr(x,k)[i])
        # Set reference values.
        self.InputCntl.SetReferenceArea(self.opts.get_RefArea())
        self.InputCntl.SetReferenceLength(self.opts.get_RefLength())
        self.InputCntl.SetMomentPoint(self.opts.get_RefPoint())
        # Go safely to root folder.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get the case.
        frun = self.x.GetFullFolderNames(i)
        # Make folder if necessary.
        if not os.path.isdir(frun): os.mkdir(frun, dmask)
        # Get the cut planes.
        XSlices = self.opts.get_Xslices()
        YSlices = self.opts.get_Yslices()
        ZSlices = self.opts.get_Zslices()
        # Process cut planes
        if XSlices: self.InputCntl.SetXSlices(XSlices)
        if YSlices: self.InputCntl.SetYSlices(YSlices)
        if ZSlices: self.InputCntl.SetZSlices(ZSlices)
        # Loop through the output functional 'optForce's
        for Name, kw in self.opts.get_optForces().items():
            # Set the force.
            self.InputCntl.SetOutputForce(Name, **kw)
        
        # Loop through the runs.
        for j in range(self.opts.get_nSeq()):
            # Get the first-order status.
            fo = self.opts.get_first_order(j)
            # Set the status.
            if fo:
                # Run `flowCart` in first-order mode (everywhere)
                self.InputCntl.SetFirstOrder()
            else:
                # Run `flowCart` in second-order mode (cut cells are separate)
                self.InputCntl.SetSecondOrder()
            # Get robust mode.
            if self.opts.get_robust_mode(j):
                # Set robust mode.
                self.InputCntl.SetRobustMode()
            # Name of output file.
            fout = os.path.join(frun, 'input.%02i.cntl' % j)
            # Write the input file.
            self.InputCntl.Write(fout)
        # Return to original path.
        os.chdir(fpwd)
        
    # Function prepare the aero.csh files
    def PrepareAeroCsh(self, i):
        """
        Write :file:`aero.csh` for run case *i* in the appropriate folder and
        with the appropriate settings.
        
        :Call:
            >>>car3d.PrepareAeroCsh(i)
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
            *i*: :class:`int`
                Run idnex
        :Versions:
            * 2014.06.10 ``@ddalle``: First version
            * 2014.10.03 ``@ddalle``: Version 2.0
        """
        # Test if it's present (not required)
        try:
            self.AeroCsh
        except Exception:
            return
        # Safely go to the root folder.
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Get the case.
        frun = self.x.GetFullFolderNames(i)
        # Make folder if necessary.
        if not os.path.isdir(frun): os.mkdir(frun, dmask)
        # Loop through the run sequence.
        for j in range(self.opts.get_nSeq()):
            # Only write aero.csh for adaptive cases.
            if not self.opts.get_use_aero_csh(j): continue
            # Process global options
            self.AeroCsh.SetCFL(self.opts.get_cfl(j))
            self.AeroCsh.SetCFLMin(self.opts.get_cflmin(j))
            self.AeroCsh.SetnIter(self.opts.get_it_fc(j))
            self.AeroCsh.SetnIterAdjoint(self.opts.get_it_ad(j))
            self.AeroCsh.SetnAdapt(self.opts.get_n_adapt_cycles(j))
            self.AeroCsh.SetnRefinements(self.opts.get_maxR(j))
            self.AeroCsh.SetFlowCartMG(self.opts.get_mg_fc(j))
            self.AeroCsh.SetAdjointCartMG(self.opts.get_mg_ad(j))
            self.AeroCsh.SetFMG(self.opts.get_fmg(j))
            self.AeroCsh.SetPMG(self.opts.get_pmg(j))
            self.AeroCsh.SetAdjFirstOrder(self.opts.get_adj_first_order(j))
            self.AeroCsh.SetLimiter(self.opts.get_limiter(j))
            self.AeroCsh.SetYIsSpanwise(self.opts.get_y_is_spanwise(j))
            self.AeroCsh.SetABuffer(self.opts.get_abuff(j))
            self.AeroCsh.SetFinalMeshXRef(self.opts.get_final_mesh_xref(j))
            self.AeroCsh.SetBinaryIO(self.opts.get_binaryIO(j))
            # Process the adaptation-specific lists.
            self.AeroCsh.SetAPC(self.opts.get_apc())
            self.AeroCsh.SetMeshGrowth(self.opts.get_mesh_growth())
            self.AeroCsh.SetnIterList(self.opts.get_ws_it())
            # Destination file name
            fout = os.path.join(frun, 'aero.%02i.csh' % j)
            # Write the input file.
            self.AeroCsh.Write(fout)
            # Make it executable.
            os.chmod(fout, dmask)
        # Go back home.
        os.chdir(fpwd)
        # Done
        return None
        
    # Function to read "loadsCC.dat" files
    def GetLoadsCC(self):
        """Read all available 'loadsCC.dat' files.
        
        :Call:
            >>> cart3d.GetLoadsCC()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Effects:
            Creates *cart3d.LoadsCC* instance
        :Versions:
            * 2014.06.05 ``@ddalle``: First version
        """
        # Call the constructor.
        self.LoadsCC = LoadsDat(self, fname="loadsCC.dat")
        return None
        
    # Function to write "loadsCC.csv"
    def WriteLoadsCC(self):
        """Write gathered loads to CSV file to "loadsCC.csv"
        
        :Call:
            >>> cart3d.WriteLoadsCC()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Versions:
            * 2014.06.04 ``@ddalle``: First version
        """
        # Check for the attribute.
        if not hasattr(self, 'LoadsCC'):
            self.GetLoadsCC()
        # Write.
        self.LoadsCC.Write(self.x)
        return None
        
    # Function to read "loadsCC.dat" files
    def GetLoadsTRI(self):
        """Read all available 'loadsTRI.dat' files.
        
        :Call:
            >>> cart3d.GetLoadsTRI()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Effects:
            Creates *cart3d.LoadsCC* instance
        :Versions:
            * 2014.06.04 ``@ddalle``: First version
        """
        # Call the constructor.
        self.LoadsTRI = LoadsDat(self, fname="loadsTRI.dat")
        return None
        
    # Function to write "loadsCC.csv"
    def WriteLoadsTRI(self):
        """Write gathered loads to CSV file to "loadsTRI.csv"
        
        :Call:
            >>> cart3d.WriteLoadsTRI()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Instance of global pyCart settings object
        :Versions:
            * 2014.06.04 ``@ddalle``: First version
        """
        # Check for the attribute.
        if not hasattr(self, 'LoadsTRI'):
            self.GetLoadsTRI()
        # Write.
        self.LoadsTRI.Write(self.x)
        return None
    
    
    
    # Check for root location
    def CheckRootDir(self):
        """Check if the current directory is the case root directory
        
        Suppose the directory structure for a case is as follows.
        
        * `/nobackup/uuser/plane/`
            * `Grid_d0.0/`
                * `m1.20/`
                * `m1.40/`
            * `Grid_d1.0/`
                * `m1.20/`
                * `m1.40/`
                
        Then this function will return ``True`` if and only if the current
        working directory is ``'/nobackup/uuser/plane/'``.
        
        :Call:
            >>> q = cart3d.CheckRootDir()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Global pyCart settings object instance
        :Outputs:
            *q*: :class:`bool`
                True if current working directory is the case root directory
        :Versions:
            * 2014.06.30 ``@ddalle``: First version
        """
        # Compare the working directory and the stored root directory.
        return os.path.abspath('.') == self.RootDir
    
    # Check for group location
    def CheckGroupDir(self):
        """
        Check if the current directory is a group-level directory
        
        Suppose the directory structure for a case is as follows.
        
        * `/nobackup/uuser/plane/`
            * `Grid_d0.0/`
                * `m1.20/`
                * `m1.40/`
            * `Grid_d1.0/`
                * `m1.20/`
                * `m1.40/`
                
        Then this function will return ``True`` if and only if the current
        working directory is ``'/nobackup/uuser/plane/Grid_d0.0'`` or 
        ``'/nobackup/uuser/plane/Grid_d1.0'``.
        
        :Call:
            >>> q = cart3d.CheckGroupDir()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Global pyCart settings object instance
        :Outputs:
            *q*: :class:`bool`
                True if current working directory is a group-level directory
        :Versions:
            * 2014.06.30 ``@ddalle``: First version
        """
        # Compare the working directory and the stored root directory.
        return os.path.abspath('..') == self.RootDir
    
    # Check for group location
    def CheckCaseDir(self):
        """
        Check if the current directory is a case-level directory
        
        Suppose the directory structure for a case is as follows.
        
        * `/nobackup/uuser/plane/`
            * `Grid_d0.0/`
                * `m1.20/`
                * `m1.40/`
            * `Grid_d1.0/`
                * `m1.20/`
                * `m1.40/`
                
        Then this function will return ``True`` if the current working 
        directory is either of the ``'m1.20'`` or ``'m1.40'`` folders.
        
        :Call:
            >>> q = cart3d.CheckCaseDir()
        :Inputs:
            *cart3d*: :class:`pyCart.cart3d.Cart3d`
                Global pyCart settings object instance
        :Outputs:
            *q*: :class:`bool`
                True if current working directory is a group-level directory
        :Versions:
            * 2014.06.30 ``@ddalle``: First version
        """
        # Compare the working directory and the stored root directory.
        return os.path.abspath(os.path.join('..','..')) == self.RootDir
        


# Function to read conditions file.
def ReadTrajectoryFile(fname='Trajectory.dat', keys=['Mach','alpha','beta'],
    prefix="F"):
    """Read a simple list of configuration variables
    
    :Call:
        >>> x = pyCart.ReadTrajectoryFile(fname)
        >>> x = pyCart.ReadTrajectoryFile(fname, keys)
    :Inputs:
        *fname*: :class:`str`
            Name of file to read, defaults to ``'Trajectory.dat'``
        *keys*: :class:`list` of :class:`str` items
            List of variable names, defaults to ``['Mach','alpha','beta']``
        *prefix*: :class:`str`
            Header for name of each folder
    :Outputs:
        *x*: :class:`pyCart.trajectory.Trajectory`
            Instance of the pyCart trajectory class
    :Versions:
        * 2014.05.27 ``@ddalle``: First version
    """
    return Trajectory(fname, keys, prefix)
    

