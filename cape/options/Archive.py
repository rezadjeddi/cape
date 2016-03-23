"""
Interface to case archiving options
===================================

This module provides a class to access options relating to archiving folders
that were used to run CFD analysis
"""

# Ipmort options-specific utilities
from util import rc0, odict, getel

# Turn dictionary into Archive options
def auto_Archive(opts):
    """Automatically convert dict to :mod:`pyCart.options.Archive.Archive`
    
    :Call:
        >>> opts = auto_Archive(opts)
    :Inputs:
        *opts*: :class:`dict`
            Dict of either global, "RunControl" or "Archive" options
    :Outputs:
        *opts*: :class:`pyCart.options.Archive.Archive`
            Instance of archiving options
    :Versions:
        * 2016-02-29 ``@ddalle``: First version
    """
    # Get type
    t = type(opts).__name__
    # Check type
    if t == "Archive":
        # Good; quit
        return opts
    elif t == "RunControl":
        # Get the sub-object
        return opts["Archive"]
    elif t == "Options":
        # Get the sub-sub-object
        return opts["RunControl"]["Archive"]
    elif t in ["dict", "odict"]:
        # Downselect if given parent class
        opts = opts.get("RunControl", opts)
        opts = opts.get("Archive",    opts)
        # Convert to class
        return Archive(**opts)
    else:
        # Invalid type
        raise TypeError("Unformatted input must be type 'dict', not '%s'" % t)
# def auto_Archive


# Class for folder management and archiving
class Archive(odict):
    """Dictionary-based interfaced for options specific to folder management"""
    
   
    # -------------
    # Basic Options
    # -------------
   # <
    # Archive base folder
    def get_ArchiveFolder(self):
        """Return the path to the archive
        
        :Call:
            >>> fdir = opts.get_ArchiveFolder()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fdir*: :class:`str`
                Path to root directory of archive
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        return self.get_key('ArchiveFolder')
        
    # Set archive base folder
    def set_ArchiveFolder(self, fdir=rc0('ArchiveFolder')):
        """Set the path to the archive
        
        :Call:
            >>> opts.set_ArchiveFolder(fdir)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fdir*: :class:`str`
                Path to root directory of archive
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        self.set_key('ArchiveFolder', fdir)
        
    # Archive format
    def get_ArchiveFormat(self):
        """Return the format for folder archives
        
        :Call:
            >>> fmt = opts.get_ArchiveFormat()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fmt*: ``""`` | {``"tar"``} | ``"gzip"`` | ``"bz2"``
                Archive format
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        return self.get_key('ArchiveFormat')
        
    # Set archive format
    def set_ArchiveFormat(self, fmt=rc0('ArchiveFormat')):
        """Set the format for folder archives
        
        :Call:
            >>> opts.set_ArchiveFormat(fmt)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fmt*: ``""`` | {``"tar"``} | ``"gzip"`` | ``"bz2"``
                Archive format
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        self.set_key('ArchiveFormat', fmt)
        
    # Get archive type
    def get_ArchiveType(self):
        """Return the archive type; whether or not to save as a single tar ball
        
            * ``"full"``: Archives all contents of the case as one tar ball
            * ``"sub"``: Archive case as group of tar balls/files
        
        :Call:
            >>> atype = opts.get_ArchiveType()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fcmd*: {"full"} | "sub"
                Name of archive type
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key('ArchiveType')
        
    # Set archive type
    def set_ArchiveType(self, atype=rc0('ArchiveType')):
        """Set the archive type; determines what is deleted before archiving
        
        :Call:
            >>> opts.set_ArchiveType(atype)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *atype*: {"full"} | "sub"
                Name of archive type
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.set_key('ArchiveType', atype)
        
    # Get archive type
    def get_ArchiveTemplate(self):
        """Return the archive type; determines what is deleted before archiving
        
        Note that all types except ``"full"`` will delete files from the working
        folder before archiving.  However, archiving actions, including the
        preliminary deletions, only take place if the case is marked *PASS*.
        
            * ``"full"``: Archives all contents of run directory
            * ``"best"``: Deletes all previous adaptation folders
            * ``"viz"``: Deletes all :file:`Mesh*.c3d` files and check files
            * ``"hist"``: Deletes all mesh, tri, and TecPlot files
        
        :Call:
            >>> atype = opts.get_ArchiveType()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fcmd*: {"full"} | "viz" | "best" | "hist"
                Name of archive type
        :Versions:
            * 2015-02-16 ``@ddalle``: First version
        """
        return self.get_key('ArchiveTemplate')
        
    # Set archive type
    def set_ArchiveTemplate(self, atype=rc0('ArchiveTemplate')):
        """Set the archive type; determines what is deleted before archiving
        
        :Call:
            >>> opts.set_ArchiveTemplate(atype)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *atype*: {"full"} | "viz" | "best" | "hist"
                Name of archive template
        :Versions:
            * 2015-02-16 ``@ddalle``: First version
            * 2016-02-29 ``@ddalle``: Moved from previous *ArchiveType*
        """
        self.set_key('ArchiveTemplate', atype)
        
    # Get archiving action
    def get_ArchiveAction(self):
        """Return the action to take after finishing a case
        
        :Call:
            >>> fcmd = opts.get_ArchiveAction()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fcmd*: {""} | "skeleton" | "rm" | "archive"
                Type of archiving action to take
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        return self.get_key('ArchiveAction')
        
    # Set archiving action
    def set_ArchiveAction(self, fcmd=rc0('ArchiveAction')):
        """Set the action to take after finishing a case
        
        :Call:
            >>> opts.set_ArchiveAction(fcmd)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fcmd*: {""} | "skeleton" | "rm" | "archive"
                Type of archiving action to take
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        self.set_key('ArchiveAction', fcmd)
        
    # Get archiving command
    def get_RemoteCopy(self):
        """Return the command used for remote copying
        
        :Call:
            >>> fcmd = opts.get_RemoteCopy()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fcmd*: {"scp"} | "rsync" | "shiftc --wait"
                Command to use for archiving
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        return self.get_key('RemoteCopy')
        
    # Set archiving command
    def set_RemoteCopy(self, fcmd='scp'):
        """Set the command used for remote copying
        
        :Call:
            >>> opts.set_RemoteCopy(fcmd)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fcmd*: {"scp"} | "rsync" | "shiftc"
                Type of archiving action to take
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        self.set_key('RemoteCopy', fcmd)
        
    # Get the archive format for PBS output files
    def get_TarPBS(self):
        """Return the archive format for adapt folders
        
        :Call:
            >>> fmt = opts.get_TarPBS()
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
        :Outputs:
            *fmt*: ``""`` | {``"tar"``} | ``"gzip"`` | ``"bz2"``
                Archive format
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        return self.get_key('TarPBS')
        
    # Set the archive format for visualization files
    def set_TarPBS(self, fmt=rc0('TarPBS')):
        """Set the archive format for adapt folders
        
        :Call:
            >>> opts.set_TarPBS(fmt)
        :Inputs:
            *opts*: :class:`pyCart.options.Options`
                Options interface
            *fmt*: ``""`` | {``"tar"``} | ``"gzip"`` | ``"bz2"``
                Archive format
        :Versions:
            * 2015-01-10 ``@ddalle``: First version
        """
        self.set_key('TarPBS', fmt)
   # >
   
    # -----
    # Tools
    # -----
   # <
    # Add to general key
    def add_to_key(self, key, fpre):
        """Add to the folders of groups to tar before archiving
        
        :Call:
            >>> opts.add_to_key(key, fpre)
            >>> opts.add_to_key(key, lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *key*: :class:`str`
                Name of the key to update
            *fpre*: :class:`str`
                Folder or folder glob to add to list
            *lpre*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        # Check for null inputs
        if fpre is None: return
        # Get Current list
        fdel = self.get_key(key)
        # Types
        td = type(fdel).__name__
        tp = type(fpre).__name__
        # Check key type
        if td in ['odict', 'dict']:
            # Check input type
            if tp not in ['dict', 'odict']:
                raise TypeError(
                    ("Appending to key '%s', with value '%s'\n" % (key, fdel)) +
                    ("Cannot append type '%s' to dictionary options" % tp))
            # Append dictionary
            for fi in fpre:
                # Check if values is already there
                if fi not in fdel: fdel[fi] = fpre[fi]
        elif td in ['list', 'ndarray']:
            # Check input type
            if tp not in ['list', 'ndarray']:
                # Ensure list
                fpre = [fpre]
            # Append each file to the list
            for fi in fpre:
                # Check if the file is already there
                if fi not in fdel: fdel.append(fi)
        # Set the parameter
        self[key] = fdel
    
    # Archive extension
    def get_ArchiveExtension(self):
        """Get archive extension
        
        :Call:
            >>> ext = opts.get_ArchiveExtenstion()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *ext*: :class:`str` | {tar} | tgz | bz | bz2 | zip
                Archive extension
        :Versions:
            * 2016-03-01 ``@ddalle``: First version
        """
        # Get the format
        fmt = self.get_ArchiveFormat()
        # Process
        if fmt in ['gzip', 'tgz']:
            # GZip
            return 'tgz'
        elif fmt in ['zip']:
            # Zip
            return 'zip'
        elif fmt in ['bzip', 'bz', 'bzip2', 'bz2', 'tbz', 'tbz2']:
            # bzip2
            return 'tbz2'
        else:
            # Default: tar
            return 'tar'
            
    # Archive command
    def get_ArchiveCmd(self):
        """Get archiving command
        
        :Call:
            >>> cmd = opts.get_ArchiveCmd()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *cmd*: :class:`list` (:class:`str`)
                Tar command and appropriate flags
        :Versions:
            * 2016-03-01 ``@ddalle``: First version
        """
        # Get the format
        fmt = self.get_ArchiveFormat()
        # Process
        if fmt in ['gzip' ,'tgz']:
            # Gzip
            return ['tar', '-czf']
        elif fmt in ['zip']:
            # Zip
            return ['zip', '-r']
        elif fmt in ['bzip', 'bz', 'bzip2', 'bz2', 'tbz', 'tbz2']:
            # Bzip2
            return ['tar', '-cjf']
        else:
            # Default: tar
            return ['tar', '-uf']
            
    # Unarchive command
    def get_UnarchiveCmd(self):
        """Get command to unarchive
        
        :Call:
            >>> cmd = opts.get_UnarchiveCmd()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *cmd*: :class:`list` (:class:`str`)
                Untar command and appropriate flags
        :Versions:
            * 2016-03-01 ``@ddalle``: First version
        """
        # Get the format
        fmt = self.get_ArchiveFormat()
        # Process
        if fmt in ['gzip' ,'tgz']:
            # Gzip
            return ['tar', '-xzf']
        elif fmt in ['zip']:
            # Zip
            return ['unzip']
        elif fmt in ['bzip', 'bz', 'bzip2', 'bz2', 'tbz', 'tbz2']:
            # Bzip2
            return ['tar', '-xjf']
        else:
            # Default: tar
            return ['tar', '-xf']
   # >
    
    # ----------------------------
    # Progress Archive Definitions
    # ----------------------------
   # <
    # List of files to delete
    def get_ArchiveProgressDeleteFiles(self):
        """Get list of files to delete at end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressDeleteFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file globs to delete at the end of each run
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressDeleteFiles")
        
    # Add to list of files to delete
    def add_ArchiveProgressDeleteFiles(self, fpro):
        """Add to the list of files to delete at end of each run
        
        :Call:
            >>> opts.add_ArchiveProgressDeleteFiles(fpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str` | :class:`list` (:class:`str`)
                File glob or list of file globs to add
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressDeleteFiles", fpro)
        
    # List of folders to delete
    def get_ArchiveProgressDeleteDirs(self):
        """Get list of folders to delete at end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressDeleteDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folder names to delete at the end of each run
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressDeleteDirs")
        
    # Add to list of files to delete
    def add_ArchiveProgressDeleteDirs(self, fpro):
        """Add to the list of folders to delete at end of each run
        
        :Call:
            >>> opts.add_ArchiveProgressDeleteDirs(fpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str` | :class:`list` (:class:`str`)
                File glob or list of file globs to add
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressDeleteDirs", fpro)
        
    # List of files to update
    def get_ArchiveProgressUpdateFiles(self):
        """Get list of files to update at end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressUpdateFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folder names to delete at the end of each run
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressUpdateFiles")
        
    # Add to list of files to update
    def add_ArchiveProgressUpdateFiles(self, fpro):
        """Add to the list of files to update at end of each run
        
        :Call:
            >>> opts.add_ArchiveProgressUpdateFiles(fpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str` | :class:`list` (:class:`str`)
                File glob or list of file globs to add
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressUpdateFiles", fpro)
        
    # List of file groups to tar
    def get_ArchiveProgressTarGroups(self):
        """Get list of file groups to tar at the end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressTarGroups()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folder names to delete at the end of each run
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressTarGroups")
        
    # Add to list of file groups to tar
    def add_ArchiveProgressTarGroups(self, fpro):
        """Add to the list of file groups to tar at the end of each run
        
        :Call:
            >>> opts.add_ArchiveProgressTarGroups(fpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str` | :class:`list` (:class:`str`)
                File glob or list of file globs to add
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressTarGroups", fpro)
        
    # List of folders to tar
    def get_ArchiveProgressTarDirs(self):
        """Get list of folders to tar at the end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressTarDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folder names to delete at the end of each run
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressTarDirs")
        
    # Add to list of folders to tar
    def add_ArchiveProgressTarDirs(self, fpro):
        """Add to the list of folders to tar at the end of each run
        
        :Call:
            >>> opts.add_ArchiveProgressTarDirs(fpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str` | :class:`list` (:class:`str`)
                File glob or list of file globs to add
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressTarDirs", fpro)
   # >
   
    # ------------------------
    # Pre-Archiving Processing
    # ------------------------
   # <
    # List of files to delete
    def get_ArchivePreDeleteFiles(self):
        """Get list of files to delete **before** archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePreDeleteFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key("PreDeleteFiles")
        
    # Add to list of files to delete
    def add_ArchivePreDeleteFiles(self, fpre):
        """Add to the list of files to delete before archiving
        
        :Call:
            >>> opts.add_ArchivePreDeleteFiles(fpre)
            >>> opts.add_ArchivePreDeleteFiles(lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpre*: :class:`str`
                File or file glob to add to list
            *lpre*: :class:`list` (:class:`str`)
                List of files or file globs to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PreDeleteFiles", fpre)
            
    # List of folders to delete
    def get_ArchivePreDeleteDirs(self):
        """Get list of folders to delete **before** archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePreDeleteDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key("PreDeleteDirs")
        
    # Add to list of folders to delete
    def add_ArchivePreDeleteDirs(self, fpre):
        """Add to the list of folders to delete before archiving
        
        :Call:
            >>> opts.add_ArchivePreDeleteDirs(fpre)
            >>> opts.add_ArchivePreDeleteDirs(lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpre*: :class:`str`
                Folder or file glob to add to list
            *lpre*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PreDeleteDirs", fpre)
    
    # List of files to tar before archiving
    def get_ArchivePreTarGroups(self):
        """Get list of files to tar prior to archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePreTarGroups()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-029 ``@ddalle``: First version
        """
        return self.get_key("PreTarGroups")
        
    # Add to list of folders to delete
    def add_ArchivePreTarGroups(self, fpre):
        """Add to the list of groups to tar before archiving
        
        :Call:
            >>> opts.add_ArchivePreTarGroups(fpre)
            >>> opts.add_ArchivePreTarGroups(lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpre*: :class:`str`
                File glob to add to list
            *lpre*: :class:`str`
                List of globs of files to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PreTarGroups", fpre)
    
    # List of folders to tar before archiving
    def get_ArchivePreTarDirs(self):
        """Get list of folders to tar prior to archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePreTarDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-029 ``@ddalle``: First version
        """
        return self.get_key("PreTarDirs")
        
    # Add to list of folders to delete
    def add_ArchivePreTarDirs(self, fpre):
        """Add to the folders of groups to tar before archiving
        
        :Call:
            >>> opts.add_ArchivePreTarDirs(fpre)
            >>> opts.add_ArchivePreTarDirs(lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpre*: :class:`str`
                Folder or folder glob to add to list
            *lpre*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PreTarDirs", fpre)
        
    # List of files to update before archiving
    def get_ArchivePreUpdateFiles(self):
        """Get :class:`dict` of files of which to keep only *n*
        
        :Call:
            >>> fglob = opts.get_ArchivePreUpdateFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-029 ``@ddalle``: First version
        """
        return self.get_key("PreUpdateFiles")
        
    # Add to list of files to update before archiving
    def add_ArchivePreUpdateFiles(self, fpre):
        """Add to :class:`dict` of files of which to keep only *n*
        
        :Call:
            >>> opts.add_ArchivePreUpdateFiles(fpre)
            >>> opts.add_ArchivePreUpdateFiles(lpre)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpre*: :class:`str`
                Folder or folder glob to add to list
            *lpre*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PreUpdateFiles", fpre)
   # >
    
    # -------------------------
    # Post-Archiving Processing
    # -------------------------
   # <
    # List of files to delete
    def get_ArchivePostDeleteFiles(self):
        """Get list of files to delete after archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePreDeleteFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete after archiving
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key("PostDeleteFiles")
        
    # Add to list of files to delete
    def add_ArchivePostDeleteFiles(self, fpost):
        """Add to the list of files to delete after archiving
        
        :Call:
            >>> opts.add_ArchivePostDeleteFiles(fpost)
            >>> opts.add_ArchivePostDeleteFiles(lpost)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpost*: :class:`str`
                File or file glob to add to list
            *lpost*: :class:`list` (:class:`str`)
                List of files or file globs to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PostDeleteFiles", fpost)
            
    # List of folders to delete
    def get_ArchivePostDeleteDirs(self):
        """Get list of folders to delete after archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePostDeleteDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folders to delete after archiving
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key("PostDeleteDirs")
        
    # Add to list of folders to delete
    def add_ArchivePostDeleteDirs(self, fpost):
        """Add to the list of folders to delete after archiving
        
        :Call:
            >>> opts.add_ArchivePostDeleteDirs(fpost)
            >>> opts.add_ArchivePostDeleteDirs(lpost)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpost*: :class:`str`
                Folder or file glob to add to list
            *lpost*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PostDeleteDirs", fpost)
            
    # List of files to tar after archiving
    def get_ArchivePostTarGroups(self):
        """Get list of files to tar prior to archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePostTarGroups()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-029 ``@ddalle``: First version
        """
        return self.get_key("PostTarGroups")
        
    # Add to list of folders to delete
    def add_ArchivePostTarGroups(self, fpost):
        """Add to the list of groups to tar before archiving
        
        :Call:
            >>> opts.add_ArchivePostTarGroups(fpost)
            >>> opts.add_ArchivePostTarGroups(lpost)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpost*: :class:`str`
                File glob to add to list
            *lpost*: :class:`str`
                List of globs of files to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PostTarGroups", fpost)
    
    # List of folders to tar before archiving
    def get_ArchivePostTarDirs(self):
        """Get list of folders to tar after archiving
        
        :Call:
            >>> fglob = opts.get_ArchivePostTarDirs()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of globs of folders to delete fter archiving
        :Versions:
            * 2016-02-029 ``@ddalle``: First version
        """
        return self.get_key("PostTarDirs")
        
    # Add to list of folders to delete
    def add_ArchivePostTarDirs(self, fpost):
        """Add to the folders of groups to tar after archiving
        
        :Call:
            >>> opts.add_ArchivePostTarDirs(fpost)
            >>> opts.add_ArchivePostTarDirs(lpost)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpost*: :class:`str`
                Folder or folder glob to add to list
            *lpost*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PostTarDirs", fpost)
        
    # List of files to update before archiving
    def get_ArchivePostUpdateFiles(self):
        """Get :class:`dict` of files of which to keep only *n*
        
        :Call:
            >>> fglob = opts.get_ArchivePostUpdateFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        return self.get_key("PostUpdateFiles")
        
    # Add to list of files to update before archiving
    def add_ArchivePostUpdateFiles(self, fpost):
        """Add to :class:`dict` of files of which to keep only *n*
        
        :Call:
            >>> opts.add_ArchivePostUpdateFiles(fpost)
            >>> opts.add_ArchivePostUpdateFiles(lpost)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpost*: :class:`str`
                Folder or folder glob to add to list
            *lpost*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-02-29 ``@ddalle``: First version
        """
        self.add_to_key("PostUpdateFiles", fpost)
        
    # List of files to archive at end of each run
    def get_ArchiveProgressArchiveFiles(self):
        """Get :class:`dict` of files to archive at end of each run
        
        :Call:
            >>> fglob = opts.get_ArchiveProgressArchiveFiles()
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
        :Outputs:
            *fglob*: :class:`list` (:class:`str`)
                List of file wild cards to delete before archiving
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        return self.get_key("ProgressArchiveFiles")
        
    # Add to list of files to archive at end of each run
    def add_ArchiveProgressArchiveFiles(self, fpro):
        """Add to :class:`dict` of files of which to keep only *n*
        
        :Call:
            >>> opts.add_ArchiveProgressArchiveFiles(fpro)
            >>> opts.add_ArchiveProgressArchiveFiles(lpro)
        :Inputs:
            *opts*: :class:`cape.options.Options`
                Options interface
            *fpro*: :class:`str`
                Folder or folder glob to add to list
            *lpo*: :class:`str`
                List of folders or globs of folders to add to list
        :Versions:
            * 2016-03-14 ``@ddalle``: First version
        """
        self.add_to_key("ProgressArchiveFiles", fpro)
   # >
            
# class Archive

