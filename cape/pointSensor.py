"""
Point sensors module: :mod:`cape.pointSensor`
===============================================

This module contains a class for reading and averaging point sensors.  It is not
included in the :mod:`cape.dataBook` module in order to give finer import
control when used in other modules.

Point sensors are set into groups, so the ``"DataBook"`` section of the JSON
file may have a point sensor group called ``"P1"`` that includes points
``"p1"``, ``"p2"``, and ``"p3"``.

If a data book is read in as *DB*, the point sensor group *DBP* for group
``"P1"`` and the point sensor *p1* are obtained using the commands below.

    .. code-block:: python
    
        // Point sensor group
        DBP = DB.PointSensors["P1"]
        // Individual point sensor
        p1 = DBP["p1"]
"""

# File interface
import os, glob
# Basic numerics
import numpy as np
# Date processing
from .options   import odict
# Utilities and advanced statistics
from . import util
from . import case
from . import dataBook

# Basis module
from . import dataBook

# Placeholder variables for plotting functions.
plt = 0

# Dedicated function to load Matplotlib only when needed.
def ImportPyPlot():
    """Import :mod:`matplotlib.pyplot` if not loaded
    
    :Call:
        >>> cape.dataBook.ImportPyPlot()
    :Versions:
        * 2014-12-27 ``@ddalle``: First version
    """
    # Make global variables
    global plt
    global tform
    global Text
    # Check for PyPlot.
    try:
        plt.gcf
    except AttributeError:
        # Load the modules.
        import matplotlib.pyplot as plt
        import matplotlib.transforms as tform
        from matplotlib.text import Text
# def ImportPyPlot


# Data book for group of point sensors
class DBPointSensorGroup(dataBook.DBBase):
    """
    Point sensor group data book
    
    :Call:
        >>> DBPG = DBPointSensorGroup(x, opts, name)
    :Inputs:
        *x*: :class:`cape.trajectory.Trajectory`
            Trajectory/run matrix interface
        *opts*: :class:`cape.options.Options`
            Options interface
        *name*: :class:`str` | ``None``
            Name of data book item (defaults to *pt*)
        *pts*: :class:`list` (:class:`str`) | ``None``
            List of points to read, by default all points in the group
        *RootDir*: :class:`str` | ``None``
            Project root directory absolute path, default is *PWD*
    :Outputs:
        *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
            A point sensor group data book
    :Versions:
        * 2015-12-04 ``@ddalle``: First version
    """
  # ==========
  # Config
  # ==========
  # <
    # Initialization method
    def __init__(self, x, opts, name, **kw):
        """Initialization method
        
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Save root directory
        self.RootDir = kw.get('RootDir', os.getcwd())
        # Save the interface.
        self.x = x
        self.opts = opts
        # Save the name
        self.name = name
        # Get the list of points.
        self.pts = kw.get('pts', opts.get_DBGroupPoints(name))
        # Loop through the points.
        for pt in self.pts:
            self[pt] = DBPointSensor(x, opts, pt, name)
            
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Initialize string
        lbl = "<DBPointSensorGroup %s, " % self.name
        # Number of cases in book
        lbl += "nPoint=%i>" % len(self.pts)
        # Output
        return lbl
    __str__ = __repr__
  # >
  
  # ======
  # I/O
  # ======
  # <
    # Output method
    def Write(self):
        """Write to file each point sensor data book in a group
        
        :Call:
            >>> DBPG.Write()
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                A point sensor group data book
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Loop through points
        for pt in self.pts:
            # Sort it.
            self[pt].Sort()
            # Write it
            self[pt].Write()
  # >
  
  # ==========
  # Case I/O
  # ==========
  # <
    # Read case point data
    def ReadCasePoint(self, pt):
        """Read point data from current run folder
        
        :Call:
            >>> P = DBPG.ReadCasePoint(pt)
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointGroup`
                Point sensor group data book
            *pt*: :class:`str`
                Name of point to read
        :Outputs:
            *P*: :class:`dict`
                Dictionary of state variables as requested from the point
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        # Read data from a custom file
        pass
  # >
  
  # ============
  # Updaters
  # ============
  # <
   # -------
   # Config
   # -------
   # [
    # Process list of components
    def ProcessComps(self, pt=None, **kw):
        """Process list of points
        
        This performs several conversions:
        
            ============   ===================
            *comp*         Output
            ============   ===================
            ``None``       ``DBPG.pts``
            :class:`str`   ``pt.split(',')``
            :class:`list`  ``pt``
            ============   ===================
        
        :Call:
            >>> DBPG.ProcessComps(pt=None)
        :Inputs:
            *DB*: :class:`cape.dataBook.DataBook`
                Point sensor group data book
            *pt*: {``None``} | :class:`list` (:class:`str`) | :class:`str`
                Point name or list of point names
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        # Get type
        t = type(pt).__name__
        # Default list of components
        if pt is None:
            # Default: all components
            return self.pts
        elif t in ['str', 'unicode']:
            # Split by comma (also ensures list)
            return pt.split(',')
        elif t in ['list', 'ndarray']:
            # Already a list?
            return pt
        else:
            # Unknown
            raise TypeError("Cannot process point list with type '%s'" % t)
   # ]
   
   # -----------
   # Update/Add
   # -----------
   # [
    # Update data book
    def Update(self, I=None, pt=None):
        """Update the data book for a list of cases from the run matrix
        
        :Call:
            >>> DBPG.UpdateDataBook(I=None, pt=None)
        :Inputs:
            *DBPG*: :class:`cape.dataBook.DBPointGroup`
                Point sensor group data book
            *I*: :class:`list` (:class:`int`) | ``None``
                List of trajectory indices or update all cases in trajectory
            *pt*: {``None``} | :class:`list` (:class:`str`) | :class:`str`
                Point name or list of point names
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        # Default indices (all)
        if I is None:
            # Use all trajectory points
            I = range(self.x.nCase)
        # Process list of components
        pts = self.ProcessComps(pt=pt)
        # Loop through points
        for pt in pts:
            # Check type
            if pt not in self.pts: continue
            # Status update
            print("Point '%s' ..." % pt)
            # Save location
            fpwd = os.getcwd()
            # Go to root dir
            os.chdir(self.RootDir)
            # Start counter
            n = 0
            # Loop through indices
            for i in I:
                try:
                    # See if it can be udated
                    n += self.UpdateCasePoint(i, pt)
                except Excaption as e:
                    # Print error message and move on
                    print("update failed: %s" % e.message)
            # Return to original location
            os.chdir(fpwd)
            # Move on to next component if no updates
            if n == 0:
                # Unlock
                self[pt].Unlock()
                continue
            # Status update
            print("Writing %i new or updated entries" % n)
            # Sort the point 
            self[pt].Sort()
            # Write it
            self[pt].Write(merge=True, unlock=True)
    
    # Update or add an entry for one component
    def UpdateCaseComp(self, i, pt):
        """Update or add a case to a point data book
        
        The history of a run directory is processed if either one of three
        criteria are met.
        
            1. The case is not already in the data book
            2. The most recent iteration is greater than the data book value
            3. The number of iterations used to create statistics has changed
        
        :Call:
            >>> n = DBPG.UpdateCaseComp(i, pt)
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                Point sensor group data book
            *i*: :class:`int`
                Trajectory index
            *pt*: :class:`str`
                Name of point
        :Outputs:
            *n*: ``0`` | ``1``
                How many updates were made
        :Versions:
            * 2014-12-22 ``@ddalle``: First version
            * 2017-04-12 ``@ddalle``: Modified to work one component
            * 2017-04-23 ``@ddalle``: Added output
            * 2017-10-10 ``@ddalle``: From :class:`cape.dataBook.DataBook`
        """
        # Check if it's present
        if pt not in self:
            raise KeyError("No point sensor '%s'" % pt)
        # Get the first data book component.
        DBc = self[comp]
        # Try to find a match existing in the data book.
        j = DBc.FindMatch(i)
        # Get the name of the folder.
        frun = self.x.GetFullFolderNames(i)
        # Status update.
        print(frun)
        # Go home.
        os.chdir(self.RootDir)
        # Check if the folder exists.
        if not os.path.isdir(frun):
            # Nothing to do.
            return 0
        # Go to the folder.
        os.chdir(frun)
        # Get the current iteration number.
        nIter = self.GetCurrentIter()
        # Get the number of iterations used for stats.
        nStats = self.opts.get_nStats()
        # Get the iteration at which statistics can begin.
        nMin = self.opts.get_nMin()
        # Process whether or not to update.
        if (not nIter) or (nIter < nMin + nStats):
            # Not enough iterations (or zero iterations)
            print("  Not enough iterations (%s) for analysis." % nIter)
            q = False
        elif np.isnan(j):
            # No current entry.
            print("  Adding new databook entry at iteration %i." % nIter)
            q = True
        elif DBc['nIter'][j] < nIter:
            # Update
            print("  Updating from iteration %i to %i."
                % (DBc['nIter'][j], nIter))
            q = True
        elif DBc['nStats'][j] < nStats:
            # Change statistics
            print("  Recomputing statistics using %i iterations." % nStats)
            q = True
        else:
            # Up-to-date
            print("  Databook up to date.")
            q = False
        # Check for an update
        if (not q): return 0
        # Maximum number of iterations allowed.
        nMax = min(nIter-nMin, self.opts.get_nMaxStats())
        # Read data
        P = self.ReadPoint(pt, i)
        
        # Save the data.
        if np.isnan(j):
            # Add to the number of cases.
            DBc.n += 1
            # Append trajectory values.
            for k in self.x.keys:
                # I hate the way NumPy does appending.
                DBc[k] = np.append(DBc[k], getattr(self.x,k)[i])
            # Append values.
            for c in DBc.DataCols:
                DBc[c] = np.hstack((DBc[c], [P[c]]))
            # Append iteration counts.
            if 'nIter' in DBc:
                DBc['nIter']  = np.hstack((DBc['nIter'], [nIter]))
        else:
            # Save updated trajectory values
            for k in DBc.xCols:
                # Append to that column
                DBc[k][j] = getattr(self.x,k)[i]
            # Update data values.
            for c in DBc.DataCols:
                DBc[c][j] = P[c]
            # Update the other statistics.
            if 'nIter' in DBc:
                DBc['nIter'][j]   = nIter
        # Go back.
        os.chdir(self.RootDir)
        # Output
        return 1
   # ]
            
   # -------
   # Delete
   # -------
   # [
    # Function to delete entries by index
    def DeleteCases(self, I, pt=None):
        """Delete list of cases from point sensor data book
        
        :Call:
            >>> DBPG.Delete(I)
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                Point sensor group data book
            *I*: :class:`list` (:class:`int`)
                List of trajectory indices
            *pt*: {``None``} | :class:`list` (:class:`str`) | :class:`str`
                Point name or list of point names
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        # Default.
        if I is None: return
        # Process list of components
        pts = self.ProcessComps(pt=pt)
        # Loop through components
        for pt in pts:
            # Check if present
            if pt not in self.pts: continue
            # Perform deletions
            nj = self.DeleteCasesComp(I, comp)
            # Write the component
            if nj > 0:
                # Write cleaned-up data book
                self[comp].Write(unlock=True)
            else:
                # Unlock
                self[comp].Unlock()
        
    # Function to delete entries by index
    def DeleteCasesComp(self, I, pt):
        """Delete list of cases from data book
        
        :Call:
            >>> n = DBPG.Delete(I, pt)
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                Point sensor group data book
            *I*: :class:`list` (:class:`int`)
                List of trajectory indices or update all cases in trajectory
            *pt
        :Outputs:
            *n*: :class:`int`
                Number of deleted entries
        :Versions:
            * 2015-03-13 ``@ddalle``: First version
            * 2017-04-13 ``@ddalle``: Split by component
            * 2017-10-10 ``@ddalle``: From :class:`cape.dataBook.DataBook`
        """
        # Check if it's present
        if pt not in self:
            print("WARNING: No point sensor '%s'" % pt)
        # Get the first data book component.
        DBc = self[pt]
        # Number of cases in current data book.
        nCase = DBc.n
        # Initialize data book index array.
        J = []
        # Loop though indices to delete.
        for i in I:
            # Find the match.
            j = DBc.FindMatch(i)
            # Check if one was found.
            if np.isnan(j): continue
            # Append to the list of data book indices.
            J.append(j)
        # Number of deletions
        nj = len(J)
        # Exit if no deletions
        if nj == 0:
            return nj
        # Report status
        print("  Removing %s entries from point '%s'" % (nj, pt))
        # Initialize mask of cases to keep.
        mask = np.ones(nCase, dtype=bool)
        # Set values equal to false for cases to be deleted.
        mask[J] = False
        # Extract data book component.
        DBc = self[comp]
        # Loop through data book columns.
        for c in DBc.keys():
            # Apply the mask
            DBc[c] = DBc[c][mask]
        # Update the number of entries.
        DBc.n = len(DBc[DBc.keys()[0]])
        # Output
        return nj
    # ]
  # >
  
  # ============
  # Organization
  # ============
  # <
    # Sorting method
    def Sort(self):
        """Sort point sensor group
        
        :Call:
            >>> DBPG.Sort()
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                A point sensor group data book
        :Versions:
            * 2016-03-08 ``@ddalle``: First version
        """
        # Loop through points
        for pt in self.pts:
            self[pt].Sort()
            
    # Match the databook copy of the trajectory
    def UpdateTrajectory(self):
        """Match the trajectory to the cases in the data book
        
        :Call:
            >>> DBPG.UpdateTrajectory()
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
                A point sensor group data book
        :Versions:
            * 2015-05-22 ``@ddalle``: First version
        """
        # Get the first component.
        DBc = self[self.pts[0]]
        # Loop through the fields.
        for k in self.x.keys:
            # Copy the data.
            setattr(self.x, k, DBc[k])
            # Set the text.
            self.x.text[k] = [str(xk) for xk in DBc[k]]
        # Set the number of cases.
        self.x.nCase = DBc.n
  # >
# class DBPointSensorGroup


# Class for surface pressures pulled from triq
class DBTriqPointGroup(DBPointSensorGroup):
    """Post-processed point sensor group data book
    
    :Call:
        >>> DBPG = DBTriqPointGroup(x, opts, name, pts=None, RootDir=None)
    :Inputs:
        *x*: :class:`cape.trajectory.Trajectory`
            Trajectory/run matrix interface
        *opts*: :class:`cape.options.Options`
            Options interface
        *name*: :class:`str` | ``None``
            Name of data book group
        *pts*: {``None``} | :class:`list` (:class:`str`)
            List of points to read; defaults to all points in thegroup
        *RootDir*: {``None``} | :class:`str`
            Project root directory absolute path, default is *PWD*
    :Outputs:
        *DBPG*: :class:`cape.pointSensor.DBPointSensorGroup`
            A point sensor group data book
    :Versions:
        * 2017-10-10 ``@ddalle``: First version
    """
  # ==========
  # Config
  # ==========
  # <
    # Initialization method
    def __init__(self, x, opts, name, **kw):
        """Initialization method
        
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Save root directory
        self.RootDir = kw.get('RootDir', os.getcwd())
        # Save the interface.
        self.x = x
        self.opts = opts
        # Save the name
        self.name = name
        # Get the list of points.
        self.pts = kw.get('pts', opts.get_DBGroupPoints(name))
        # Loop through the points.
        for pt in self.pts:
            self[pt] = DBTriqPoint(x, opts, pt, name)
            
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Initialize string
        lbl = "<DBTriqPointGroup %s, " % self.name
        # Number of cases in book
        lbl += "nPoint=%i>" % len(self.pts)
        # Output
        return lbl
    __str__ = __repr__
  # >
  
  # ==========
  # Case I/O
  # ==========
  # <
    # Read case point data
    def ReadCasePoint(self, pt):
        """Read point data from current run folder
        
        :Call:
            >>> P = DBPG.ReadCasePoint(pt)
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBTriqPointGroup`
                Point sensor group data book
            *pt*: :class:`str`
                Name of point to read
        :Outputs:
            *P*: :class:`dict`
                Dictionary of state variables as requested from the point
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        # Read data from a custom file
        pass
    

    # Read Triq file from this folder
    def ReadCaseTriq(self):
        """Read the the most recent Triq file from this folder
        
        :Call:
            >>> triq, VarList = DBPG.ReadCaseTriq()
        :Inputs:
            *DBPG*: :class:`cape.pointSensor.DBTriqPointGroup`
                Point sensor group data book
        :Outputs:
            *triq*: :class:`cape.tri.Triq`
                Annotated triangulation interface
            *VarList*: :class:`list` (:class:`str`)
                List of variable names
        :Versions:
            * 2017-10-10 ``@ddalle``: First version
        """
        pass
  # >
# class DBTriqPointGroup



# Data book of point sensors
class DBPointSensor(dataBook.DBBase):
    """Point sensor data book
    
    Plotting methods are inherited from :class:`cape.dataBook.DBBase`,
    including :func:`cape.dataBook.DBBase.PlotHist` for plotting historgrams of
    point sensor results in particular.
    
    :Call:
        >>> DBP = DBPointSensor(x, opts, pt, name=None)
    :Inputs:
        *x*: :class:`cape.trajectory.Trajectory`
            Trajectory/run matrix interface
        *opts*: :class:`cape.options.Options`
            Options interface
        *pt*: :class:`str`
            Name of point
        *name*: :class:`str` | ``None``
            Name of data book item (defaults to *pt*)
        *RootDir*: :class:`str` | ``None``
            Project root directory absolute path, default is *PWD*
    :Outputs:
        *DBP*: :class:`pyCart.pointSensor.DBPointSensor`
            An individual point sensor data book
    :Versions:
        * 2015-12-04 ``@ddalle``: Started
    """
  # ========
  # Config
  # ========
  # <
    # Initialization method
    def __init__(self, x, opts, pt, name=None, **kw):
        """Initialization method
        
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        # Save relevant inputs
        self.x = x
        self.opts = opts
        self.pt = pt
        # Save data book title
        if name is None:
            # Default name
            self.comp = pt
        else:
            # Specified name
            self.comp = name
        
        # Save root directory
        self.RootDir = kw.get('RootDir', os.getcwd())
        # Folder containing the data book
        fdir = opts.get_DataBookDir()
        # Folder name for compatibility
        fdir = fdir.replace("/", os.sep)
        fdir = fdir.replace("\\", os.sep)
        
        # File name
        fpt = 'pt_%s.csv' % pt
        # Absolute path to point sensors
        fname = os.path.join(fdir, fpt)
        # Save the file name
        self.fname = fname
        
        # Process columns
        self.ProcessColumns()
        
        # Read the file or initialize empty arrays.
        self.Read(fname)
        
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Initialize string
        lbl = "<DBPointSensor %s, " % self.pt
        # Number of cases in book
        lbl += "nCase=%i>" % self.n
        # Output
        return lbl
    __str__ = __repr__
  # >
  
  # =========
  # Updaters
  # =========
  # <
    # Process a case
    def UpdateCase(self, i):
        """Prepare to update one point sensor case if necessary
        
        :Call:
            >>> DBP.UpdateCase(i)
        :Inputs:
            *DBP*: :class:`cape.pointSensor.DBPointSensor`
                An individual point sensor data book
            *i*: :class:`int`
                Case index
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        pass
   # >       
# class DBPointSensor



# Data book of TriQ point sensors
class DBTriqPoint(DBPointSensor):
    """TriQ point sensor data book
    
    Plotting methods are inherited from :class:`cape.dataBook.DBBase`,
    including :func:`cape.dataBook.DBBase.PlotHist` for plotting historgrams of
    point sensor results in particular.
    
    :Call:
        >>> DBP = DBTriqPoint(x, opts, pt, name=None)
    :Inputs:
        *x*: :class:`cape.trajectory.Trajectory`
            Trajectory/run matrix interface
        *opts*: :class:`cape.options.Options`
            Options interface
        *pt*: :class:`str`
            Name of point
        *name*: :class:`str` | ``None``
            Name of data book item (defaults to *pt*)
        *RootDir*: :class:`str` | ``None``
            Project root directory absolute path, default is *PWD*
    :Outputs:
        *DBP*: :class:`pyCart.pointSensor.DBPointSensor`
            An individual point sensor data book
    :Versions:
        * 2015-12-04 ``@ddalle``: Started
    """
  # ========
  # Config
  # ========
  # <
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Initialize string
        lbl = "<DBTriqPoint %s, " % self.pt
        # Number of cases in book
        lbl += "nCase=%i>" % self.n
        # Output
        return lbl
    __str__ = __repr__
  # >
  
  # =========
  # Updaters
  # =========
  # <
    # Process a case
    def UpdateCase(self, i):
        """Prepare to update one point sensor case if necessary
        
        :Call:
            >>> DBP.UpdateCase(i)
        :Inputs:
            *DBP*: :class:`cape.pointSensor.DBTriqPoint`
                An individual point sensor data book
            *i*: :class:`int`
                Case index
        :Versions:
            * 2015-12-04 ``@ddalle``: First version
        """
        pass
   # >       
# class DBPointSensor


