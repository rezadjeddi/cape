#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------
:mod:`cape.tnakit.plot_mpl`: Matplotlib/Pyplot Interfaces
--------------------------------------------------------------------

This module contains handles to various :mod:`matplotlib` plotting
methods.  In particular, it centralizes some of the multiple-line
instructions that are used in multiple places.  An example is placing
labels on one or more corners of the axis window.

It also includes syntax to import modules without raising ``ImportError``.
"""

# Standard library modules
import os

# Required third-party modules
import numpy as np

# TNA toolkit modules
import cape.tnakit.kwutils as kwutils
import cape.tnakit.optitem as optitem
import cape.tnakit.rstutils as rstutils
import cape.tnakit.statutils as statutils
import cape.tnakit.typeutils as typeutils

# Get a variable to hold the "type" of "module"
mod = os.__class__

# Initialize handle for modules
plt = object()
mpl = object()
mplax = object()
mplfig = object()


# Import :mod:`matplotlib`
def import_matplotlib():
    """Function to import Matplotlib if possible

    This function checks if the global variable *mpl* is already a
    module.  If so, the function exits without doing anything.
    Otherwise it imports :mod:`matplotlib` as *mpl*.  If the operating
    system is not Windows, and there is no environment variable
    *DISPLAY*, the backend is set to ``"Agg"``.

    :Call:
        >>> import_matplotlib()
    :Versions:
        * 2019-08-22 ``@ddalle``: Documented first version
    """
    # Make global variables
    global mpl
    global mplax
    global mplfig
    # Exit if already imported
    if isinstance(mpl, mod):
        return
    # Import module
    try:
        import matplotlib as mpl
        import matplotlib.axes as mplax
        import matplotlib.figure as mplfig
    except ImportError:
        return
    # Check for no-display
    if (os.name != "nt") and (os.environ.get("DISPLAY") is None):
        # Not on Windows and no display: no window to create fig
        mpl.use("Agg")


# Import :mod:`matplotlib`
def import_pyplot():
    """Function to import Matplotlib's PyPlot if possible

    This function checks if the global variable *plt* is already a
    module.  If so, the function exits without doing anything.
    Otherwise it imports :mod:`matplotlib.pyplot` as *plt* after
    calling :func:`import_matplotlib`.

    :Call:
        >>> import_pyplot()
    :See also:
        * :func:`import_matplotlib`
    :Versions:
        * 2019-08-22 ``@ddalle``: Documented first version
    """
    # Make global variables
    global plt
    # Exit if already imported
    if isinstance(plt, mod):
        return
    # Otherwise, import matplotlib first
    import_matplotlib()
    # Import module
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return


# Primary plotter
def plot(xv, yv, *a, **kw):
    """Plot connected points with many options

    :Call:
        >>> h, kw = plot(xv, yv, *a, **kw)
    :Inputs:
        *xv*: :class:`np.ndarray` (:class:`float`)
            Array of values for *x*-axis
        *yv*: :class:`np.ndarray` (:class:`float`)
            Array of values for *y*-axis
    :Outputs:
        *h*: :class:`cape.tnakit.plto_mpl.MPLHandle`
            Dictionary of plot handles
    :Versions:
        * 2019-03-01 ``@ddalle``: First (independent) version
        * 2019-12-23 ``@ddalle``: Object-oriented options and output
    """
   # --- Prep ---
    # Ensure plot() is loaded
    import_pyplot()
    # Process options
    opts = MPLOpts(**kw)
    # Initialize output
    h = MPLHandle()
    # Number of args and args used
    na = len(a)
    ia = 0
   # --- Default Control ---
    # Min/Max
    if ("ymin" in opts) and ("ymax" in opts):
        # If min/max values are specified, turn on *PlotMinMax*
        qmmx = True
    else:
        # Otherwise false
        qmmx = False
    # UQ
    if ("yerr" in opts) or ("xerr" in opts):
        # If min/max values are specified, turn on *PlotUncertainty*
        quq = True
    else:
        # Otherwise false
        quq = False
   # --- Control Options ---
    # Options to plot min/max
    qline = opts.get("ShowLine", True)
    qmmx = opts.get("ShowMinMax", qmmx)
    qerr = opts.get("ShowError", False)
    quq = opts.get("ShowUncertainty", quq and (not qerr))
   # --- Universal Options ---
    # Font options
    kw_font = opts.font_options()
   # --- Figure Setup ---
    # Process figure options
    kw_fig = opts.figure_options()
    # Get/create figure
    h.fig = figure(**kw_fig)
   # --- Axis Setup ---
    # Process axis options
    kw_ax = opts.axes_options()
    # Get/create axis
    h.ax = axes(**kw_ax)
   # --- Primary Plot ---
    # Process plot options
    kw_plot = opts.plot_options()
    # Call plot method
    if qline:
        # Check *a[0]*
        if (na > 0) and typeutils.isstr(a[0]):
            # Format given
            fmt = (a[0],)
            # One arg used
            ia += 1
        else:
            # No format option
            fmt = tuple()
        # Plot call
        h.lines += _plot(xv, yv, *fmt, **kw_plot)
   # --- Min/Max ---
    # Process min/max options
    opts_mmax = opts.minmax_options()
    # Get type
    minmax_type = opts_mmax.get("MinMaxPlotType", "ErrorBar")
    # Options for the plot function
    kw_mmax = opts_mmax.get("MinMaxOptions", {})
    # Plot it
    if qmmx:
        # Min/max values
        if na >= ia + 2:
            # Get parameter values
            ymin = a[ia]
            ymax = a[ia+1]
            # Increase count
            ia += 2
        else:
            # Pop values
            ymin = opts.get("ymin", None)
            ymax = opts.get("ymax", None)
        # Plot call
        if minmax_type == "FillBetween":
            # Do a :func:`fill_between` plot
            h.minmax = fill_between(xv, ymin, ymax, **kw_mmax)
        elif minmax_type == "ErrorBar":
            # Convert to error bar widths
            yerr = minmax_to_errorbar(yv, ymin, ymax, **kw_mmax)
            # Do a :func:`errorbar` plot
            h.minmax = errorbar(xv, yv, yerr, **kw_mmax)
   # --- Error ---
    # Process "error" options
    opts_error = opts.error_options()
    # Get type
    error_type = opts_error.get("ErrorPlotType", "FillBetween")
    # Get options for plot function
    kw_err = opts_error.get("ErrorOptions", {})
    # Plot it
    if qerr:
        # Min/max values
        if na >= ia+1:
            # Get parameter values
            yerr = a[ia]
            # Increase count
            ia += 1
        else:
            # Pop values
            yerr = kw.get("yerr", None)
        # Check for horizontal error bars
        xerr = kw.get("xerr", None)
        # Plot call
        if error_type == "FillBetween":
            # Convert to min/max values
            ymin, ymax = errorbar_to_minmax(yv, yerr)
            # Do a :func:`fill_between` plot
            h.error = fill_between(xv, ymin, ymax, **kw_err)
        elif t_err == "ErrorBar":
            # Do a :func:`errorbar` plot
            h.error = errorbar(xv, yv, yerr, **kw_err)
   # --- UQ ---
    # Process uncertainty quantification options
    opts_uq = opts.uq_options()
    # Plot type
    uq_type = opts.get("UncertaintyPlotType", "FillBetween")
    # Get options for plot function
    kw_uq = opts_uq.get("UncertaintyOptions", {})
    # Plot it
    if quq:
        # Min/max values
        if na >= ia+1:
            # Get parameter values
            yerr = a[ia]
            # Increase count
            ia += 1
        else:
            # Pop values
            yerr = kw.get("uy", kw.get("yerr", None))
        # Check for horizontal error bars
        xerr = kw.get("ux", kw.get("ux", None))
        # Plot call
        if uq_type == "FillBetween":
            # Convert to min/max values
            ymin, ymax = errorbar_to_minmax(yv, yerr)
            # Do a :func:`fill_between` plot
            h.uq = fill_between(xv, ymin, ymax, **kw_uq)
        elif uq_type == "ErrorBar":
            # Do a :func:`errorbar` plot
            h.uq = errobar(xv, yv, yerr, **kw_uq)
   # --- Axis formatting ---
    ## Process grid lines options
    kw_grid = opts.grid_options()
    # Apply grid lines
    grid(h.ax, **kw_grid)
    # Process spine options
    kw_spines = opts.spine_options()
    # Apply options relating to spines
    h.spines = format_spines(h.ax, **kw_spines)
    # Process axes format options
    kw_axfmt = opts.axformat_options()
    # Apply formatting
    h.xlabel, h.ylabel = axes_format(h.ax, **kw_axfmt)
   # --- Margin adjustment ---
    # Process axes margin/adjust options
    kw_axadj = opts.axadjust_options()
    # Adjust extents
    axes_adjust(h.fig, ax=h.ax, **kw_axadj)
   # --- Legend ---
    ## Process options for legend
    kw_legend = opts.legend_options()
    # Create legend
    h.legend = legend(h.ax, **kw_legend)
   # --- Cleanup ---
    # Save options
    h.opts = opts
    # Output
    return h


# Manage single subplot extents
def axes_adjust(fig=None, **kw):
    r"""Manage margins of one axes handle

    This function provides two methods for adjusting the margins of an
    axes handle.  The first is to automatically detect all the space
    taken up outside of the plot region by both tick labels and axes
    labels and then expand the plot to fill the figure up to amounts
    specified by the *Margin* parameters.  The second is to directly
    specify the figure coordinates of the figure edges using the
    *Adjust* parameters, which override any *Margin* specifications. It
    is possible, however, to use *Adjust* for the top and *Margin* for
    the bottom, for example.

    :Call:
        >>> ax = axes_adjust(fig=None, **kw)
    :Inputs:
        *fig*: {``None``} | :class:`Figure` | :class:`int`
            Figure handle or number (default from :func:`plt.gcf`)
        *ax*: {``None``} | :class:`AxesSubplot`
            Axes handle, if specified, *Subplot* is ignored
        *Subplot*: {``None``} | :class:`int` > 0
            Subplot index; if ``None``, use :func:`plt.gca`; adds a
            new subplot if *Subplot* is greater than the number of
            existing subplots in *fig* (1-based index)
        *SubplotRows*: {*Subplot*} | :class:`int` > 0
            Number of subplot rows if creating new subplot
        *SubplotCols*: {*Subplot*} | :class:`int` > 0
            Number of subplot columns if creating new subplot
        *MarginBottom*: {``0.02``} | :class:`float`
            Figure fraction from bottom edge to bottom label
        *MarginLeft*: {``0.02``} | :class:`float`
            Figure fraction from left edge to left-most label
        *MarginRight*: {``0.015``} | :class:`float`
            Figure fraction from right edge to right-most label
        *MarginTop*: {``0.015``} | :class:`float`
            Figure fraction from top edge to top-most label
        *AdjustBottom*: ``None`` | :class:`float`
            Figure coordinate for bottom edge of axes
        *AdjustLeft*: ``None`` | :class:`float`
            Figure coordinate for left edge of axes
        *AdjustRight*: ``None`` | :class:`float`
            Figure coordinate for right edge of axes
        *AdjustTop*: ``None`` | :class:`float`
            Figure coordinate for top edge of axes
        *KeepAspect*: {``None``} | ``True`` | ``False``
            Keep aspect ratio; default is ``True`` unless
            ``ax.get_aspect()`` is ``"auto"``
    :Outputs:
        *ax*: :class:`AxesSubplot`
            Handle to subplot directed to use from these options
    :Versions:
        * 2020-01-03 ``@ddalle``: First version
        * 2010-01-10 ``@ddalle``: Add support for ``"equal"`` aspect
    """
    # Make sure pyplot is present
    import_pyplot()
    # Default figure
    if fig is None:
        # Get most recent figure or create
        fig = plt.gcf()
    elif isinstance(fig, int):
        # Get figure handle from number
        fig = plt.figure(fig)
    elif not isinstance(fig, mplfig.Figure):
        # Not a figure or number
        raise TypeError(
            "'fig' arg expected 'int' or 'Figure' (got %s)" % type(fig))
    # Process options
    opts = MPLOpts(**kw)
    # Get axes from figure
    ax_list = fig.get_axes()
    # Minimum number of axes
    nmin_ax = min(1, len(ax_list))
    # Get "axes" option
    ax = opts.get("ax")
    # Get subplot number options
    subplot_i = opts.get("Subplot")
    subplot_m = opts.get("SubplotRows", nmin_ax)
    subplot_n = opts.get("SubplotCols", nmin_ax // subplot_m)
    # Check for axes
    if ax is None:
        # Check for index
        if subplot_i is None:
            # Get most recent axes
            ax = plt.gca()
            # Reset axes list
            ax_list = fig.get_axes()
            # Get index
            subplot_i = ax_list.index(ax) + 1
        elif not isinstance(subplot_i, int):
            # Must be an integer
            raise TypeError(
                "'Subplot' keyword must be 'int' (got %s)" % type(subplot_i))
        elif subplot_i <= 0:
            # Must be *positive*
            raise ValueError(
                "'Subplot' index must be positive (1-based) (got %i)" %
                subplot_i)
        elif subplot_i > len(ax_list):
            # Create new subplot
            ax = fig.add_subplot(subplot_m, subplot_n, subplot_i)
        else:
            # Get existing subplot (1-based indexing for consistency)
            ax = ax_list[subplot_i - 1]
    elif ax not in ax_list:
        # Axes from different figure!
        raise ValueError("Axes handle 'ax' is not in current figure")
    else:
        # Get subplot index (1-based index)
        subplot_i = ax_list.index(ax) + 1
    # Figure out subplot column and row index from counts (0-based)
    subplot_j = (subplot_i - 1) // subplot_n
    subplot_k = (subplot_i - 1) % subplot_n
    # Get sizes of all tick and axes labels
    labelw_l, labelh_b, labelw_r, labelh_t = get_axes_label_margins(ax)
    # Process width and height
    ax_w = 1.0 - labelw_r - labelw_l
    ax_h = 1.0 - labelh_t - labelh_b
    # Process row and column space available
    ax_rowh = ax_h / float(subplot_m)
    ax_colw = ax_w / float(subplot_n)
    # Default margins (no tight_layout yet)
    adj_b = labelh_b + subplot_j * ax_rowh
    adj_l = labelw_l + subplot_k * ax_colw
    adj_r = adj_l + ax_colw
    adj_t = adj_b + ax_rowh
    # Get extra margins
    margin_b = opts.get("MarginBottom", 0.02)
    margin_l = opts.get("MarginLeft", 0.02)
    margin_r = opts.get("MarginRight", 0.015)
    margin_t = opts.get("MarginTop", 0.015)
    # Apply to minimum margins
    adj_b += margin_b
    adj_l += margin_l
    adj_r -= margin_r
    adj_t -= margin_t
    # Get user options
    adj_b = opts.get("AdjustBottom", adj_b)
    adj_l = opts.get("AdjustLeft", adj_l)
    adj_r = opts.get("AdjustRight", adj_r)
    adj_t = opts.get("AdjustTop", adj_t)
    # Get current position of axes
    x0, y0, w0, h0 = ax.get_position().bounds
    # Keep same bottom edge if not specified
    if adj_b is None:
        adj_b = y0
    # Keep same left edge if not specified
    if adj_l is None:
        adj_l = x0
    # Keep same right edge if not specified
    if adj_r is None:
        adj_r = x0 + w0
    # Keep same top edge if not specified
    if adj_t is None:
        adj_t = y0 + h0
    # Aspect ratio option
    keep_ar = opts.get("KeepAspect")
    # Default aspect ratio option
    if keep_ar is None:
        # True unless current aspect is "equal" (which is usual case)
        keep_ar = ax.get_aspect() != "auto"
    # Turn off axis("equal") option if necessary
    if (not keep_ar) and (ax.get_aspect() != "auto"):
        # Can only adjust aspect ratio if this is off
        ax.set_aspect("auto")
    # Process aspect ratio
    if keep_ar:
        # Get the width and height of adjusted figure w/ cur margins
        w1 = adj_r - adj_l
        h1 = adj_t - adj_b
        # Currently expected expansion ratios
        rw = w1 / w0
        rh = h1 / h0
        # We can only use the smaller expansion
        if rw > rh:
            # Get current horizontal center
            xc = 0.5 * (adj_l + adj_r)
            # Reduce the horizontal expansion
            w1 = w0 * rh
            # New edge locations
            adj_l = xc - 0.5*w1
            adj_r = xc + 0.5*w1
        elif rh > rw:
            # Get current vertical center
            yc = 0.5 * (adj_b + adj_t)
            # Reduce vertical expansion
            h1 = h0 * rw
            # New edge locations
            adj_b = yc - 0.5*h1
            adj_t = yc + 0.5*h1
    # Set new position
    ax.set_position([adj_l, adj_b, adj_r-adj_l, adj_t-adj_b])
    # Output
    return ax


# Co-align a column of axes
def axes_adjust_col(fig, **kw):
    r"""Adjust a column of axes with shared horizontal extents

    :Call:
        >>> axes_adjust_col(fig, **kw)
    :Inputs:
        *fig*: {``None``} | :class:`Figure` | :class:`int`
            Figure handle or number (default from :func:`plt.gcf`)
        *SubplotList*: {``None``} | :class:`list`\ [:class:`int`]
            List of subplots nums in column (default is all)
        *SubplotRubber*: {``-1``} | :class:`int`
            Index of subplot to adjust to expand vertical
        *MarginBottom*: {``0.02``} | :class:`float`
            Figure fraction from bottom edge to bottom label
        *MarginLeft*: {``0.02``} | :class:`float`
            Figure fraction from left edge to left-most label
        *MarginRight*: {``0.015``} | :class:`float`
            Figure fraction from right edge to right-most label
        *MarginTop*: {``0.015``} | :class:`float`
            Figure fraction from top edge to top-most label
        *MarginVSpace*, *vspace*: {``0.02``} | :class:`float`
            Figure fraction for vertical space between axes
        *AdjustBottom*: ``None`` | :class:`float`
            Figure coordinate for bottom edge of axes
        *AdjustLeft*: ``None`` | :class:`float`
            Figure coordinate for left edge of axes
        *AdjustRight*: ``None`` | :class:`float`
            Figure coordinate for right edge of axes
        *AdjustTop*: ``None`` | :class:`float`
            Figure coordinate for top edge of axes
        *KeepAspect*: {``None``} | ``True`` | ``False``
            Keep aspect ratio; default is ``True`` unless
            ``ax.get_aspect()`` is ``"auto"``
    :Versions:
        * 2020-01-10 ``@ddalle``: First version
    """
    # Make sure pyplot is present
    import_pyplot()
    # Default figure
    if fig is None:
        # Get most recent figure or create
        fig = plt.gcf()
    elif isinstance(fig, int):
        # Get figure handle from number
        fig = plt.figure(fig)
    elif not isinstance(fig, mplfig.Figure):
        # Not a figure or number
        raise TypeError(
            "'fig' arg expected 'int' or 'Figure' (got %s)" % type(fig))
    # Process options
    opts = MPLOpts(**kw)
    # Get axes from figure
    ax_list = fig.get_axes()
    # Number of axes
    nax = len(ax_list)
    # Get list of figures
    subplot_list = kw.get("SubplotList", range(1, nax+1))
    # Get index of ax to use for vertical rubber
    subplot_rubber = kw.get("SubplotRubber", -1)
    # Adjust for 1-based index
    if subplot_rubber > 0:
        subplot_rubber -= 1
    # Get handle
    ax_rubber = ax_list[subplot_rubber]
    # Number of axes in col
    nrows = len(subplot_list)
    # Get the margins occupied by tick and axes labels
    margins = [get_axes_label_margins(ax_list[i-1]) for i in subplot_list]
    # Extract the sides
    margins_l = [margin[0] for margin in margins]
    margins_b = [margin[1] for margin in margins]
    margins_r = [margin[2] for margin in margins]
    margins_t = [margin[3] for margin in margins]
    # Use the maximum margin for left and right
    wa = max(margins_l)
    wb = max(margins_r)
    # Get extra margins
    margin_b = opts.get("MarginBottom", 0.02)
    margin_l = opts.get("MarginLeft", 0.02)
    margin_r = opts.get("MarginRight", 0.015)
    margin_t = opts.get("MarginTop", 0.015)
    margin_v = opts.get("MarginVSpace", 0.02)
    # Default extents
    adj_b = margin_b + margins_b[0]
    adj_l = margin_l + wa
    adj_r = 1.0 - margin_r - wb
    adj_t = 1.0 - margin_t - margins_t[-1]
    # Get user options
    adj_b = opts.get("AdjustBottom", adj_b)
    adj_l = opts.get("AdjustLeft", adj_l)
    adj_r = opts.get("AdjustRight", adj_r)
    adj_t = opts.get("AdjustTop", adj_t)
    # Shared axes width
    w_all = adj_r - adj_l
    # Get current extents
    extents = [ax_list[i-1].get_position().bounds for i in subplot_list]
    # Deal with any axis("equal") subplots
    for (j, i) in enumerate(subplot_list):
        # Get axes
        ax = ax_list[i-1]
        # Check for aspect ratio
        if ax.get_aspect() == "auto":
            # No adjustments necessary
            continue
        # Otherwise, get current position spec
        xminj, yminj, wj, hj = extents[j]
        # Expand (or shrink) current height
        hj = hj * (w_all / wj)
        # Recreate extents (can't change existing tuple)
        extents[j] = (xminj, yminj, wj, hj)
    # Measure all the current figure heights
    h_list = [pos[3] for pos in extents]
    # Total vertical space occupied by fixed plots
    h_fixed = sum(h_list) - h_list[subplot_rubber]
    # Add in required vertical text space
    if nrows > 1:
        h_fixed += sum(margins_b[1:]) + sum(margins_t[:-1])
    # Add in vertical margins between subplots
    h_fixed += margin_v * (nrows-1)
    # Calculate vertical extent for the rubber plot
    h_rubber = adj_t - adj_b - h_fixed
    # Initialize cumulative vertical coordinate
    ymin = adj_b - margins_b[0]
    # Loop through axes
    for (j, i) in enumerate(subplot_list):
        # Get axes
        ax = ax_list[i-1]
        # Check if it's the rubber plot
        if ax is ax_rubber:
            # Use the previously calculated height
            hj = h_rubber
        else:
            # Use the current extent
            hj = extents[j][3]
        # Add bottom text margin
        ymin += margins_b[j]
        # Set position
        ax.set_position([adj_l, ymin, w_all, hj])
        # Add top text margin and vspace
        ymin += margins_t[j] + margin_v
        # Add plot extent
        ymin += hj


# Co-align a row of axes
def axes_adjust_row(fig, **kw):
    r"""Adjust a row of axes with shared vertical extents

    :Call:
        >>> axes_adjust_row(fig, **kw)
    :Inputs:
        *fig*: {``None``} | :class:`Figure` | :class:`int`
            Figure handle or number (default from :func:`plt.gcf`)
        *SubplotList*: {``None``} | :class:`list`\ [:class:`int`]
            List of subplots nums in column (default is all)
        *SubplotRubber*: {``-1``} | :class:`int`
            Index of subplot to adjust to expand horizontally
        *MarginBottom*: {``0.02``} | :class:`float`
            Figure fraction from bottom edge to bottom label
        *MarginLeft*: {``0.02``} | :class:`float`
            Figure fraction from left edge to left-most label
        *MarginRight*: {``0.015``} | :class:`float`
            Figure fraction from right edge to right-most label
        *MarginTop*: {``0.015``} | :class:`float`
            Figure fraction from top edge to top-most label
        *MarginHSpace*, *vspace*: {``0.02``} | :class:`float`
            Figure fraction for horizontal space between axes
        *AdjustBottom*: ``None`` | :class:`float`
            Figure coordinate for bottom edge of axes
        *AdjustLeft*: ``None`` | :class:`float`
            Figure coordinate for left edge of axes
        *AdjustRight*: ``None`` | :class:`float`
            Figure coordinate for right edge of axes
        *AdjustTop*: ``None`` | :class:`float`
            Figure coordinate for top edge of axes
        *KeepAspect*: {``None``} | ``True`` | ``False``
            Keep aspect ratio; default is ``True`` unless
            ``ax.get_aspect()`` is ``"auto"``
    :Versions:
        * 2020-01-10 ``@ddalle``: First version
    """
    # Make sure pyplot is present
    import_pyplot()
    # Default figure
    if fig is None:
        # Get most recent figure or create
        fig = plt.gcf()
    elif isinstance(fig, int):
        # Get figure handle from number
        fig = plt.figure(fig)
    elif not isinstance(fig, mplfig.Figure):
        # Not a figure or number
        raise TypeError(
            "'fig' arg expected 'int' or 'Figure' (got %s)" % type(fig))
    # Process options
    opts = MPLOpts(**kw)
    # Get axes from figure
    ax_list = fig.get_axes()
    # Number of axes
    nax = len(ax_list)
    # Get list of figures
    subplot_list = kw.get("SubplotList", range(1, nax+1))
    # Get index of ax to use for vertical rubber
    subplot_rubber = kw.get("SubplotRubber", -1)
    # Adjust for 1-based index
    if subplot_rubber > 0:
        subplot_rubber -= 1
    # Get handle
    ax_rubber = ax_list[subplot_rubber]
    # Number of axes in row
    ncols = len(subplot_list)
    # Get the margins occupied by tick and axes labels
    margins = [get_axes_label_margins(ax_list[i-1]) for i in subplot_list]
    # Extract the sides
    margins_l = [margin[0] for margin in margins]
    margins_b = [margin[1] for margin in margins]
    margins_r = [margin[2] for margin in margins]
    margins_t = [margin[3] for margin in margins]
    # Use the maximum margin for left and right
    ha = max(margins_b)
    hb = max(margins_t)
    # Get extra margins
    margin_b = opts.get("MarginBottom", 0.02)
    margin_l = opts.get("MarginLeft", 0.02)
    margin_r = opts.get("MarginRight", 0.015)
    margin_t = opts.get("MarginTop", 0.015)
    margin_h = opts.get("MarginHSpace", 0.02)
    # Default extents
    adj_b = margin_b + ha
    adj_l = margin_l + margins_l[0]
    adj_r = 1.0 - margin_r - margins_r[-1]
    adj_t = 1.0 - margin_t - hb
    # Get user options
    adj_b = opts.get("AdjustBottom", adj_b)
    adj_l = opts.get("AdjustLeft", adj_l)
    adj_r = opts.get("AdjustRight", adj_r)
    adj_t = opts.get("AdjustTop", adj_t)
    # Shared axes height
    h_all = adj_r - adj_l
    # Get current extents
    extents = [ax_list[i-1].get_position().bounds for i in subplot_list]
    # Deal with any axis("equal") subplots
    for (j, i) in enumerate(subplot_list):
        # Get axes
        ax = ax_list[i-1]
        # Check for aspect ratio
        if ax.get_aspect() == "auto":
            # No adjustments necessary
            continue
        # Otherwise, get current position spec
        xminj, yminj, wj, hj = extents[j]
        # Expand (or shrink) current height
        wj = wj * (h_all / hj)
        # Recreate extents (can't change existing tuple)
        extents[j] = (xminj, yminj, wj, hj)
    # Measure all the current figure widths
    w_list = [pos[2] for pos in extents]
    # Total vertical space occupied by fixed plots
    w_fixed = sum(w_list) - w_list[subplot_rubber]
    # Add in required vertical text space
    if ncols > 1:
        w_fixed += sum(margins_l[1:]) + sum(margins_r[:-1])
    # Add in vertical margins between subplots
    w_fixed += margin_h * (ncols-1)
    # Calculate vertical extent for the rubber plot
    w_rubber = adj_r - adj_l - w_fixed
    # Initialize cumulative vertical coordinate
    xmin = adj_l - margins_l[0]
    # Loop through axes
    for (j, i) in enumerate(subplot_list):
        # Get axes
        ax = ax_list[i-1]
        # Check if it's the rubber plot
        if ax is ax_rubber:
            # Use the previously calculated height
            wj = w_rubber
        else:
            # Use the current extent
            wj = extents[j][2]
        # Add bottom text margin
        xmin += margins_l[j]
        # Set position
        ax.set_position([xmin, adj_b, wj, h_all])
        # Add top text margin and vspace
        xmin += margins_r[j] + margin_h
        # Add plot extent
        xmin += wj


# Get extents of axes in figure fraction coordinates
def get_axes_plot_extents(ax=None):
    r"""Get extents of axes plot in figure fraction coordinates

    :Call:
        >>> xmin, ymin, xmax, ymax = get_axes_plot_extents(ax)
    :Inputs:
        *ax*: {``None``} | :class:`Axes`
            Axes handle (defaults to ``plt.gca()``)
    :Outputs:
        *xmin*: :class:`float`
            Horizontal coord of plot region left edge, 0 is figure left
        *ymin*: :class:`float`
            Vertical coord of plot region bottom edge, 0 is fig bottom
        *xmax*: :class:`float`
            Horizontal coord of plot region right edge, 1 is fig right
        *ymax*: :class:`float`
            Vertical coord of plot region top edge, 1 is figure's top
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Import modules
    import_pyplot()
    # Default axes
    if ax is None:
        ax = plt.gca()
    # Get figure
    fig = ax.figure
    # Draw the figure once to ensure the extents can be calculated
    ax.draw(fig.canvas.get_renderer())
    # Size of figure in pixels
    _, _, ifig, jfig = fig.get_window_extent().bounds
    # Get pixel count for axes extents
    ia, ja, ib, jb = _get_axes_extents(ax)
    # Convert to fractions
    xmin = ia / ifig
    ymin = ja / jfig
    xmax = ib / ifig
    ymax = jb / jfig
    # Output
    return xmin, ymin, xmax, ymax


# Get extents of axes with labels
def get_axes_full_extents(ax=None):
    r"""Get extents of axes including labels in figure fraction coords

    :Call:
        >>> xmin, ymin, xmax, ymax = get_axes_full_extents(ax)
    :Inputs:
        *ax*: {``None``} | :class:`Axes`
            Axes handle (defaults to ``plt.gca()``)
    :Outputs:
        *xmin*: :class:`float`
            Horizontal coord of plot region left edge, 0 is figure left
        *ymin*: :class:`float`
            Vertical coord of plot region bottom edge, 0 is fig bottom
        *xmax*: :class:`float`
            Horizontal coord of plot region right edge, 1 is fig right
        *ymax*: :class:`float`
            Vertical coord of plot region top edge, 1 is figure's top
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Import modules
    import_pyplot()
    # Default axes
    if ax is None:
        ax = plt.gca()
    # Get figure
    fig = ax.figure
    # Draw the figure once to ensure the extents can be calculated
    ax.draw(fig.canvas.get_renderer())
    # Size of figure in pixels
    _, _, ifig, jfig = fig.get_window_extent().bounds
    # Get pixel count for axes extents
    ia, ja, ib, jb = _get_axes_full_extents(ax)
    # Convert to fractions
    xmin = ia / ifig
    ymin = ja / jfig
    xmax = ib / ifig
    ymax = jb / jfig
    # Output
    return xmin, ymin, xmax, ymax


# Get extents of axes with labels
def get_axes_label_margins(ax=None):
    r"""Get margins occupied by axis and tick labels on axes' four sides

    :Call:
        >>> wl, hb, wr, ht = get_axes_label_margins(ax)
    :Inputs:
        *ax*: {``None``} | :class:`Axes`
            Axes handle (defaults to ``plt.gca()``)
    :Outputs:
        *wl*: :class:`float`
            Figure fraction beyond plot of labels on left
        *hb*: :class:`float`
            Figure fraction beyond plot of labels below
        *wr*: :class:`float`
            Figure fraction beyond plot of labels on right
        *ht*: :class:`float`
            Figure fraction beyond plot of labels above
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Import modules
    import_pyplot()
    # Default axes
    if ax is None:
        ax = plt.gca()
    # Get figure
    fig = ax.figure
    # Draw the figure once to ensure the extents can be calculated
    ax.draw(fig.canvas.get_renderer())
    # Size of figure in pixels
    _, _, ifig, jfig = fig.get_window_extent().bounds
    # Get pixel count for axes extents
    wa, ha, wb, hb = _get_axes_label_margins(ax)
    # Convert to fractions
    margin_l = wa / ifig
    margin_b = ha / jfig
    margin_r = wb / ifig
    margin_t = hb / jfig
    # Output
    return margin_l, margin_b, margin_r, margin_t


# Get extents of axes in pixels
def _get_axes_plot_extents(ax):
    r"""Get extents of axes plot in figure fraction coordinates

    :Call:
        >>> ia, ja, ib, jb = _get_axes_plot_extents(ax)
    :Inputs:
        *ax*: :class:`Axes`
            Axes handle
    :Outputs:
        *ia*: :class:`float`
            Pixel count of plot region left edge, 0 is figure left
        *ja*: :class:`float`
            Pixel count of plot region bottom edge, 0 is fig bottom
        *ib*: :class:`float`
            Pixel count of plot region right edge
        *jb*: :class:`float`
            Pixel count of plot region top edge
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Get pixel count for axes extents
    ia, ja, iw, jh = ax.get_window_extent().bounds
    # Add width and height
    ib = ia + iw
    jb = ja + jh
    # Output
    return ia, ja, ib, jb


# Get extents of axes with labels
def _get_axes_full_extents(ax):
    r"""Get extents of axes including labels in pixels

    :Call:
        >>> ia, ja, ib, jb = _get_axes_full_extents(ax)
    :Inputs:
        *ax*: :class:`Axes`
            Axes handle
    :Outputs:
        *ia*: :class:`float`
            Pixel count of plot plus labels left edge
        *ja*: :class:`float`
            Pixel count of plot plus labels bottom edge
        *ib*: :class:`float`
            Pixel count of plot plus labels right edge
        *jb*: :class:`float`
            Pixel count of plot plus labels top edge
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Get pixel count for axes extents
    ia, ja, ib, jb = _get_axes_plot_extents(ax)
    # Get plot window bounds to check for valid tick labels
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    # Get axis label extents
    ia_x, ja_x, iw_x, jw_x = ax.xaxis.label.get_window_extent().bounds
    ia_y, ja_y, iw_y, jw_y = ax.yaxis.label.get_window_extent().bounds
    # Initialize bounds of labels and axes, if the extent is nonzero
    if iw_x*jw_x > 0:
        # Get axes bounds
        ib_x = ia_x + iw_x
        jb_x = ja_x + jw_x
        # Note: could be logical here and just use xlabel to set bottom
        # bounds, but why not be conservative?
        ia = min(ia, ia_x)
        ib = max(ib, ib_x)
        ja = min(ja, ja_x)
        jb = max(jb, jb_x)
    # Process ylabel
    if iw_y*jw_y > 0:
        # Get axes bounds
        ib_y = ia_y + iw_y
        jb_y = ja_y + jw_y
        # Note: could be logical here and just use xlabel to set bottom
        # bounds, but why not be conservative?
        ia = min(ia, ia_y)
        ib = max(ib, ib_y)
        ja = min(ja, ja_y)
        jb = max(jb, jb_y)
    # Loop through xtick labels
    for tick in ax.get_xticklabels():
        # Get position in data coordinates
        xtick, _ = tick.get_position()
        # Check if it's clipped
        if (xtick < xmin) or (xtick > xmax):
            continue
        # Get window extents
        ia_t, ja_t, iw_t, jw_t = tick.get_window_extent().bounds
        # Check for null tick
        if iw_t*jw_t == 0.0:
            continue
        # Translate to actual bounds
        ib_t = ia_t + iw_t
        jb_t = ja_t + jw_t
        # Update bounds
        ia = min(ia, ia_t)
        ib = max(ib, ib_t)
        ja = min(ja, ja_t)
        jb = max(jb, jb_t)
    # Loop through ytick labels
    for tick in ax.get_yticklabels():
        # Get position in data coordinates
        _, ytick = tick.get_position()
        # Check if it's clipped
        if (ytick < ymin) or (ytick > ymax):
            continue
        # Get window extents
        ia_t, ja_t, iw_t, jw_t = tick.get_window_extent().bounds
        # Check for null tick
        if iw_t*jw_t == 0.0:
            continue
        # Translate to actual bounds
        ib_t = ia_t + iw_t
        jb_t = ja_t + jw_t
        # Update bounds
        ia = min(ia, ia_t)
        ib = max(ib, ib_t)
        ja = min(ja, ja_t)
        jb = max(jb, jb_t)
    # Deal with silly scaling factors for both axes
    for tick in [ax.xaxis.offsetText, ax.yaxis.offsetText]:
        # Get window extents
        ia_t, ja_t, iw_t, jw_t = tick.get_window_extent().bounds
        # Check for null tick
        if iw_t*jw_t == 0.0:
            continue
        # Translate to actual bounds
        ib_t = ia_t + iw_t
        jb_t = ja_t + jw_t
        # Update bounds
        ia = min(ia, ia_t)
        ib = max(ib, ib_t)
        ja = min(ja, ja_t)
        jb = max(jb, jb_t)
    # Output
    return ia, ja, ib, jb


# Get extents of axes with labels
def _get_axes_label_margins(ax):
    r"""Get pixel counts of tick and axes labels on all four sides

    :Call:
        >>> wa, ha, wb, hb = _get_axes_label_margins(ax)
    :Inputs:
        *ax*: :class:`Axes`
            Axes handle
    :Outputs:
        *wa*: :class:`float`
            Pixel count beyond plot of labels on left
        *ha*: :class:`float`
            Pixel count beyond plot of labels below
        *wb*: :class:`float`
            Pixel count beyond plot of labels on right
        *hb*: :class:`float`
            Pixel count beyond plot of labels above
    :Versions:
        * 2020-01-08 ``@ddalle``: First version
    """
    # Get pixel count for plot extents
    ia_ax, ja_ax, ib_ax, jb_ax = _get_axes_plot_extents(ax)
    # Get pixel count for plot extents
    ia, ja, ib, jb = _get_axes_full_extents(ax)
    # Margins
    wa = ia_ax - ia
    ha = ja_ax - ja
    wb = ib - ib_ax
    hb = jb - jb_ax
    # Output
    return wa, ha, wb, hb


# Show an image
def imshow(png, **kw):
    r"""Display an image

    :Call:
        >>> img = imshow(fpng, **kw)
        >>> img = imshow(png, **kw)
    :Inputs:
        *fpng*: :class:`str`
            Name of PNG file
        *png*: :class:`np.ndarray`
            Image array from :func:`plt.imread`
        *ImageXMin*: {``0.0``} | :class:`float`
            Coordinate for left edge of image
        *ImageXMax*: {``None``} | :class:`float`
            Coordinate for right edge of image
        *ImageXCenter*: {``None``} | :class:`float`
            Horizontal center coord if *x* edges not specified
        *ImageYMin*: {``None``} | :class:`float`
            Coordinate for bottom edge of image
        *ImageYMax*: {``None``} | :class:`float`
            Coordinate for top edge of image
        *ImageYCenter*: {``0.0``} | :class:`float`
            Vertical center coord if *y* edges not specified
        *ImageExtent*: {``None``} | :class:`tuple` | :class:`list`
            Spec for *ImageXMin*, *ImageXMax*, *ImageYMin*, *ImageYMax*
    :Outputs:
        *img*: :class:`matplotlib.image.AxesImage`
            Image handle
    :Versions:
        * 2020-01-09 ``@ddalle``: First version
    """
    # Make sure modules are loaded
    import_pyplot()
    # Process opts
    opts = MPLOpts(**kw)
    # Get opts for imshow
    kw_imshow = opts.imshow_options()
    # Use basic function
    return _imshow(png, **kw_imshow)


# Show an image
def _imshow(png, **kw):
    r"""Display an image

    :Call:
        >>> img = _imshow(fpng, **kw)
        >>> img = _imshow(png, **kw)
    :Inputs:
        *fpng*: :class:`str`
            Name of PNG file
        *png*: :class:`np.ndarray`
            Image array from :func:`plt.imread`
        *ImageXMin*: {``0.0``} | :class:`float`
            Coordinate for left edge of image
        *ImageXMax*: {``None``} | :class:`float`
            Coordinate for right edge of image
        *ImageXCenter*: {``None``} | :class:`float`
            Horizontal center coord if *x* edges not specified
        *ImageYMin*: {``None``} | :class:`float`
            Coordinate for bottom edge of image
        *ImageYMax*: {``None``} | :class:`float`
            Coordinate for top edge of image
        *ImageYCenter*: {``0.0``} | :class:`float`
            Vertical center coord if *y* edges not specified
        *ImageExtent*: {``None``} | :class:`tuple` | :class:`list`
            Spec for *ImageXMin*, *ImageXMax*, *ImageYMin*, *ImageYMax*
    :Outputs:
        *img*: :class:`matplotlib.image.AxesImage`
            Image handle
    :Versions:
        * 2020-01-09 ``@ddalle``: First version
    """
    # Process input
    if typeutils.isstr(png):
        # Check if file exists
        if not os.path.isfile(png):
            raise SystemError("No PNG file '%s'" % png)
        # Read it
        png = plt.imread(png)
    elif not isinstance(png, np.ndarray):
        # Bad type
        raise TypeError("Image array must be NumPy array")
    elif png.nd not in [2, 3]:
        # Bad dimension
        raise ValueError("Image array must be 2D or 3D (got %i dims)" % png.nd)
    # Process image size
    png_rows = png.shape[0]
    png_cols = png.shape[1]
    # Aspect ratio
    png_ar = float(png_rows) / float(png_cols)
    # Process input coordinates
    xmin = kw.get("ImageXMin")
    xmax = kw.get("ImageXMax")
    ymin = kw.get("ImageYMin")
    ymax = kw.get("ImageYMax")
    # Middle coordinates if filling in
    xmid = kw.get("ImageXCenter")
    ymid = kw.get("ImageYCenter")
    # Check both axes if either side is specified
    x_nospec = (xmin is None) and (xmax is None)
    y_nospec = (ymin is None) and (ymax is None)
    # Fill in defaults
    if x_nospec and y_nospec:
        # All defaults
        extent = (0, png_cols, png_rows, 0)
    elif y_nospec:
        # Check which side(s) specified
        if xmin is None:
            # Read *xmin* from right edge
            xmin = xmax - png_cols
        elif xmax is None:
            # Read *xmax* from left edge
            xmax = xmin + png_cols
        # Specify default *y* values
        yhalf = 0.5 * (xmax - xmin) * png_ar
        # Create *y* window
        if ymid is None:
            # Use ``0``
            ymin = -yhalf
            ymax = yhalf
        else:
            # Use center
            ymin = ymid - yhalf
            ymax = ymid + yhalf
        # Extents
        extent = (xmin, xmax, ymin, ymax)
    elif x_nospec:
        # Check which side(s) specified
        if ymin is None:
            # Read *xmin* from right edge
            ymin = ymax - png_rows
        elif xmax is None:
            # Read *xmax* from left edge
            ymax = ymin + png_rows
        # Scale *x* width
        xwidth = (ymax - ymin) / png_ar
        # Check for a center
        if xmid is None:
            # Use ``0`` for left edge
            xmin = 0.0
            xmax = xwidth
        else:
            # Use specified center
            xmin = xmid - 0.5*xwidth
            xmax = xmid + 0.5*xwidth
        # Extents
        extent = (xmin, xmax, ymin, ymax)
    else:
        # Check which side(s) of *x* is(are) specified
        if xmin is None:
            # Read *xmin* from right edge
            xmin = xmax - png_cols
        elif xmax is None:
            # Read *xmax* from left edge
            xmax = xmin + png_cols
        # Check which side(s) of *y* is(are) specified
        if ymin is None:
            # Read *xmin* from right edge
            ymin = ymax - png_rows
        elif xmax is None:
            # Read *xmax* from left edge
            ymax = ymin + png_rows
        # Extents
        extent = (xmin, xmax, ymin, ymax)
    # Check for directly specified width
    kw_extent = kw.get("ImageExtent")
    # Override ``None``
    if kw_extent is not None:
        extent = kw_extent
    # Show the image
    img = plt.imshow(png, extent=extent)
    # Output
    return img


# Primary Histogram plotter
def hist(v, **kw):
    """Plot histograms with many options

    :Call:
        >>> h, kw = plot_base(xv, yv, *a, **kw)
    :Inputs:
        *v*: :class:`np.ndarray` (:class:`float`)
            List of values for which to create histogram
    :Outputs:
        *h*: :class:`dict`
            Dictionary of plot handles
    :Versions:
        * 2019-03-11 ``@jmeeroff``: function created
    """
   # --- Prep ---
    # Ensure plot() is loaded
    import_pyplot()
    # Initialize output
    h = {}
    # Filter out non-numeric entries
    v = v[np.logical_not(np.isnan(v))]
    # define coefficient for labeling
    coeff = kw.pop("coeff", "c")
   # --- Statistics ---
    # Calculate the mean
    vmu = np.mean(v)
    # Calculate StdDev
    vstd = np.std(v)
    # Coverage Intervals
    cov = kw.pop("Coverage", kw.pop("cov", 0.99))
    cdf = kw.pop("CoverageCDF", kw.pop("cdf", cov))
    # Nominal bounds (like 3-sigma for 99.5% coverage, etc.)
    kcdf = student.ppf(0.5+0.5*cdf, v.size)
    # Check for outliers ...
    fstd = kw.pop('FilterSigma', 2.0*kcdf)
    # Remove values from histogram
    if fstd:
        # Find indices of cases that are within outlier range
        j = np.abs(v-vmu)/vstd <= fstd
        # Filter values
        v = v[j]
    # Calculate interval
    acov, bcov = stats.get_cov_interval(v, cov, cdf=cdf, **kw)
   # --- Universal Options ---
    # dictionary for universal options
    # 1 -- Orientation
    orient = kw.pop("orientation", "vertical")
    kw_u = {
        "orientation": orient,
    }
   # --- Figure Setup ---
    # Process figure options
    kw_f = mplopts.figure_options(kw)
    # Get/create figure
    h["fig"] = figure(**kw_f)
   # --- Axis Setup ---
    # Process axis options
    kw_a = mplopts.axes_options(kw)
    # Get/create axis
    ax = axes(**kw_a)
    # Save it
    h["ax"] = ax
   # --- Histogram Plot ---
    # Process histogram plot options
    kw_p = mplopts.hist_options(kw, kw_u)
    # Plot
    h['hist'] = _hist(v, **kw_p)
   # --- Plot Gaussian ---
    normed = kw_p['density']
    # Need to pop the gaussian command regardless
    qgaus = kw.pop("PlotGaussian", True)
    # Only plot gaussian if the historgram is 'normed'
    qgaus = normed and qgaus
    # Process gaussian options
    kw_gauss = mplopts.gauss_options(kw, kw_p, kw_u)
    # Plot gaussian
    if qgaus:
        h['gauss'] = plot_gaussian(ax, vmu, vstd, **kw_gauss)
   # --- Axis formatting ---
    # Process grid lines options
    kw_gl = mplopts.grid_options(kw, kw_p, kw_u)
    # Apply grid lines
    grid(ax, **kw_gl)
    # Process spine options
    kw_sp = mplopts.spine_options(kw, kw_p, kw_u)
    # Apply options relating to spines
    h["spines"] = format_spines(ax, **kw_sp)
    # Process axes format options
    kw_axfmt = mplopts.axformat_options(kw, kw_p, kw_u)
    # Force y=0 or x=0 depending on orientation
    if orient == "vertical":
        kw_axfmt['YMin'] = 0
    else:
        kw_axfmt['XMin'] = 0
    # Apply formatting
    h['xlabel'], h['ylabel'] = axes_format(h['ax'], **kw_axfmt)
   # --- Plot an Interval ---
    # Get flag for manual interval plot
    qint = kw.pop("PlotInterval", False)
    # Process options
    kw_interval = mplopts.interval_options(kw, kw_p, kw_u)
    # Plot if necessary
    if qint:
        h['interval'] = plot_interval(ax, acov, bcov, **kw_interval)
   # --- Plot Mean ---
    qmu = kw.pop("PlotMean", True)
    # Process mean options
    kw_mu = mplopts.mu_options(kw, kw_p, kw_u)
    # Plot the mean
    if qmu:
        h['mean'] = plot_mean(ax, vmu, **kw_mu)
   # --- Plot Standard Deviation ---
    qsig = kw.pop("PlotSigma", False)
    # Process sigma options
    kw_s = mplopts.std_options(kw, kw_p, kw_u)
    # Plot the sigma
    if qsig:
        h['sigma'] = _plots_std(ax, vmu, vstd, **kw_s)
   # --- Delta Plot ----
    qdel = kw.pop("PlotDelta", False)
    # Process delta options
    kw_delta = mplopts.delta_options(kw, kw_p, kw_u)
    # Plot the delta
    if qdel:
        h['delta'] = plot_delta(ax, vmu, **kw_delta)
   # --- Mean labels ---
    # Process mean labeling options
    opts = kw.pop("MeanLabelOptions", {})
    kw_mu_lab = mplopts.histlabel_options(opts, kw_p, kw_u)
    c = kw_mu_lab.pop('clabel', 'mu')
    # Do the label
    if qmu:
        # Formulate the label
        # Format code
        flbl = kw_mu_lab.pop("MuFormat", "%.4f")
        # First part
        klbl = (u'%s' % c)
        # Insert value
        lbl = ('%s = %s' % (klbl, flbl)) % vmu
        h['MeanLabel'] = histlab_part(lbl, 0.99, True, ax, **kw_mu_lab)
   # --- StdDev labels ---
    # Process mean labeling options
    opts = kw.pop("SigmaLabelOptions", {})
    # Make sure alignment is correct
    opts.setdefault('horizontalalignment', 'left')
    kw_sig_lab = mplopts.histlabel_options(opts, kw_p, kw_u)
    c = kw_sig_lab.pop('clabel', coeff)
    # Do the label
    if qsig:
        # Formulate the label
        # Format code
        flbl = kw_mu_lab.pop("SigFormat", "%.4f")
        # First part
        klbl = (u'\u03c3(%s)' % c)
        # Insert value
        lbl = ('%s = %s' % (klbl, flbl)) % vstd
        h['SigmaLabel'] = histlab_part(lbl, 0.01, True, ax, **kw_sig_lab)
   # --- Interval Labels ---
    # Process mean labeling options
    opts = kw.pop("IntLabelOptions", {})
    kw_int_lab = mplopts.histlabel_options(opts, kw_p, kw_u)
    c = kw_int_lab.pop('clabel', cov)
    if qint:
        flbl = kw_sig_lab.get("IntervalFormat", "%.4f")
        # Form
        klbl = "I(%.1f%%%%)" % (100*c)
        # Get ionterval values
        a = kw_interval.get('imin', None)
        b = kw_interval.get('imax', None)
        # Insert value
        lbl = ('%s = [%s,%s]' % (klbl, flbl, flbl)) % (a, b)
        h['IntLabel'] = histlab_part(lbl, 0.99, False, ax, **kw_int_lab)
   # --- Delta Labels ---
    # Process Delta labeling options
    opts = kw.pop("DeltaLabelOptions", {})
    opts.setdefault('horizontalalignment', 'left')
    kw_del_lab = mplopts.histlabel_options(opts, kw_p, kw_u)
    c = kw_del_lab.pop('clabel', 'coeff')
    if qdel:
        flbl = kw_del_lab.get("DeltaFormat", "%.4f")
        # Get delta values
        dc = kw_delta.get('Delta', 0.0)
        # Insert value
        if type(dc).__name__ in ['ndarray', 'list', 'tuple']:
            lbl = (u'\u0394%s = (%s, %s)' % (c, flbl, flbl)) % (dc[0], dc[1])
        else:
            lbl = (u'\u0394%s = %s' % (c, flbl)) % dc
        h['delta'] = histlab_part(lbl, 0.01, False, ax, **kw_del_lab)
   # --- Cleanup ---
    # Any unused keys?
    genopts.display_remaining("plot_hist", "    ", **kw)
    # Output
    return h


# Figure part
def figure(**kw):
    r"""Get or create figure handle and format it

    :Call:
        >>> fig = figure(**kw)
    :Inputs:
        *fig*: {``None``} | :class:`matplotlib.figure.Figure`
            Optional figure handle
        *FigOptions*: {``None``} | :class:`dict`
            Options to apply to figure handle using :func:`fig.set`
    :Outputs:
        *fig*: :class:`matplotlib.figure.Figure`
            Figure handle
    :Versions:
        * 2019-03-06 ``@ddalle``: First version
    """
    # Import PyPlot
    import_pyplot()
    import_matplotlib()
    # Get figure handle and other options
    fig = kw.get("fig", None)
    figopts = kw.get("FigOptions", {})
    # Check for a figure number
    fignum = figopts.pop("num", None)
    # Create figure if needed
    if not isinstance(fig, mplfig.Figure):
        # Check for specified figure
        if fignum is None:
            # Use most recent figure (can be new one)
            fig = plt.gcf()
        else:
            # Get specified figure
            fig = plt.figure(fignum)
    # Loop through options
    for (k, v) in figopts.items():
        # Check for None
        if not v:
            continue
        # Get setter function
        fn = getattr(fig, "set_" + k, None)
        # Check property
        if fn is None:
            sys.stderr.write("No figure property '%s'\n" % k)
            sys.stderr.flush()
        # Apply setter
        fn(v)
    # Output
    return fig


# Axis part (initial)
def axes(**kw):
    """Create new axes or edit one if necessary

    :Call:
        >>> fig = axes(**kw)
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Optional axes handle
        *AxesOptions*: {``None``} | :class:`dict`
            Options to apply to figure handle using :func:`ax.set`
    :Outputs:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
    :Versions:
        * 2019-03-06 ``@ddalle``: First version
    """
    # Import PyPlot
    import_pyplot()
    # Get figure handle and other options
    ax = kw.get("ax", None)
    axopts = kw.get("AxesOptions", {})
    # Check for a subplot description
    axnum = axopts.pop("subplot", None)
    # Create figure if needed
    if not isinstance(ax, mplax._subplots.Axes):
        # Check for specified figure
        if axnum is None:
            # Use most recent figure (can be new one)
            ax = plt.gca()
        else:
            # Get specified figure
            ax = plt.subplot(axnum)
    # Loop through options
    for (k, v) in axopts.items():
        # Check for None
        if not v:
            continue
        # Get setter function
        fn = getattr(ax, "set_" + k, None)
        # Check property
        if fn is None:
            sys.stderr.write("No axes property '%s'\n" % k)
            sys.stderr.flush()
        # Apply setter
        fn(v)
    # Output
    return ax


# Plot part
def _plot_nocheck(xv, yv, fmt, **kw):
    r"""Call the :func:`plot` function with cycling options

    :Call:
        >>> h = _plot(xv, yv, **kw)
        >>> h = _plot(xv, yv, fmt, **kw)
    :Inputs:
        *xv*: :class:`np.ndarray`
            Array of *x*-coordinates
        *yv*: :class:`np.ndarray`
            Array of *y*-coordinates
        *fmt*: :class:`str`
            Optional format option
        *i*, *Index*: {``0``} | :class:`int`
            Phase number to cycle through plot options
        *rotate*, *Rotate*: ``True`` | {``False``}
            Plot independent variable on vertical axis
    :Keyword Arguments:
        * See :func:`matplotlib.pyplot.plot`
    :Outputs:
        *h*: :class:`list` (:class:`matplotlib.lines.Line2D`)
            List of line instances
    :Versions:
        * 2019-03-04 ``@ddalle``: First version
    """
    # Ensure plot() is available
    import_pyplot()
    # Get index
    i = kw.pop("Index", kw.pop("i", 0))
    # Get rotation option
    r = kw.pop("Rotate", kw.pop("rotate", False))
    # Flip inputs
    if r:
        yv, xv = xv, yv
    # Initialize plot options
    kw_p = MPLOpts.select_phase(kw, i)
    # Call plot
    if typeutils.isstr(fmt):
        # Call with extra format argument
        h = plt.plot(xv, yv, fmt, **kw_p)
    else:
        # No format argument
        h = plt.plot(xv, yv, **kw_p)
    # Output
    return h


def _plot(xv, yv, fmt=None, **kw):
    r"""Call the :func:`plot` function with cycling options

    :Call:
        >>> h = _plot(xv, yv, **kw)
        >>> h = _plot(xv, yv, fmt, **kw)
    :Inputs:
        *xv*: :class:`np.ndarray`
            Array of *x*-coordinates
        *yv*: :class:`np.ndarray`
            Array of *y*-coordinates
        *fmt*: :class:`str`
            Optional format option
        *i*, *Index*: {``0``} | :class:`int`
            Phase number to cycle through plot options
        *rotate*, *Rotate*: ``True`` | {``False``}
            Plot independent variable on vertical axis
    :Keyword Arguments:
        * See :func:`matplotlib.pyplot.plot`
    :Outputs:
        *h*: :class:`list` (:class:`matplotlib.lines.Line2D`)
            List of line instances
    :Versions:
        * 2019-03-04 ``@ddalle``: First version
    """
    # Process options
    opts = MPLOpts(**kw)
    # Get plot options
    kw_p = opts.plot_options()
    # Call root function
    return _plot_nocheck(xv, yv, fmt=fmt, **kw_p)


# Move axes all the way to one side
def move_axes(ax, loc, margin=0.0):
    r"""Move an axes object's plot region to one side

    :Call:
        >>> move_axes(ax, loc, margin=0.0)
    :Inputs:
        *ax*: :class:`Axes`
            Axes handle
        *loc*: :class:`str` | :class:`int`
            Direction to move axes

                ===========================  ============
                String                       Code
                ===========================  ============
                ``"top"`` | ``"up"``         ``1``
                ``"right"``                  ``2``
                ``"bottom"`` | ``"down"``    ``3``
                ``"left"``                   ``4``
                ===========================  ============

        *margin*: {``0.0``} | :class:`float`
            Margin to leave outside of axes and tick labels
    :Versions:
        * 2020-01-10 ``@ddalle``: First version
    """
    # Import plot modules
    import_pyplot()
    # Check inputs
    if not isinstance(loc, (int, typeutils.strlike)):
        raise TypeError("Location must be int or str (got %s)" % type(loc))
    elif isinstance(loc, int) and (loc < 1 or loc > 10):
        raise TypeError("Location int must be in [1 .. 4] (got %i)" % loc)
    elif not isinstance(margin, float):
        raise TypeError("Margin must be float (got %s)" % type(margin))
    # Get axes
    if ax is None:
        ax = plt.gca()
    # Get current position
    xmin, ymin, w, h = ax.get_position().bounds
    # Max positions
    xmax = xmin + w
    ymax = ymin + h
    # Get extents occupied by labels
    wa, ha, wb, hb = get_axes_label_margins(ax)
    # Filter location
    if loc in [1, "top", "up"]:
        # Get shift directions to top edge
        dx = 0.0
        dy = 1.0 - hb - margin - ymax
    elif loc in [2, "right"]:
        # Get shift direction to right edge
        dx = 1.0 - wb - margin - xmax
        dy = 0.0
    elif loc in [3, "bottom", "down"]:
        # Get shift direction to bottom
        dx = 0.0
        dy = margin + ha - ymin
    elif loc in [4, "left"]:
        # Get shift direction to bottom and right
        dx = margin + wa - xmin
        dy = 0.0 
    else:
        # Unknown string
        raise ValueError("Unknown location string '%s'" % loc)
    # Set new position
    ax.set_position([xmin + dx, ymin + dy, w, h])


# Nudge axes without resizing
def nudge_axes(ax, dx=0.0, dy=0.0):
    r"""Move an axes object's plot region to one side

    :Call:
        >>> nudge_axes(ax, dx=0.0, dy=0.0)
    :Inputs:
        *ax*: :class:`Axes`
            Axes handle
        *dx*: {``0.0``} | :class:`float`
            Figure fraction to move axes to the right
        *dy*: {``0.0``} | :class:`float`
            Figure fraction to move axes upward
    :Versions:
        * 2020-01-10 ``@ddalle``: First version
    """
    # Import plot modules
    import_pyplot()
    # Check inputs
    if not isinstance(dx, float):
        raise TypeError("dx must be float (got %s)" % type(dx))
    if not isinstance(dy, float):
        raise TypeError("dy must be float (got %s)" % type(dy))
    # Get axes
    if ax is None:
        ax = plt.gca()
    # Get current position
    xmin, ymin, w, h = ax.get_position().bounds
    # Set new position
    ax.set_position([xmin + dx, ymin + dy, w, h])


# Region plot
def fill_between(xv, ymin, ymax, **kw):
    r"""Call the :func:`fill_between` or :func:`fill_betweenx` function

    :Call:
        >>> h = fill_between(xv, ymin, ymax, **kw)
    :Inputs:
        *xv*: :class:`np.ndarray`
            Array of independent variable values
        *ymin*: :class:`np.ndarray` | :class:`float`
            Array of values or single value for lower bound of window
        *ymax*: :class:`np.ndarray` | :class:`float`
            Array of values or single value for upper bound of window
        *i*, *Index*: {``0``} | :class:`int`
            Phase number to cycle through plot options
        *Rotate*: ``True`` | {``False``}
            Option to plot independent variable on vertical axis
    :Versions:
        * 2019-03-04 ``@ddalle``: First version
        * 2019-08-22 ``@ddalle``: Renamed from :func:`fillbetween`
    """
   # --- Values ---
    # Convert possible scalar for *ymin*
    if isinstance(ymin, float):
        # Expand scalar to array
        yl = ymin*np.ones_like(xv)
    elif typeutils.isarray(ymin):
        # Ensure array (not list, etc.)
        yl = np.asarray(ymin)
    else:
        raise TypeError(
            ("'ymin' value must be either float or array ") +
            ("(got %s)" % ymin.__class__))
    # Convert possible scalar for *ymax*
    if isinstance(ymax, float):
        # Expand scalar to array
        yu = ymax*np.ones_like(xv)
    elif typeutils.isarray(ymax):
        # Ensure array (not list, etc.)
        yu = np.asarray(ymax)
    else:
        raise TypeError(
            ("'ymax' value must be either float or array ") +
            ("(got %s)" % ymax.__class__))
   # --- Main ---
    # Ensure fill_between() is available
    import_pyplot()
    # Get index
    i = kw.pop("i", kw.pop("Index", 0))
    # Get rotation option
    r = kw.pop("Rotate", False)
    # Check for vertical or horizontal
    if r:
        # Vertical function
        fnplt = plt.fill_betweenx
    else:
        # Horizontal function
        fnplt = plt.fill_between
    # Initialize plot options
    kw_fb = MPLOpts.select_phase(kw, i)
    # Call the plot method
    h = fnplt(xv, yl, yu, **kw_fb)
    # Output
    return h


# Error bar plot
def errorbar(xv, yv, yerr=None, xerr=None, **kw):
    r"""Call the :func:`errobar` function

    :Call:
        >>> h = errorbar(xv, yv, yerr=None, xerr=None, **kw
    :Inputs:
        *xv*: :class:`np.ndarray`
            Array of independent variable values
        *yv*: :class:`np.ndarray` | :class:`float`
            Array of values for center of error bar
        *yerr*: {``None``} | :class:`np.ndarray` | :class:`float`
            Array or constant error bar half-heights; shape(2,N) array
            for distinct above- and below-widths
        *xerr*: {``None``} | :class:`np.ndarray` | :class:`float`
            Array or constant error bar half-widths; shape(2,N) array
            for distinct above- and below-widths
        *i*, *Index*: {``0``} | :class:`int`
            Phase number to cycle through plot options
        *Rotate*: ``True`` | {``False``}
            Option to plot independent variable on vertical axis
    :Versions:
        * 2019-03-04 ``@ddalle``: First version
        * 2019-08-22 ``@ddalle``: Renamed from :func:`errorbar_part`
    """
   # --- Values ---
    # Convert possible scalar for *yerr*
    if yerr is None:
        # No vertical uncertainty (?)
        uy = None
    elif isinstance(yerr, float):
        # Expand scalar to array
        uy = yerr*np.ones_like(yv)
    elif typeutils.isarray(yerr):
        # Ensure array (not list, etc.)
        uy = np.asarray(yerr)
    else:
        raise TypeError(
            ("'yerr' value must be either float or array ") +
            ("(got %s)" % yerr.__class__))
    # Convert possible scalar for *ymax*
    if xerr is None:
        # No horizontal uncertainty
        ux = None
    elif isinstance(xerr, float):
        # Expand scalar to array
        ux = xerr*np.ones_like(xv)
    elif typeutils.isarray(xerr):
        # Ensure array (not list, etc.)
        ux = np.asarray(xerr)
    else:
        raise TypeError(
            ("'xerr' value must be either None, float, or array ") +
            ("(got %s)" % yerr.__class__))
   # --- Main ---
    # Ensure fill_between() is available
    import_pyplot()
    # Get index
    i = kw.pop("i", kw.pop("Index", 0))
    # Get rotation option
    r = kw.pop("Rotate", False)
    # Check for vertical or horizontal
    if r:
        # Vertical function
        xv, yv, xerr, yerr = yv, xv, yerr, xerr
    # Initialize plot options
    kw_eb = MPLOpts.select_phase(kw, i)
    # Call the plot method
    h = plt.errorbar(xv, yv, yerr=uy, xerr=ux, **kw_eb)
    # Output
    return h


# Histogram
def _hist(v, **kw):
    """Call the :func:`hist` function

    :Call:
        >>> h = _hist(V, **kw))
    :Inputs:
        *v*: :class:`np.ndarray` (:class:`float`)
            List of values for which to create histogram
    :Keyword Arguments:
        * See :func:`matplotlib.pyplot.hist`
    :Outputs:
        *h*: :class: `tuple`
            Tuple of (n, bins, patches)
    :Versions:
        * 2019-03-11 ``@jmeeroff``: First version
        * 2019-08-22 ``@ddalle``: From :func:`Part.hist_part`
    """
    # Ensure hist() is available
    import_pyplot()
    # Call plot
    h = plt.hist(v, **kw)
    # Output
    return h


# Mean plotting part
def plot_mean(ax, vmu, **kw):
    """Plot the mean on the histogram

    :Call:
        >>> h = plot_mean(V, ax **kw))
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *vmu*: :class: 'float'
            Desired mean of distribution (`np.meam()`)
    :Keyword Arguments:
        *orientation*: {``"horizontal"``} | ``"vertical"``
            Option to flip *x* and *y* axes
    :Outputs:
        *h*: :class:`matplotlib.lines.Line2D`
            Handle to options for simple line
    :Versions:
        * 2019-03-11 ``@jmeeroff``: First version
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Get horizontal/vertical option
    orient = kw.pop('orientation', "")
    # Check orientation
    if orient == 'vertical':
        # Vertical: get vertical limits of axes window
        pmin, pmax = ax.get_ylim()
        # Plot a vertical mean line
        h = plt.plot([vmu, vmu], [pmin, pmax], **kw)

    else:
        # Horizontal: get horizontal limits of axes window
        pmin, pmax = ax.get_xlim()
        # Plot a horizontal range bar
        h = plt.plot([pmin, pmax], [vmu, vmu], **kw)
    # Return
    return h[0]


# Show an interval on a histogram
def plot_interval(ax, vmin, vmax, **kw):
    """Plot the mean on the histogram

    :Call:
        >>> h = plot_interval(ax, vmin, vmax, **kw))
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *vmin*: :class:`float`
            Minimum value of interval to plot
        *vmax*: :class:`float`
            Maximum value of interval to plot
    :Keyword Arguments:
        *orientation*: {``"horizontal"``} | ``"vertical"``
            Option to flip *x* and *y* axes
    :Outputs:
        *h*: :class:`matplotlib.collections.PolyCollection`
            Handle to interval plot
    :Versions:
        * 2019-03-11 ``@jmeeroff``: First version
        * 2019-08-22 ``@ddalle``: Added *vmin*, *vmax* inputs
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Get horizontal/vertical option
    orient = kw.pop('orientation', "")
    # Check orientation
    if orient == 'vertical':
        # Vertical: get vertical limits of axes window
        pmin, pmax = ax.get_ylim()
        # Plot a vertical range bar
        h = plt.fill_betweenx([pmin, pmax], vmin, vmax, **kw)

    else:
        # Horizontal: get horizontal limits of axes window
        pmin, pmax = ax.get_xlim()
        # Plot a horizontal range bar
        h = plt.fill_between([pmin, pmax], vmin, vmax, **kw)
    # Return
    return h


# Gaussian plotting part
def plot_gaussian(ax, vmu, vstd, **kw):
    """Plot a Gaussian distribution (on a histogram)

    :Call:
        >>> h = plot_gaussian(ax, vmu, vstd, **kw))
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *vmu*: :class: 'float'
            Mean of distribution
        *vstd*: :class: `float`
            Standard deviation of distribution
    :Keyword Arguments:
        *orientation*: {``"horizontal"``} | ``"vertical"``
            Option to flip *x* and *y* axes
        *ngauss*: {``151``} | :class:`int` > 2
            Number of points to use in Gaussian curve
    :Outputs:
        *h*: :class:`matplotlib.lines.Line2D`
            Handle to options for Gaussian curve
    :Versions:
        * 2019-03-11 ``@jmeeroff``: First version
        * 2019-08-22 ``@ddalle``: Added *ngauss*
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Get horizontal/vertical option
    orient = kw.pop('orientation', "")
    # Get axis limits
    if orient == "vertical":
        # Get existing horizontal limits
        xmin, xmax = ax.get_xlim()
    else:
        # Get existing
        xmin, xmax = ax.get_ylim()
    # Number of points to plot
    ngauss = kw.pop("ngauss", 151)
    # Create points at which to plot
    xval = np.linspace(xmin, xmax, ngauss)
    # Compute Gaussian distribution
    yval = 1/(vstd*np.sqrt(2*np.pi))*np.exp(-0.5*((xval-vmu)/vstd)**2)
    # Plot
    if orient == "vertical":
        # Plot vertical dist with bump pointing to the right
        h = plt.plot(xval, yval, **kw)
    else:
        # Plot horizontal dist with vertical bump
        h = plt.plot(yval, xval, **kw)
    # Return
    return h[0]


# Interval using two lines
def _plots_std(ax, vmu, vstd, **kw):
    """Use two lines to show standard deviation window

    :Call:
        >>> h = _plots_std(ax, vmu, vstd, **kw))
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *vmu*: :class: 'float'
            Desired mean of distribution (`np.meam()`)
        *vstd*: :class: `float`
            Desired standard deviation of distribution( `np.std()`)
    :Keyword Arguments:
        * "StdOptions" : :dict: of line `LineOptions`
    :Outputs:
        *h*: ``None`` | :class:`list`\ [:class:`matplotlib.Line2D`]
            List of line instances
    :Versions:
        * 2019-03-14 ``@jmeeroff``: First version
        * 2019-08-22 ``@ddalle``: From :func:`Part.std_part`
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Get orientation option
    orient = kw.pop('orientation', None)
    # Check multiplier
    ksig = kw.pop('StDev', None)
    # Exit if no standard deviation to show
    if not ksig:
        return
    # Plot lines
    if type(ksig).__name__ in ['ndarray', 'list', 'tuple']:
        # Separate lower and upper limits
        vmin = vmu - ksig[0]*vstd
        vmax = vmu + ksig[1]*vstd
    else:
        # Use as a single number
        vmin = vmu - ksig*vstd
        vmax = vmu + ksig*vstd
    # Check orientation
    if orient == 'vertical':
        # Get vertical limits
        pmin, pmax = ax.get_ylim()
        # Plot a vertical line for the min and max
        h = (
            plt.plot([vmin, vmin], [pmin, pmax], **kw) +
            plt.plot([vmax, vmax], [pmin, pmax], **kw))
    else:
        # Get horizontal limits
        pmin, pmax = ax.get_xlim()
        # Plot a horizontal line for the min and max
        h = (
            plt.plot([pmin, pmax], [vmin, vmin], **kw) +
            plt.plot([pmin, pmax], [vmax, vmax], **kw))
    # Return
    return h


# Delta Plotting
def plot_delta(ax, vmu, **kw):
    """Plot deltas on the histogram

    :Call:
        >>> h = plot_delta(ax, vmu, **kw))
    :Inputs:
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *vmu*: :class: 'float'
            Desired mean of distribution (`np.meam()`)
    :Keyword Arguments:
        * "DeltaOptions" : :dict: of line `LineOptions`
    :Outputs:
        *h*: :class:`list` (:class:`matplotlib.lines.Line2D`)
            List of line instances
    :Versions:
        * 2019-03-14 ``@jmeeroff``: First version
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Check orientation
    orient = kw.pop('orientation', None)
    # Reference delta
    dc = kw.pop('Delta', 0.0)
    # Check for single number or list
    if type(dc).__name__ in ['ndarray', 'list', 'tuple']:
        # Separate lower and upper limits
        cmin = vmu - dc[0]
        cmax = vmu + dc[1]
    else:
        # Use as a single number
        cmin = vmu - dc
        cmax = vmu + dc
    # Check orientation
    if orient == 'vertical':
        pmin, pmax = ax.get_ylim()
        # Plot a vertical line for the min and max
        h = (
            plt.plot([cmin, cmin], [pmin, pmax], **kw) +
            plt.plot([cmax, cmax], [pmin, pmax], **kw))
    else:
        pmin, pmax = ax.get_xlim()
        # Plot a horizontal line for the min and max
        h = (
            plt.plot([pmin, pmax], [cmin, cmin], **kw) +
            plt.plot([pmin, pmax], [cmax, cmax], **kw))
    # Return
    return h


# Histogram Labels Plotting
def histlab_part(lbl, pos1, pos2, ax, **kw):
    """Plot the mean on the histogram

    :Call:
        >>> h = histlab_part(lbl, pos, ax, **kw))
    :Inputs:
        *lbl*: :class:`string`
            Label title (i.e. coefficient)
        *ax*: ``None`` | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
        *pos1*: :class: `float`
            label locations (left to right alignment)
        *pos2*: :class: `boolean'
            above(True) below(False) top spine alignment
    :Keyword Arguments:
        * "*Options" : :dict: of `LabelOptions`
    :Outputs:
        *h*: :class:`list` (:class:`matplotlib.lines.Line2D`)
            List of label instances
    :Versions:
        * 2019-03-14 ``@jmeeroff``: First version
    """
    # Ensure pyplot loaded
    import_pyplot()
    # Remove orientation orientation
    kw.pop('orientation', None)
    # get figure handdle
    f = plt.gcf()
    # Y-coordinates of the current axes w.r.t. figure scale
    ya = ax.get_position().get_points()
    ha = ya[1, 1] - ya[0, 1]
    # Y-coordinates above and below the box
    yf = 2.5 / ha / f.get_figheight()
    yu = 1.0 + 0.065*yf
    yl = 1.0 - 0.04*yf
    # Above/Below Spine location
    if pos2:
        y = yu
    else:
        y = yl
    # plot the label
    h = plt.text(pos1, y, lbl, transform=ax.transAxes, **kw)
    return h


# Legend
def legend(ax=None, **kw):
    """Create/update a legend

    :Call:
        >>> leg = legend(ax=None, **kw)
    :Inputs:
        *ax*: {``None``} | :class:`matplotlib.axes._subplots.AxesSubplot`
            Axis handle (default is ``plt.gca()``
    :Outputs:
        *leg*: :class:`matplotlib.legend.Legend`
            Legend handle
    :Versions:
        * 2019-03-07 ``@ddalle``: First version
        * 2019-08-22 ``@ddalle``: From :func:`Part.legend_part`
    """
   # --- Setup ---
    # Check basic option
    # Import modules if needed
    import_pyplot()
    # Get overall "Legend" option
    show_legend = kw.pop("ShowLegend", None)
    # Exit immediately if explicit
    if show_legend is False:
        return
    # Get font properties (copy)
    opts_prop = dict(kw.pop("prop", {}))
    # Default axis: most recent
    if ax is None:
        ax = plt.gca()
    # Get figure
    fig = ax.get_figure()
   # --- Initial Attempt ---
    # Initial legend attempt
    try:
        # Use the options with specified font
        leg = ax.legend(prop=opts_prop, **kw)
    except Exception:
        # Remove font
        opts_prop.pop("family", None)
        # Repeat plot
        leg = ax.legend(prop=opts_prop, **kw)
   # --- Font ---
    # Number of entries in the legend
    ntext = len(leg.get_texts())
    # If no legends, remove it
    if (ntext < 1) or not show_legend:
        # Delete legend
        leg.remove()
        # Exit function
        return leg
    # Get number of columns, and apply default based on number of labels
    ncol = kw.setdefault("ncol", ntext // 5 + 1)
    # Get Number of rows
    nrow = (ntext // ncol) + (ntext % ncol > 0)
    # Default font size
    if nrow > 5:
        # Smaller font
        fsize = 7
    else:
        # Larger font (still pretty small)
        fsize = 9
    # Apply default font size
    opts_prop.setdefault("size", fsize)
   # --- Spacing ---
    # Penultimate legend
    leg = ax.legend(prop=opts_prop, **kw)
    # We have to draw the figure in order to get legend box
    fig.canvas.draw()
    # Get bounds of the legend box
    bbox = leg.get_window_extent()
    # Transformation so we convert the bounds of the legend into data space
    trans = ax.transData.inverted()
    # Convert to data space
    (xlmin, ylmin), (xlmax, ylmax) = trans.transform(bbox)
    # Get data limits
    xmin, xmax = get_xlim(ax, pad=0.0)
    ymin, ymax = get_ylim(ax, pad=0.0)
    # Get location
    loc = kw.get("loc")
    # Check for special cases
    if loc in ["upper center", 9]:
        # Check bottom of legend box
        if ylmin < ymax:
            # Get axes limits
            ya, yb = ax.get_ylim()
            # Extend the upper limit of *y*-axis to make room
            yu = yb + max(0.0, ymax-ylmin)
            # Set new limits
            ax.set_ylim(ya, yu)
    elif loc in ["lower center", 8]:
        # Check top of legend box
        if ylmax > ymin:
            # Get axes limits
            ya, yb = ax.get_ylim()
            # Extend the lower limit of *y*-axis to make room
            yl = ya - max(0.0, ylmax-ymin)
            # Set new limits
            ax.set_ylim(yl, yb)
   # --- Cleanup ---
    # Output
    return leg


# Axes format
def axes_format(ax, **kw):
    r"""Format and label axes

    :Call:
        >>> xl, yl = axes_format(ax, **kw)
    :Inputs:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
    :Outputs:
        *xl*: :class:`matplotlib.text.Text`
            X label
        *yl*: :class:`matplotlib.text.Text`
            Y label
    :Versions:
        * 2019-03-06 ``@jmeeroff``: First version
        * 2020-01-08 ``@ddalle``: 2.0, removed margin adjustment
        * 2020-01-08 ``@ddalle``: 2.1, from :func:`axes_format`
    """
   # --- Prep ---
    # Make sure pyplot loaded
    import_pyplot()
   # --- Labels ---
    # Get user-specified axis labels
    xlbl = kw.get("XLabel", None)
    ylbl = kw.get("YLabel", None)
    # Check for rotation kw
    rot = kw.get("Rotate", False)
    # Switch args if needed
    if rot:
        # Flip labels
        xlbl, ylbl = ylbl, xlbl
    # Check for orientation kw (histogram)
    orient = kw.get('orientation', None)
    if orient == 'vertical':
        # Flip labels
        xlbl, ylbl = ylbl, xlbl
    # Apply *x* label
    if xlbl is None:
        # Get empty label
        xl = ax.xaxis.label
    else:
        # Apply label
        xl = plt.xlabel(xlbl)
    # Apply *y* label
    if ylbl is None:
        # Get handle to empty label
        yl = ax.yaxis.label
    else:
        # Create non-empty label
        yl = plt.ylabel(ylbl)
   # --- Data Limits ---
    # Get pad parameter
    pad = kw.get("Pad", 0.05)
    # Specific pad parameters
    xpad = kw.get("XPad", pad)
    ypad = kw.get("YPad", pad)
    # Get limits that include all data (and not extra).
    xmin, xmax = get_xlim(ax, pad=xpad)
    ymin, ymax = get_ylim(ax, pad=ypad)
    # Check for specified limits
    xmin = kw.get("XLimMin", xmin)
    xmax = kw.get("XLimMax", xmax)
    ymin = kw.get("YLimMin", ymin)
    ymax = kw.get("YLimMax", ymax)
    # Check for typles
    xmin, xmax = kw.get("XLim", (xmin, xmax))
    ymin, ymax = kw.get("YLim", (ymin, ymax))
    # Make sure data is included.
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
   # --- Cleanup ---
    # Output
    return xl, yl


# Creation and formatting of grid lines
def grid(ax, **kw):
    r"""Add grid lines to an axis and format them

    :Call:
        >>> grid(ax, **kw)
    :Inputs:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
    :Effects:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Grid lines added to axes
    :Versions:
        * 2019-03-07 ``@jmeeroff``: First version
        * 2019-12-23 ``@ddalle``: Updated from :mod:`plotutils`
    """
    # Make sure pyplot loaded
    import_pyplot()
    # Get major grid option
    major_grid = kw.get("Grid", None)
    # Check value
    if major_grid is None:
        # Leave it as it currently is
        pass
    elif major_grid:
        # Get grid style
        kw_major = kw.get("GridOptions", {})
        # Ensure that the axis is below
        ax.set_axisbelow(True)
        # Add the grid
        ax.grid(True, **kw_major)
    else:
        # Turn the grid off, even if previously turned on
        ax.grid(False)
    # Get minor grid option
    minor_grid = kw.get("MinorGrid", None)
    # Check value
    if minor_grid is None:
        # Leave it as it currently is
        pass
    elif minor_grid:
        # Get grid style
        kw_minor = kw.get("MinorGridOptions", {})
        # Ensure that the axis is below
        ax.set_axisbelow(True)
        # Minor ticks are required
        ax.minorticks_on()
        # Add the grid
        ax.grid(which="minor", **kw_minor)
    else:
        # Turn the grid off, even if previously turned on
        ax.grid(False, which="minor")


# Single spine: extents
def format_spine1(spine, opt, vmin, vmax):
    r"""Apply visibility options to a single spine

    :Call:
        >>> format_spine1(spine, opt, vmin, vmax)
    :Inputs:
        *spine*: :clas:`matplotlib.spines.Spine`
            A single spine (left, right, top, or bottom)
        *opt*: ``None`` | ``True`` | ``False`` | ``"clipped"``
            Option for this spine
        *vmin*: :class:`float`
            If using clipped spines, minimum value for spine
        *vmax*: :class:`float`
            If using clipped spines, maximum value for spine
    :Versions:
        * 2019-03-08 ``@ddalle``: First version
    """
    # Process it
    if opt is None:
        # Leave as is
        pass
    elif opt is True:
        # Turn on
        spine.set_visible(True)
    elif opt is False:
        # Turn off
        spine.set_visible(False)
    elif typeutils.isstr(opt):
        # Check value
        if opt == "on":
            # Same as ``True``
            spine.set_visible(True)
        elif opt == "off":
            # Same as ``False``
            spine.set_visible(False)
        elif opt in ["clip", "clipped", "truncate", "truncated"]:
            # Set limits
            spine.set_bounds(vmin, vmax)
        else:
            raise ValueError("Could not process spine option '%s'" % opt)
    else:
        raise TypeError("Could not process spine option " +
                        ("of type '%s'" % opt.__class__))


# Spine formatting
def format_spines(ax, **kw):
    r"""Format Matplotlib axes spines and ticks

    :Call:
        >>> h = format_spines(ax, **kw)
    :Inputs:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Axes handle
    :Effects:
        *ax*: :class:`matplotlib.axes._subplots.AxesSubplot`
            Grid lines added to axes
    :Versions:
        * 2019-03-07 ``@jmeeroff``: First version
        * 2019-12-23 ``@ddalle``: From :mod:`tnakit.plotutils`
    """
   # --- Setup ---
    # Make sure pyplot loaded
    import_pyplot()
    # Get spine handles
    spineL = ax.spines["left"]
    spineR = ax.spines["right"]
    spineT = ax.spines["top"]
    spineB = ax.spines["bottom"]
    # Set default flags to "clipped" if certain other options are present
    # In particular, if manual bounds are specified, set the default spine
    # option to "clipped" unless otherwise specified
    for d in ["X", "Left", "Right", "Y", "Top", "Bottom"]:
        # Spine flag
        k = d + "Spine"
        # Key for min and max spine values
        kmin = k + "Min"
        kmax = k + "Max"
        # Check
        if kmin in kw:
            kw.setdefault(k, "clipped")
        elif kmax in kw:
            kw.setdefault(k, "clipped")
   # --- Data/Spine Bounds ---
    # Get existing data limits
    xmin, xmax = get_xlim(ax, pad=0.0)
    ymin, ymax = get_ylim(ax, pad=0.0)
    # Process manual limits for min and max spines
    xa = kw.get("XSpineMin", xmin)
    xb = kw.get("XSpineMax", xmax)
    ya = kw.get("YSpineMin", ymin)
    yb = kw.get("YSpineMax", ymax)
    # Process manual limits for individual spines
    yaL = kw.get("LeftSpineMin", ya)
    ybL = kw.get("LeftSpineMax", yb)
    yaR = kw.get("RightSpineMin", ya)
    ybR = kw.get("RightSpineMax", yb)
    xaB = kw.get("BottomSpineMin", xa)
    xbB = kw.get("BottomSpineMax", xb)
    xaT = kw.get("TopSpineMin", xa)
    xbT = kw.get("TopSpineMax", xb)
   # --- Overall Spine Options ---
    # Option to turn off all spines
    qs = kw.get("Spines", None)
    # Only valid options are ``None`` and ``False``
    if qs is not False: qs = None
    # Spine pairs options
    qX = kw.get("XSpine", qs)
    qY = kw.get("YSpine", qs)
    # Left spine options
    qL = kw.get("LeftSpine",   qY)
    qR = kw.get("RightSpine",  qY)
    qT = kw.get("TopSpine",    qX)
    qB = kw.get("BottomSpine", qX)
   # --- Spine On/Off Extents ---
    # Process these options
    format_spine1(spineL, qL, yaL, ybL)
    format_spine1(spineR, qR, yaR, ybR)
    format_spine1(spineT, qT, xaT, xbT)
    format_spine1(spineB, qB, xaB, xbB)
   # --- Spine Formatting ---
    # Paired options
    spopts = kw.get("SpineOptions", {})
    xsopts = kw.get("XSpineOptions", {})
    ysopts = kw.get("YSpineOptions", {})
    # Individual spines
    lsopts = kw.get("LeftSpineOptions", {})
    rsopts = kw.get("RightSpineOptions", {})
    bsopts = kw.get("BottomSpineOptions", {})
    tsopts = kw.get("TopSpineOptions", {})
    # Combine settings
    xsopts = dict(spopts, **xsopts)
    ysopts = dict(spopts, **ysopts)
    lsopts = dict(ysopts, **lsopts)
    rsopts = dict(ysopts, **rsopts)
    bsopts = dict(xsopts, **bsopts)
    tsopts = dict(xsopts, **tsopts)
    # Apply spine options
    spineL.set(**lsopts)
    spineR.set(**rsopts)
    spineB.set(**bsopts)
    spineT.set(**tsopts)
   # --- Tick Settings ---
    # Option to turn off all ticks
    qt = kw.get("Ticks", None)
    # Only valid options are ``None`` and ``False``
    if qt is not False: qt = None
    # Options for ticks on each axis
    qtL = kw.get("LeftSpineTicks",   qt and qL)
    qtR = kw.get("RightSpineTicks",  qt and qR)
    qtB = kw.get("BottomSpineTicks", qt and qB)
    qtT = kw.get("TopSpineTicks",    qt and qT)
    # Turn on/off
    if qtL is not None:
        ax.tick_params(left=qtL)
    if qtR is not None:
        ax.tick_params(right=qtR)
    if qtB is not None:
        ax.tick_params(bottom=qtB)
    if qtT is not None:
        ax.tick_params(top=qtT)
   # --- Tick label settings ---
    # Option to turn off all tick labels
    qtl = kw.pop("TickLabels", None)
    # Only valid options are ``None`` and ``False``
    if qtl is not False: qtl = None
    # Options for labels on each spine
    qtlL = kw.pop("LeftTickLabels",   qtl)
    qtlR = kw.pop("RightTickLabels",  qtl)
    qtlB = kw.pop("BottomTickLabels", qtl)
    qtlT = kw.pop("TopTickLabels",    qtl)
    # Turn on/off labels
    if qtlL is not None:
        ax.tick_params(labelleft=qtlL)
    if qtlR is not None:
        ax.tick_params(labelright=qtlR)
    if qtlB is not None:
        ax.tick_params(labelbottom=qtlB)
    if qtlT is not None:
        ax.tick_params(labeltop=qtlT)
   # --- Tick Formatting ---
    # Directions
    tkdir = kw.pop("TickDirection", "out")
    xtdir = kw.pop("XTickDirection", tkdir)
    ytdir = kw.pop("YTickDirection", tkdir)
    # Apply tick directions (can be overridden below)
    ax.tick_params(axis="x", direction=xtdir)
    ax.tick_params(axis="y", direction=ytdir)
    # Universal and paired options
    tkopts = kw.pop("TickOptions", {})
    xtopts = kw.pop("XTickOptions", {})
    ytopts = kw.pop("YTickOptions", {})
    # Inherit options from spines
    tkopts = dict(spopts, **tkopts)
    xtopts = dict(xsopts, **xtopts)
    ytopts = dict(ysopts, **ytopts)
    # Apply
    ax.tick_params(axis="both", **tkopts)
    ax.tick_params(axis="x",    **xtopts)
    ax.tick_params(axis="y",    **ytopts)
   # --- Output ---
    # Return all spine handles
    return ax.spines


# Convert min/max to error bar widths
def minmax_to_errorbar(yv, ymin, ymax):
    r"""Convert min/max values to error bar below/above widths

    :Call:
        >>> yerr = minmax_to_errorbar(yv, ymin, ymax)
    :Inputs:
        *yv*: :class:`np.ndarray` shape=(*N*,)
            Nominal dependent axis values
        *ymin*: :class:`float` | :class:`np.ndarray` shape=(*N*,)
            Minimum values of region plot
        *ymax*: :class:`float` | :class:`np.ndarray` shape=(*N*,)
            Maximum values of region plot
    :Outputs:
        *yerr*: :class:`np.ndarray` shape=(2,*N*)
            Array of lower, upper error bar widths
    :Versions:
        * 2019-03-06 ``@ddalle/@jmeeroff``: First version
    """
    # Widths of *ymax* above *yv*
    yu = ymax - np.asarray(yv)
    # Widths of *ymin* below *yv*
    yl = np.asarray(yv) - ymin
    # Separate error bars
    yerr = np.array([yl, yu])
    # Output
    return yerr

# Convert min/max to error bar widths
def errorbar_to_minmax(yv, yerr):
    r"""Convert min/max values to error bar below/above widths

    :Call:
        >>> ymin, ymax = minmax_to_errorbar(yv, yerr)
    :Inputs:
        *yv*: :class:`np.ndarray` shape=(*N*,)
            Nominal dependent axis values
        *yerr*: :class:`float` | :class:`np.ndarray` shape=(2,*N*) | (*N*,)
            Array of lower, upper error bar widths
    :Outputs:
        *ymin*: :class:`np.ndarray` shape=(*N*,)
            Minimum values of region plot
        *ymax*: :class:`np.ndarray` shape=(*N*,)
            Maximum values of region plot
    :Versions:
        * 2019-03-06 ``@ddalle/@jmeeroff``: First version
    """
    # Ensure arrays
    yv = np.asarray(yv)
    yerr = np.asarray(yerr)
    # Length of *yv*
    N = yv.size
    # Check number of dimensions of *yerr*
    if yerr.ndim == 0:
        # Scalar: simple arithmetic
        ymax = yv + yerr
        ymin = yv - yerr
    elif yerr.ndim == 1:
        # Single array: check size
        if yerr.size != N:
            raise ValueError(
                "Error bar width vector does not match size of main data")
        # Simple arithmetic
        ymax = yv + yerr
        ymin = yv - yerr
    elif yerr.ndim == 2:
        # 2D array: separate below/above widths
        if yerr.shape[0] != 2:
            raise ValueError(
                ("2D error bar width must have shape (2,N), ") +
                ("got %s" % repr(yerr.shape)))
        elif yerr.shape[1] != N:
            raise ValueError(
                "Error bar width vector does not match size of main data")
        # Separate above/below deltas
        ymax = yv + yerr[1]
        ymin = yv - yerr[0]
    else:
        # 3D or more array
        raise ValueError(
            "Cannot convert %i-D array to min/max values" % yerr.ndim)
    # Output
    return ymin, ymax


# Function to automatically get inclusive data limits.
def get_ylim(ax, pad=0.05):
    r"""Calculate appropriate *y*-limits to include all lines in a plot

    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` and
    :class:`matplotlib.collections.PolyCollection` are checked.

    :Call:
        >>> ymin, ymax = get_ylim(ax, pad=0.05)
    :Inputs:
        *ax*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *pad*: :class:`float`
            Extra padding to min and max values to plot.
    :Outputs:
        *ymin*: :class:`float`
            Minimum *y* coordinate including padding
        *ymax*: :class:`float`
            Maximum *y* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
        * 2019-03-07 ``@ddalle``: Added ``"LineCollection"``
    """
    # Initialize limits
    ymin = np.inf
    ymax = -np.inf
    # Loop through all children of the input axes.
    for h in ax.get_children():
        # Get the type.
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Get the y data for this line
            ydata = h.get_ydata()
            # Check the min and max data
            if len(ydata) > 0:
                ymin = min(ymin, min(h.get_ydata()))
                ymax = max(ymax, max(h.get_ydata()))
        elif t in ['PathCollection', 'PolyCollection', 'LineCollection']:
            # Loop through paths
            for P in h.get_paths():
                # Get the coordinates
                ymin = min(ymin, min(P.vertices[:, 1]))
                ymax = max(ymax, max(P.vertices[:, 1]))
        elif t in ["Rectangle"]:
            # Skip if invisible
            if h.axes is None:
                continue
            # Get bounding box
            bbox = h.get_bbox().extents
            # Combine limits
            ymin = min(ymin, bbox[1])
            ymax = max(ymax, bbox[3])
        elif t in ["AxesImage"]:
            # Get bounds
            bbox = h.get_extent()
            # Update limits
            xmin = min(xmin, min(bbox[2], bbox[3]))
            xmax = max(xmax, max(bbox[2], bbox[3]))
    # Check for identical values
    if ymax - ymin <= 0.1*pad:
        # Expand by manual amount
        ymax += pad*abs(ymax)
        ymin -= pad*abs(ymin)
    # Add padding
    yminv = (1+pad)*ymin - pad*ymax
    ymaxv = (1+pad)*ymax - pad*ymin
    # Output
    return yminv, ymaxv


# Function to automatically get inclusive data limits.
def get_xlim(ax, pad=0.05):
    r"""Calculate appropriate *x*-limits to include all lines in a plot

    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` are
    checked.

    :Call:
        >>> xmin, xmax = get_xlim(ax, pad=0.05)
    :Inputs:
        *ax*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *pad*: :class:`float`
            Extra padding to min and max values to plot.
    :Outputs:
        *xmin*: :class:`float`
            Minimum *x* coordinate including padding
        *xmax*: :class:`float`
            Maximum *x* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
        * 2019-03-07 ``@ddalle``: Added ``"LineCollection"``
    """
    # Initialize limits
    xmin = np.inf
    xmax = -np.inf
    # Loop through all children of the input axes.
    for h in ax.get_children()[:-1]:
        # Get the type's name string
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Get data
            xdata = h.get_xdata()
            # Check the min and max data
            if len(xdata) > 0:
                xmin = min(xmin, np.min(h.get_xdata()))
                xmax = max(xmax, np.max(h.get_xdata()))
        elif t in ['PathCollection', 'PolyCollection', 'LineCollection']:
            # Loop through paths
            for P in h.get_paths():
                # Get the coordinates
                xmin = min(xmin, np.min(P.vertices[:, 0]))
                xmax = max(xmax, np.max(P.vertices[:, 0]))
        elif t in ["Rectangle"]:
            # Skip if invisible
            if h.axes is None: continue
            # Get bounding box
            bbox = h.get_bbox().extents
            # Combine limits
            xmin = min(xmin, bbox[0])
            xmax = max(xmax, bbox[2])
        elif t in ["AxesImage"]:
            # Get bounds
            bbox = h.get_extent()
            # Update limits
            xmin = min(xmin, min(bbox[0], bbox[1]))
            xmax = max(xmax, max(bbox[0], bbox[1]))
    # Check for identical values
    if xmax - xmin <= 0.1*pad:
        # Expand by manual amount
        xmax += pad*abs(xmax)
        xmin -= pad*abs(xmin)
    # Add padding
    xminv = (1+pad)*xmin - pad*xmax
    xmaxv = (1+pad)*xmax - pad*xmin
    # Output
    return xminv, xmaxv


# Output class
class MPLHandle(object):
    r"""Container for handles from :mod:`matplotlib.pyplot`

    :Versions:
        * 2019-12-20 ``@ddalle``: First version
    """
    # Initialization method
    def __init__(self, **kw):
        r"""Initialization method

        :Call:
            >>> h = MPLHandle(**kw)
        :Attributes:
            *h.fig*: {``None``} | :class:`matplotlib.figure.Figure`
                Figure handle
            *h.ax*: {``None``} | :class:`matplotlib.axes.Axes`
                Axes handle
            *h.lines*: {``[]``} | :class:`list`\ [:class:`Line2D`]
                List of line handles
        :Versions:
            * 2019-12-20 ``@ddalle``: First version
        """
        # Initialize simple handles
        self.fig = kw.get("fig")
        self.ax = kw.get("ax")

        # Initialize handles
        self.lines = kw.get("lines", [])

    # Combine two handles
    def add(self, h1):
        r"""Combine two plot handle objects

        Attributes of *h1* will override those of *h* except where the
        attribute is a list.  For example, *h1.lines* will be added to
        *h.lines* to get handles to lines from both instances.

        :Call:
            >>> h.add(h1)
        :Inputs:
            *h*: :class:`MPLHandle`
                Parent handle
            *h1*: :class:`MPLHandle`
                Second handle for collecting all objects
        :Versions:
            * 2019-12-26 ``@ddalle``: First version
        """
        # Check inputs
        if not isinstance(h1, MPLHandle):
            raise TypeError("Second handle must be MPLHandle object")
        # Loop through data attributes
        for (k, v) in h1.__dict__.items():
            # Check for list (combine)
            if isinstance(v, list):
                # Get attribute from parent
                v0 = self.__dict__.get(k)
                # Check if both are lists
                if isinstance(v0, list):
                    # Combine two lists
                    self.__dict__[k] = v0 + v
                else:
                    # Replace non-list value
                    self.__dict__[k] = v
            elif v.__class__.__module__.startswith("matplotlib"):
                # Some other plot handle; replace
                self.__dict__[k] = v


# Function to get 


# Standard type strings
_rst_boolf = """```True`` | {``False``}"""
_rst_booln = """{``None``} | ``True`` | ``False``"""
_rst_boolt = """{``True``} | ``False``"""
_rst_dict = """{``None``} | :class:`dict`"""
_rst_float = """{``None``} | :class:`float`"""
_rst_floatpos = """{``None``} | :class:`float` > 0.0"""
_rst_int = """{``None``} | :class:`int`"""
_rst_intpos = """{``None``} | :class:`int` > 0"""
_rst_num = """{``None``} | :class:`int` | :class:`float`"""
_rst_numpos = """{``None``} | :class:`int` > 0 | :class:`float` > 0.0"""
_rst_str = """{``None``} | :class:`str`"""
_rst_strnum = """{``None``} | :class:`str` | :class:`int` | :class:`float`"""



# Options interface
class MPLOpts(kwutils.KwargHandler):
  # ====================
  # Class Attributes
  # ====================
  # <
   # --- Global Options ---
    # Lists of options
    _optlist = {
        "AdjustBottom",
        "AdjustLeft",
        "AdjustRight",
        "AdjustTop",
        "BottomSpine",
        "BottomSpineMax",
        "BottomSpineMin",
        "BottomSpineOptions",
        "BottomSpineTicks",
        "BottomTickLabels",
        "Density",
        "ErrorBarOptions",
        "ErrorBarMarker",
        "ErrorOptions",
        "ErrorPlotType",
        "FigDPI",
        "FigHeight",
        "FigNumber",
        "FigOptions",
        "FigWidth",
        "FillBetweenOptions",
        "FontOptions",
        "FontName",
        "FontSize",
        "FontStretch",
        "FontStyle",
        "FontVariant",
        "FontWeight",
        "Grid",
        "GridColor",
        "GridOptions",
        "GridStyle",
        "ImageExtent",
        "ImageXCenter",
        "ImageXMax",
        "ImageXMin",
        "ImageYCenter",
        "ImageYMax",
        "ImageYMin",
        "Index",
        "KeepAspect",
        "Label",
        "LeftSpine",
        "LeftSpineMax",
        "LeftSpineMin",
        "LeftSpineOptions",
        "LeftSpineTicks",
        "LeftTickLabels",
        "Legend",
        "LegendFontName",
        "LegendFontOptions",
        "LegendFontSize",
        "LegendFontStretch",
        "LegendFontStyle",
        "LegendFontVariant",
        "LegendFontWeight",
        "LegendOptions",
        "MajorGrid",
        "MarginBottom",
        "MarginHSpace",
        "MarginLeft",
        "MarginRight",
        "MarginTop",
        "MarginVSpace",
        "MinMaxOptions",
        "MinMaxPlotType",
        "MinorGrid",
        "MinorGridOptions",
        "Pad",
        "PlotColor",
        "PlotLineStyle",
        "PlotLineWidth",
        "PlotOptions",
        "RightSpine",
        "RightSpineMax",
        "RightSpineMin",
        "RightSpineOptions",
        "RightSpineTicks",
        "RightTickLabels",
        "Rotate",
        "ShowError",
        "ShowLegend",
        "ShowLine",
        "ShowMinMax",
        "ShowUncertainty",
        "SpineOptions",
        "Spines",
        "Subplot",
        "SubplotCols",
        "SubplotList",
        "SubplotRows",
        "SubplotRubber",
        "TickDirection",
        "TickFontSize",
        "TickLabels",
        "TickOptions",
        "TickRotation",
        "TickSize",
        "Ticks",
        "TopSpine",
        "TopSpineMax",
        "TopSpineMin",
        "TopSpineOptions",
        "TopSpineTicks",
        "TopTickLabels",
        "UncertaintyPlotType",
        "UncertaintyOptions",
        "XLabel",
        "XLim",
        "XPad",
        "XSpine",
        "XSpineMax",
        "XSpineMin",
        "XSpineOptions",
        "XTickDirection",
        "XTickFontSize",
        "XTickLabels",
        "XTickOptions",
        "XTickRotation",
        "XTickSize",
        "XTicks",
        "YLabel",
        "YLim",
        "YPad",
        "YSpine",
        "YSpineMax",
        "YSpineMin",
        "YSpineOptions",
        "YTickDirection",
        "YTickFontSize",
        "YTickLabels",
        "YTickOptions",
        "YTickRotation",
        "YTickSize",
        "YTicks",
        "ax",
        "fig",
        "xerr",
        "yerr",
        "ymin",
        "ymax"
    }

    # Options for which a singleton is a list
    _optlist_list = {
        "dashes",
        "XLim",
        "YLim",
        "XTickLabels",
        "XTicks",
        "YTickLabels",
        "YTicks"
    }

    # Alternate names
    _optmap = {
        "Axes": "ax",
        "BottomTicks": "BottomSpineTicks",
        "ErrorBarOpts": "ErrorBarOptions",
        "Figure": "fig",
        "FillBetweenOpts": "FillBetweenOptions",
        "Font": "FontName",
        "FontFamily": "FontName",
        "GridOpts": "GridOptions",
        "LeftTicks": "LeftSpineTicks",
        "MajorGridOpts": "GridOptions",
        "MajorGridOptions": "GridOptions",
        "MinMaxOpts": "MinMaxOptions",
        "PlotOpts": "PlotOptions",
        "RightTicks": "RightSpineTicks",
        "ShowUQ": "ShowUncertainty",
        "TopTicks": "TopSpineTicks",
        "UQOptions": "UncertaintyOptions",
        "UQOpts": "UncertaintyOptions",
        "UncertaintyOpts": "UncertaintyOptions",
        "UQPlotType": "UncertaintyPlotType",
        "density": "Density",
        "grid": "Grid",
        "hfig": "FigHeight",
        "hspace": "MarginHSpace",
        "i": "Index",
        "label": "Label",
        "lbl": "Label",
        "nfig": "FigNumber",
        "numfig": "FigNumber",
        "rotate": "Rotate",
        "subplot": "Subplot",
        "vspace": "MarginVSpace",
        "wfig": "FigWidth",
        "xlabel": "XLabel",
        "xlim": "XLim",
        "ylabel": "YLabel",
        "ylim": "YLim",
    }

   # --- Option Sublists ---
    _optlists = {
        "axes": [
            "ax",
            "AxesOptions"
        ],
        "axadjust": [
            "MarginBottom",
            "MarginLeft",
            "MarginRight",
            "MarginTop",
            "AdjustBottom",
            "AdjustLeft",
            "AdjustRight",
            "AdjustTop",
            "KeepAspect",
            "Subplot",
            "SubplotCols",
            "SubplotRows"
        ],
        "axadjust_col": [
            "MarginBottom",
            "MarginLeft",
            "MarginRight",
            "MarginTop",
            "MarginVSpace",
            "AdjustBottom",
            "AdjustLeft",
            "AdjustRight",
            "AdjustTop",
            "SubplotList",
            "SubplotRubber"
        ],
        "axadjust_row": [
            "MarginBottom",
            "MarginLeft",
            "MarginRight",
            "MarginTop",
            "MarginHSpace",
            "AdjustBottom",
            "AdjustLeft",
            "AdjustRight",
            "AdjustTop",
            "SubplotList",
            "SubplotRubber"
        ],
        "axformat": [
            "Density",
            "Index",
            "Pad",
            "Rotate",
            "XLabel",
            "XLim",
            "XLimMax",
            "XLimMin",
            "XPad",
            "YLabel",
            "YLim",
            "YLimMax",
            "YLimMin",
            "YPad"
        ],
        "fig": [
            "fig",
            "FigOptions",
            "FigNumber",
            "FigWidth",
            "FigHeight",
            "FigDPI"
        ],
        "font": [
            "FontOptions",
            "FontName",
            "FontSize",
            "FontStretch",
            "FontStyle",
            "FontVariant",
            "FontWeight"
        ],
        "grid": [
            "Grid",
            "GridOptions",
            "MinorGrid",
            "MinorGridOptions",
        ],
        "plot": [
            "Index",
            "Rotate",
            "PlotOptions",
            "PlotColor",
            "PlotLineStyle",
            "PlotLineWidth",
        ],
        "imshow": [
            "ImageXMin",
            "ImageXMax",
            "ImageXCenter",
            "ImageYMin",
            "ImageYMax",
            "ImageYCenter",
            "ImageExtent"
        ],
        "errobar": [
            "Index",
            "Rotate",
            "ErrorBarOptions",
            "ErrorBarMarker"
        ],
        "fillbetween": [
            "Index",
            "Rotate",
            "FillBetweenOptions"
        ],
        "minmax": [
            "Index",
            "Rotate",
            "MinMaxOptions",
            "MinMaxPlotType",
            "ErrorBarOptions",
            "ErrorBarMarker",
            "FillBetweenOptions"
        ],
        "error": [
            "Index",
            "Rotate",
            "ErrorOptions",
            "ErrorPlotType",
            "ErrorBarOptions",
            "ErrorBarMarker",
            "FillBetweenOptions"
        ],
        "uq": [
            "Index",
            "Rotate",
            "ErrorBarMarker",
            "ErrorBarOptions",
            "FillBetweenOptions",
            "UncertaintyPlotType",
            "UncertaintyOptions"
        ],
        "spines": [
            "Spines",
            "SpineOptions",
            "Ticks",
            "TickDirection",
            "TickFontSize",
            "TickLabels",
            "TickOptions",
            "TickRotation",
            "TickSize",
            "BottomSpine",
            "BottomSpineMax",
            "BottomSpineMin",
            "BottomSpineOptions",
            "BottomSpineTicks",
            "BottomTickLabels",
            "LeftSpine",
            "LeftSpineMax",
            "LeftSpineMin",
            "LeftSpineOptions",
            "LeftSpineTicks",
            "LeftTickLabels",
            "RightSpine",
            "RightSpineMax",
            "RightSpineMin",
            "RightSpineOptions",
            "RightSpineTicks",
            "RightTickLabels",
            "TopSpine",
            "TopSpineMax",
            "TopSpineMin",
            "TopSpineOptions",
            "TopSpineTicks",
            "TopTickLabels",
            "XSpine",
            "XSpineMax",
            "XSpineMin",
            "XSpineOptions",
            "XTicks",
            "XTickDirection",
            "XTickFontSize",
            "XTickLabels",
            "XTickOptions",
            "XTickRotation",
            "XTickSize",
            "YSpine",
            "YSpineMax",
            "YSpineMin",
            "YSpineOptions",
            "YTicks",
            "YTickDirection",
            "YTickFontSize",
            "YTickLabels",
            "YTickOptions",
            "YTickRotation",
            "YTickSize",
        ],
        "legend": [
            "Legend",
            "LegendAnchor",
            "LegendFontOptions",
            "LegendLocation",
            "LegendOptions"
        ],
        "legendfont": [
            "LegendFontName",
            "LegendFontSize",
            "LegendFontStretch",
            "LegendFontStyle",
            "LegendFontVariant",
            "LegendFontWeight"
        ],
        "subplot": [
            "AdjustBottom",
            "AdjustLeft",
            "AdjustRight",
            "AdjustTop",
            "Subplot",
            "SubplotCols",
            "SubplotRows"
        ],
    }

   # --- Types ---
    # Types
    _opttypes = {
        "AdjustBottom": float,
        "AdjustLeft": float,
        "AdjustRight": float,
        "AdjustTop": float,
        "AxesOptions": dict,
        "BottomSpine": (bool, typeutils.strlike),
        "BottomSpineMax": float,
        "BottomSpineMin": float,
        "BottomSpineOptions": dict,
        "BottomSpineTicks": bool,
        "BottomTickLabels": bool,
        "Density": bool,
        "ErrorBarMarker": typeutils.strlike,
        "ErrorBarOptions": dict,
        "ErrorOptions": dict,
        "ErrorPlotType": typeutils.strlike,
        "FigDPI": (float, int),
        "FigHeight": float,
        "FigNumber": int,
        "FigOptions": dict,
        "FigWidth": float,
        "FillBetweenOptions": dict,
        "FontName": typeutils.strlike,
        "FontOptions": dict,
        "FontSize": (int, float, typeutils.strlike),
        "FontStretch": (int, float, typeutils.strlike),
        "FontStyle": typeutils.strlike,
        "FontVariant": typeutils.strlike,
        "FontWeight": (float, int, typeutils.strlike),
        "Grid": int,
        "GridOptions": dict,
        "ImageExtent": (tuple, dict),
        "ImageXCenter": float,
        "ImageXMax": float,
        "ImageXMin": float,
        "ImageYCenter": float,
        "ImageYMax": float,
        "ImageYMin": float,
        "Index": int,
        "KeepAspect": bool,
        "Label": typeutils.strlike,
        "LeftSpine": (bool, typeutils.strlike),
        "LeftSpineMax": float,
        "LeftSpineMin": float,
        "LeftSpineOptions": dict,
        "LeftSpineTicks": bool,
        "LeftTickLabels": bool,
        "Legend": bool,
        "LegendAnchor": (tuple, list),
        "LegendFontName": typeutils.strlike,
        "LegendFontOptions": dict,
        "LegendFontSize": (int, float, typeutils.strlike),
        "LegendFontStretch": (int, float, typeutils.strlike),
        "LegendFontStyle": typeutils.strlike,
        "LegendFontVariant": typeutils.strlike,
        "LegendFontWeight": (float, int, typeutils.strlike),
        "LegendLocation": (int, typeutils.strlike),
        "LegendOptions": dict,
        "MajorGrid": bool,
        "MarginBottom": float,
        "MarginHSpace": float,
        "MarginLeft": float,
        "MarginRight": float,
        "MarginTop": float,
        "MarginVSpace": float,
        "MinorGrid": bool,
        "MinorGridOptions": dict,
        "MinMaxOptions": dict,
        "MinMaxPlotType": typeutils.strlike,
        "Pad": float,
        "PlotColor": (tuple, typeutils.strlike),
        "PlotLineStyle": typeutils.strlike,
        "PlotLineWidth": (float, int),
        "PlotOptions": dict,
        "Rotate": bool,
        "ShowError": bool,
        "ShowLine": bool,
        "ShowMinMax":bool,
        "ShowUncertainty": bool,
        "SpineOptions": dict,
        "Spines": bool,
        "SubplotCols": int,
        "SubplotList": list,
        "SubplotRows": int,
        "SubplotRubber": int,
        "RightSpine": (bool, typeutils.strlike),
        "RightSpineMax": float,
        "RightSpineMin": float,
        "RightSpineOptions": dict,
        "RightSpineTicks": bool,
        "RightTickLabels": bool,
        "TickDirection": typeutils.strlike,
        "TickFontSize": (int, float, typeutils.strlike),
        "TickLabels": bool,
        "TickOptions": dict,
        "TickRotation": (int, float),
        "TickSize": (int, float, typeutils.strlike),
        "Ticks": bool,
        "TopSpine": (bool, typeutils.strlike),
        "TopSpineMax": float,
        "TopSpineMin": float,
        "TopSpineOptions": dict,
        "TopSpineTicks": bool,
        "TopTickLabels": bool,
        "UncertaintyOptions": dict,
        "UncertaintyPlotType": typeutils.strlike,
        "XLabel": typeutils.strlike,
        "XLim": (tuple, list),
        "XLimMax": float,
        "XLimMin": float,
        "XPad": float,
        "XTickDirection": typeutils.strlike,
        "XTickFontSize": (int, float, typeutils.strlike),
        "XTickLabels": (bool, list),
        "XTickOptions": dict,
        "XTickRotation": (int, float),
        "XTickSize": (int, float, typeutils.strlike),
        "XTicks": (bool, list),
        "YLabel": typeutils.strlike,
        "YLim": (tuple, list),
        "YLimMax": float,
        "YLimMin": float,
        "YPad": float,
        "YTickDirection": typeutils.strlike,
        "YTickFontSize": (int, float, typeutils.strlike),
        "YTickLabels": (bool, list),
        "YTickOptions": dict,
        "YTickRotation": (int, float),
        "YTickSize": (int, float, typeutils.strlike),
        "YTicks": (bool, list),
        "ax": object,
        "fig": object,
        "xerr": typeutils.arraylike,
        "yerr": typeutils.arraylike,
        "ymax": typeutils.arraylike,
        "ymin": typeutils.arraylike,
    }

   # --- Cascading Options ---
    # Global options mapped to subcategory options
    _kw_submap = {
        "AxesOptions": {},
        "ErrorOptions": {},
        "FigOptions": {
            "FigNumber": "num",
            "FigDPI": "dpi",
            "FigHeight": "figheight",
            "FigWidth": "figwidth",
        },
        "ErrorBarOptions": {
            "Index": "Index",
            "Rotate": "Rotate",
            "ErrorBarMarker": "marker",
            "PlotOptions.color": "color",
        },
        "FillBetweenOptions": {
            "Index": "Index",
            "Rotate": "Rotate",
            "PlotOptions.color": "color",
        },
        "FontOptions": {
            "FontName": "family",
            "FontSize": "size",
            "FontStretch": "stretch",
            "FontStyle": "style",
            "FontVariant": "variant",
            "FontWeight": "weight",
        },
        "GridOptions": {
            "GridColor": "color",
        },
        "LegendOptions": {
            "LegendAnchor": "bbox_to_anchor",
            "LegendFontOptions": "prop",
            "LegendLocation": "loc",
            "LegendNCol": "ncol",
            "ShowLegend": "ShowLegend",
        },
        "LegendFontOptions": {
            "FontOptions.family": "family",
            "FontOptions.size": "size",
            "FontOptions.stretch": "stretch",
            "FontOptions.style": "style",
            "FontOptions.variant": "variant",
            "FontOptions.weight": "weight",
            "LegendFontName": "family",
            "LegendFontSize": "size",
            "LegendFontStretch": "stretch",
            "LegendFontStyle": "style",
            "LegendFontVariant": "variant",
            "LegendFontWeight": "weight",
        },
        "MinMaxOptions": {},
        "PlotOptions": {
            "Index": "Index",
            "Rotate": "Rotate",
            "Label": "label",
            "PlotColor": "color",
            "PlotLineWidth": "lw",
            "PlotLineStyle": "ls"
        },
       "TickOptions": {
            "TickFontSize": "labelsize",
            "TickRotation": "rotation",
            "TickSize": "size",
       },
       "XTickOptions": {
           "TickOptions.labelsize": "labelsize",
           "TickOptions.rotation": "rotation",
           "TickOptions.size": "size",
            "XTickFontSize": "labelsize",
            "XTickRotation": "rotation",
            "XTickSize": "size",
       },
       "YTickOptions": {
           "TickOptions.labelsize": "labelsize",
           "TickOptions.rotation": "rotation",
           "TickOptions.size": "size",
            "YTickFontSize": "labelsize",
            "YTickRotation": "rotation",
            "YTickSize": "size",
        },
        "UncertaintyOptions": {},
    }

   # --- Conflicting Options ---
    # Aliases to merge for subcategory options
    _kw_subalias = {
        "PlotOptions": {
            "linewidth": "lw",
            "linestyle": "ls",
            "c": "color",
        },
        "ErrorBarOptions": {
            "linewidth": "lw",
            "linestyle": "ls",
            "c": "color",
            "mec": "markeredgecolor",
            "mew": "mergeredgewidth",
            "mfc": "markerfacecolor",
            "ms": "markersize",
        },
        "FillBetweenOptions": {
            "linewidth": "lw",
            "linestyle": "ls",
            "c": "color",
        },
        "GridOptions": {
            "linewidth": "lw",
            "linestyle": "ls",
            "c": "color",
        },
    }

   # --- Documentation Data ---
    # Type strings
    _rst_types = {
        "AdjustBottom": _rst_float,
        "AdjustLeft": _rst_float,
        "AdjustRight": _rst_float,
        "AdjustTop": _rst_float,
        "AxesOptions": _rst_dict,
        "BottomSpine": """{``None``} | ``True`` | ``False`` | ``"clipped"``""",
        "BottomSpineMax": _rst_float,
        "BottomSpineMin": _rst_float,
        "BottomSpineOptions": _rst_dict,
        "BottomSpineTicks": _rst_booln,
        "BottomTickLabels": _rst_booln,
        "Density": _rst_boolt,
        "ErrorBarMarker": _rst_str,
        "ErrorBarOptions": _rst_dict,
        "ErrorOptions": _rst_dict,
        "ErrorPlotType": """``"FillBetween"`` | {``"ErrorBar"``}""",
        "FigDPI": _rst_numpos,
        "FigHeight": _rst_floatpos,
        "FigNumber": _rst_intpos,
        "FigOptions": _rst_dict,
        "FigWidth": _rst_floatpos,
        "FillBetweenOptions": _rst_dict,
        "FontName": _rst_str,
        "FontOptions": _rst_dict,
        "FontSize": _rst_strnum,
        "FontStretch": _rst_strnum,
        "FontStyle": ("""{``None``} | ``"normal"`` | """ +
            """``"italic"`` | ``"oblique"``"""),
        "FontVariant": """{``None``} | ``"normal"`` | ``"small-caps"``""",
        "FontWeight": _rst_strnum,
        "Grid": _rst_boolt,
        "GridColor": """{``None``} | :class:`str` | :class:`tuple`""",
        "GridOptions": _rst_dict,
        "ImageExtent": """{``None``} | :class:`tuple` | :class:`list`""",
        "ImageXCenter": _rst_float,
        "ImageXMax": _rst_float,
        "ImageXMin": """{``0.0``} | :class:`float`""",
        "ImageYCenter": """{``0.0``} | :class:`float`""",
        "ImageYMax": _rst_float,
        "ImageYMin": _rst_float,
        "Index": """{``0``} | :class:`int` >=0""",
        "KeepAspect": _rst_booln,
        "Label": _rst_str,
        "LeftSpine": """{``None``} | ``True`` | ``False`` | ``"clipped"``""",
        "LeftSpineMax": _rst_float,
        "LeftSpineMin": _rst_float,
        "LeftSpineOptions": _rst_dict,
        "LeftSpineTicks": _rst_booln,
        "LeftTickLabels": _rst_booln,
        "Legend": _rst_booln,
        "LegendAnchor": r"""{``None``} | :class:`tuple`\ (*x*, *y*)""",
        "LegendFontName": _rst_str,
        "LegendFontOptions": _rst_dict,
        "LegendFontSize": _rst_strnum,
        "LegendFontStretch": _rst_strnum,
        "LegendFontStyle": ("""{``None``} | ``"normal"`` | """ +
            """``"italic"`` | ``"oblique"``"""),
        "LegendFontVariant": '{``None``} | ``"normal"`` | ``"small-caps"``',
        "LegendFontWeight": _rst_strnum,
        "LegendLocation": """{``None``} | :class:`str` | :class:`int`""",
        "LegendOptions": _rst_dict,
        "MajorGrid": _rst_boolt,
        "MarginBottom": _rst_float,
        "MarginHSpace": _rst_float,
        "MarginLeft": _rst_float,
        "MarginRight": _rst_float,
        "MarginTop": _rst_float,
        "MarginVSpace": _rst_float,
        "MinMaxPlotType": """{``"FillBetween"``} | ``"ErrorBar"``""",
        "MinMaxOptions": _rst_dict,
        "MinorGrid": _rst_boolf,
        "MinorGridOptions": _rst_dict,
        "Pad": _rst_float,
        "PlotColor": """{``None``} | :class:`str` | :class:`tuple`""",
        "PlotLineStyle": ('``":"`` | ``"-"`` | ``"none"`` | ' +
            '``"-."`` | ``"--"``'),
        "PlotLineWidth": _rst_numpos,
        "PlotOptions": _rst_dict,
        "RightSpine": """{``None``} | ``True`` | ``False`` | ``"clipped"``""",
        "RightSpineMax": _rst_float,
        "RightSpineMin": _rst_float,
        "RightSpineOptions": _rst_dict,
        "RightSpineTicks": _rst_booln,
        "RightTickLabels": _rst_booln,
        "Rotate": _rst_boolt,
        "ShowError": _rst_booln,
        "ShowMinMax": _rst_booln,
        "ShowUncertainty": _rst_booln,
        "Subplot": """{``None``} | :class:`Axes` | :class:`int`""",
        "SubplotCols": _rst_intpos,
        "SubplotList": r"""{``None``} | :class:`list`\ [:class:`int`]""",
        "SubplotRows": _rst_intpos,
        "SubplotRubber": _rst_int,
        "TopSpine": """{``None``} | ``True`` | ``False`` | ``"clipped"``""",
        "TopSpineMax": _rst_float,
        "TopSpineMin": _rst_float,
        "TopSpineOptions": _rst_dict,
        "TopSpineTicks": _rst_booln,
        "TopTickLabels": _rst_booln,
        "UncertaintyOptions": _rst_dict,
        "UncertaintyPlotType": """{``"FillBetween"``} | ``"ErrorBar"``""",
        "XLabel": _rst_str,
        "XLim": r"""{``None``} | (:class:`float`, :class:`float`)""",
        "XLimMax": _rst_float,
        "XLimMin": _rst_float,
        "XPad": """{*Pad*} | :class:`float`""",
        "YLabel": _rst_str,
        "YLim": r"""{``None``} | (:class:`float`, :class:`float`)""",
        "YLimMax": _rst_float,
        "YLimMin": _rst_float,
        "YPad": """{*Pad*} | :class:`float`""",
        "ax": """{``None``} | :class:`matplotlib.axes._subplots.Axes`""",
        "fig": """{``None``} | :class:`matplotlib.figure.Figure`""",
    }
    # Option descriptions
    _rst_descriptions = {
        "AdjustBottom": """Figure-scale coordinates of bottom of axes""",
        "AdjustLeft": """Figure-scale coordinates of left side of axes""",
        "AdjustRight": """Figure-scale coordinates of right side of axes""",
        "AdjustTop": """Figure-scale coordinates of top of axes""",
        "AxesOptions": """Options to :class:`AxesSubplot`""",
        "BottomSpine": "Turn on/off bottom plot spine",
        "BottomSpineMax": "Maximum *x* coord for bottom plot spine",
        "BottomSpineMin": "Minimum *x* coord for bottom plot spine",
        "BottomSpineTicks": "Turn on/off labels on bottom spine",
        "BottomSpineOptions": "Additional options for bottom spine",
        "BottomTickLabels": "Turn on/off tick labels on bottom spine",
        "Density": """Option to scale histogram plots""",
        "ErrorBarMarker": """Marker for :func:`errorbar` plots""",
        "ErrorBarOptions": """Options for :func:`errorbar` plots""",
        "ErrorOptions": """Options for error plots""",
        "ErrorPlotType": """Plot type for "error" plots""",
        "FigDPI": "Figure resolution in dots per inch",
        "FigHeight": "Figure height [inches]",
        "FigNumber": "Figure number",
        "FigOptions": """Options to :class:`matplotlib.figure.Figure`""",
        "FigWidth": "Figure width [inches]",
        "FillBetweenOptions": """Options for :func:`fill_between` plots""",
        "FontName": """Font name (categories like ``sans-serif`` allowed)""",
        "FontOptions": """Options to :class:`FontProperties`""",
        "FontSize": """Font size (options like ``"small"`` allowed)""",
        "FontStretch": ("""Stretch, numeric in range 0-1000 or """ +
            """string such as ``"condensed"``, ``"extra-condensed"``, """ +
            """``"semi-expanded"``"""),
        "FontStyle": """Font style/slant""",
        "FontVariant": """Font capitalization variant""",
        "FontWeight": ("""Numeric font weight 0-1000 or ``"normal"``, """ +
            """``"bold"``, etc."""),
        "Grid": """Option to turn on/off axes grid""",
        "GridColor": """Color passed to *GridOptions*""",
        "GridOptions": """Plot options for major grid""",
        "ImageXMin": "Coordinate for left edge of image",
        "ImageXMax": "Coordinate for right edge of image",
        "ImageXCenter": "Horizontal center coord if *x* edges not specified",
        "ImageYMin": "Coordinate for bottom edge of image",
        "ImageYMax": "Coordinate for top edge of image",
        "ImageYCenter": "Vertical center coord if *y* edges not specified",
        "ImageExtent": ("Spec for *ImageXMin*, *ImageXMax*, " +
            "*ImageYMin*, *ImageYMax*"),
        "Index": """Index to select specific option from lists""",
        "KeepAspect": ("""Keep aspect ratio; default is ``True`` unless""" +
            """``ax.get_aspect()`` is ``"auto"``"""),
        "Label": """Label passed to :func:`plt.legend`""",
        "LeftSpine": "Turn on/off left plot spine",
        "LeftSpineMax": "Maximum *y* coord for left plot spine",
        "LeftSpineMin": "Minimum *y* coord for left plot spine",
        "LeftSpineTicks": "Turn on/off labels on left spine",
        "LeftSpineOptions": "Additional options for left spine",
        "LeftTickLabels": "Turn on/off tick labels on left spine",
        "Legend": "Turn on/off (auto) legend",
        "LegendAnchor": "Location passed to *bbox_to_anchor*",
        "LegendFontName": "Font name (categories like ``sans-serif`` allowed)",
        "LegendFontOptions": "Options to :class:`FontProperties`",
        "LegendFontSize": 'Font size (options like ``"small"`` allowed)',
        "LegendFontStretch": ("""Stretch, numeric in range 0-1000 or """ +
            """string such as ``"condensed"``, ``"extra-condensed"``, """ +
            """``"semi-expanded"``"""),
        "LegendFontStyle": """Font style/slant""",
        "LegendFontVariant": """Font capitalization variant""",
        "LegendFontWeight": ("""Numeric font weight 0-1000 or """ +
            """``"normal"``, ``"bold"``, etc."""),
        "LegendLocation": """Numeric location or abbreviation""",
        "LegendOptions": """Options to :func:`plt.legend`""",
        "MajorGrid": """Option to turn on/off grid at main ticks""",
        "MarginBottom": "Figure fraction from bottom edge to bottom label",
        "MarginHSpace": "Figure fraction for horizontal space between axes",
        "MarginLeft": "Figure fraction from left edge to left-most label",
        "MarginRight": "Figure fraction from right edge to right-most label",
        "MarginTop": "Figure fraction from top edge to top-most label",
        "MarginVSpace": "Figure fraction for vertical space between axes",
        "MinMaxOptions": "Options for error-bar or fill-between min/max plot",
        "MinMaxPlotType": """Plot type for min/max plot""",
        "MinorGrid": """Turn on/off grid at minor ticks""",
        "MinorGridOptions": """Plot options for minor grid""",
        "Pad": "Padding to add to both axes, *ax.set_xlim* and *ax.set_ylim*",
        "PlotColor": """Color option to :func:`plt.plot` for primary curve""",
        "PlotOptions": """Options to :func:`plt.plot` for primary curve""",
        "PlotLineStyle": """Line style for primary :func:`plt.plot`""",
        "PlotLineWidth": """Line width for primary :func:`plt.plot`""",
        "RightSpine": "Turn on/off right plot spine",
        "RightSpineMax": "Maximum *y* coord for right plot spine",
        "RightSpineMin": "Minimum *y* coord for right plot spine",
        "RightSpineTicks": "Turn on/off labels on right spine",
        "RightSpineOptions": "Additional options for right spine",
        "RightTickLabels": "Turn on/off tick labels on right spine",
        "Rotate": """Option to flip *x* and *y* axes""",
        "ShowError": """Show "error" plot using *xerr*""",
        "ShowMinMax": """Plot *ymin* and *ymax* at each point""",
        "ShowUncertainty": """Plot uncertainty bounds""",
        "Subplot": "Subplot index (1-based)",
        "SubplotCols": "Expected number of subplot columns",
        "SubplotList": "List of subplots to put in row/column",
        "SubplotRows": "Expected number of subplot rows",
        "SubplotRubber": "Index of subplot to expand",
        "TopSpine": "Turn on/off top plot spine",
        "TopSpineMax": "Maximum *x* coord for top plot spine",
        "TopSpineMin": "Minimum *x* coord for top plot spine",
        "TopSpineTicks": "Turn on/off labels on top spine",
        "TopSpineOptions": "Additional options for top spine",
        "TopTickLabels": "Turn on/off tick labels on top spine",
        "UncertaintyOptions": """Options for UQ plots""",
        "UncertaintyPlotType": """Plot type for UQ plots""",
        "XLabel": """Label to put on *x* axis""",
        "XLim": """Limits for min and max value of *x*-axis""",
        "XLimMax": """Min value for *x*-axis in plot""",
        "XLimMin": """Max value for *x*-axis in plot""",
        "XPad": """Extra padding to add to *x* axis limits""",
        "YLabel": """Label to put on *y* axis""",
        "YLim": """Limits for min and max value of *y*-axis""",
        "YLimMax": """Min value for *y*-axis in plot""",
        "YLimMin": """Max value for *y*-axis in plot""",
        "YPad": """Extra padding to add to *y* axis limits""",
        "ax": """Handle to existing axes""",
        "fig": """Handle to existing figure""",
    }
    
   # --- RC ---
    # Default values
    _rc = {
        "ShowLine": True,
        "ShowError": False,
        "Index": 0,
        "Rotate": False,
        "AxesOptions": {},
        "ErrorBarOptions": {},
        "ErrorOptions": {},
        "FigOptions": {
            "figwidth": 5.5,
            "figheight": 4.4,
        },
        "FillBetweenOptions": {
            "alpha": 0.2,
            "lw": 0,
            "zorder": 4,
        },
        "FontOptions": {
            "family": "DejaVu Sans",
        },
        "LegendFontOptions": {},
        "LegendOptions": {
            "loc": "upper center",
            "labelspacing": 0.5,
            "framealpha": 1.0,
        },
        "MinMaxOptions": {},
        "MinMaxPlotType": "FillBetween",
        "PlotOptions": {
            "color": ["b", "k", "darkorange", "g"],
            "ls": "-",
            "zorder": 8,
        },
        "TickOptions": {},
        "XTickOptions": {},
        "YTickOptions": {},
    }

    # Options for sections
    _rc_sections = {
        "figure": {},
        "axes": {},
        "axformat": {
            "Pad": 0.05,
        },
        "axadjust": {},
        "plot": {},
        "error": {},
        "minmax": {},
        "uq": {},
        "fillbetween": {},
        "errorbar": {
            "capsize": 1.5,
            "lw": 0.5,
            "elinewidth": 0.8,
            "zorder": 6,
        },
        "imshow": {},
        "grid": {
            "Grid": True,
            "MajorGrid": True,
        },
        "majorgrid": {
            "ls": ":",
            "lw": 0.5,
            "color": "#a0a0a0",
        },
        "minorgrid": {},
        "hist": {
            "facecolor": 'c',
            "zorder": 2,
            "bins": 20,
            "density": True,
            "edgecolor": 'k',
        },
        "legend": {
            "loc": "upper center",
            "labelspacing": 0.5,
            "framealpha": 1.0,
        },
        "font": {},
        "spines": {
            "Spines": True,
            "Ticks": True,
            "TickDirection": "out",
            "RightSpineTicks": False,
            "TopSpineTicks": False,
            "RightSpine": False,
            "TopSpine": False,
        },
        "mu": {
            "color": 'k',
            "lw": 2,
            "zorder": 6,
            "label": "Mean value",
        },
        "gauss": {
            "color": "navy",
            "lw": 1.5,
            "zorder": 7,
            "label": "Normal Distribution",
        },
        "interval": {
            "color": "b",
            "lw": 0,
            "zorder": 1,
            "alpha": 0.2,
            "imin": 0.,
            "imax": 5.,
        },
        "std": {
            'color': 'navy',
            'lw': 2,
            'zorder': 5,
            "dashes": [4, 2],
            'StDev': 3,
        },
        "delta": {
            'color': "r",
            'ls': "--",
            'lw': 1.0,
            'zorder': 3,
        },
        "histlbl": {
            'color': 'k',
            'horizontalalignment': 'right',
            'verticalalignment': 'top',
        },
    }
  # >

  # ==================
  # Categories
  # ==================
  # <
    # Subplot column options
    def axadjust_col_options(self):
        r"""Process options for axes margin adjustment

        :Call:
            >>> kw = opts.axadjust_col_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`axes_adjust_col`
        :Versions:
            * 2020-01-10 ``@ddalle``: First version
            * 2020-01-18 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("axadjust_col")

    # Subplot row options
    def axadjust_row_options(self):
        r"""Process options for axes margin adjustment

        :Call:
            >>> kw = opts.axadjust_row_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`axes_adjust_row`
        :Versions:
            * 2020-01-10 ``@ddalle``: First version
            * 2020-01-18 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("axadjust_row")

    # Process axes formatting options
    def axadjust_options(self):
        r"""Process options for axes margin adjustment

        :Call:
            >>> kw = opts.axadjust_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`axes_adjust`
        :Versions:
            * 2020-01-08 ``@ddalle``: First version
            * 2020-01-18 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("axadjust")

    # Axes options
    def axes_options(self):
        r"""Process options for axes handle

        :Call:
            >>> kw = opts.axes_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`plt.axes`
        :Versions:
            * 2019-03-07 ``@ddalle``: First version
            * 2019-12-20 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "axes" section
        return self.section_options("axes")

    # Process axes formatting options
    def axformat_options(self):
        r"""Process options for axes format

        :Call:
            >>> kw = opts.axformat_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`axes_format`
        :Versions:
            * 2019-03-07 ``@jmeeroff``: First version
            * 2020-01-18 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("axformat")

    # Process options for "error" plot
    def error_options(self):
        r"""Process options for error plots

        :Call:
            >>> kw = opts.error_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`error`
        :Versions:
            * 2019-03-04 ``@ddalle``: First version
            * 2019-12-23 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "minmax" section
        kw = self.section_options("error")
        # Save section name
        mainopt = "ErrorOptions"
        # Get type-specific options removed
        kw_eb = kw.pop("ErrorBarOptions", {})
        kw_fb = kw.pop("FillBetweenOptions", {})
        kw_mm = kw.get(mainopt, {})
        # Get the plot type
        mmax_type = kw.get("MinMaxPlotType", "fillbetween").lower()
        mmax_type = mmax_type.replace("_", "")
        # Check type
        if mmax_type == "errorbar":
            # Combine ErrorBar options into main options
            kw[mainopt] = dict(kw_eb, **kw_mm)
        else:
            # Combine FillBetween options into main options
            kw[mainopt] = dict(kw_fb, **kw_mm)
        # Output
        return kw

    # Options for errorbar() plots
    def errorbar_options(self):
        r"""Process options for :func:`errorbar` calls

        :Call:
            >>> kw = opts.errorbar_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`errorbar`
        :Versions:
            * 2019-03-05 ``@ddalle``: First version
            * 2019-12-21 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Specific options
        return self.get_option("ErrorBarOptions")

    # Figure creation and manipulation
    def figure_options(self):
        r"""Process options specific to Matplotlib figure

        :Call:
            >>> kw = figure_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`plt.figure`
        :Versions:
            * 2019-03-06 ``@ddalle``: First version
            * 2019-12-20 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "figure" section
        return self.section_options("fig")

    # Options for fill_between() plots
    def fillbetween_options(self):
        r"""Process options for :func:`fill_between` calls

        :Call:
            >>> kw = opts.fillbetween_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`fill_between`
        :Versions:
            * 2019-03-05 ``@ddalle``: First version
            * 2019-12-21 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Specific options
        return self.get_option("FillBetweenOptions")

    # Global font options
    def font_options(self):
        r"""Process global font options

        :Call:
            >>> kw = opts.font_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of font property options
        :Versions:
            * 2019-03-07 ``@ddalle``: First version
            * 2019-12-19 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "font" section and only return "FontOptions"
        return self.section_options("font", "FontOptions")

    # Grid options
    def grid_options(self):
        r"""Process options to axes :func:`grid` command

        :Call:
            >>> kw = opts.grid_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`grid`
        :Versions:
            * 2019-03-07 ``@jmeeroff``: First version
            * 2019-12-23 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("grid")

    # Process imshow() options
    def imshow_options(self):
        r"""Process options for image display calls

        :Call:
            >>> kw = opts.imshow_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`imshow`
        :Versions:
            * 2020-01-09 ``@ddalle``: First version
            * 2020-01-18 ``@ddalle``: Using :class:`KwargHandler`
        """
        return self.section_options("imshow")

    # Options for font in legend
    def legend_font_options(self):
        r"""Process font options for :func:`legend` calls

        :Call:
            >>> kw = opts.legend_font_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`errorbar`
        :Versions:
            * 2020-01-19 ``@ddalle``: First version
        """
        # Specific options
        return self.get_option("LegendFontOptions")

    # Legend options
    def legend_options(self):
        r"""Process options for :func:`legend`
    
        :Call:
            >>> kw = opts.legend_options(kw, kwp={})
        :Inputs:
            *kw*: :class:`dict`
                Dictionary of options to parent function
            *kwp*: {``{}``}  | :class:`dict`
                Dictionary of options from which to inherit
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Options to :func:`legend`
        :Versions:
            * 2019-03-07 ``@ddalle``: First version
            * 2019-12-23 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-98 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Get *LegendOptions* options
        kw = self.get_option("LegendOptions")
        # Specific location options
        loc = kw.get("loc")
        # Check it
        if loc in ["upper center", 9]:
            # Bounding box location on top spine
            kw.setdefault("bbox_to_anchor", (0.5, 1.05))
        elif loc in ["lower center", 8]:
            # Bounding box location on bottom spine
            kw.setdefault("bbox_to_anchor", (0.5, -0.05))
        # Output
        return kw

    # Primary options
    def plot_options(self):
        r"""Process options to primary plot curve

        :Call:
            >>> kw = opts.plot_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`plot`
        :Versions:
            * 2019-03-07 ``@ddalle``: First version
            * 2019-12-19 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "plot" section and only return "PlotOptions"
        return self.section_options("plot", "PlotOptions")

    # Process options for min/max plot
    def minmax_options(self):
        r"""Process options for min/max plots

        :Call:
            >>> kw = opts.minmax_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`minmax`
        :Versions:
            * 2019-03-04 ``@ddalle``: First version
            * 2019-12-20 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "minmax" section
        kw = self.section_options("minmax")
        # Save section name
        mainopt = "MinMaxOptions"
        # Get type-specific options removed
        kw_eb = kw.pop("ErrorBarOptions", {})
        kw_fb = kw.pop("FillBetweenOptions", {})
        kw_mm = kw.get(mainopt, {})
        # Get the plot type
        mmax_type = kw.get("MinMaxPlotType", "fillbetween").lower()
        mmax_type = mmax_type.replace("_", "")
        # Check type
        if mmax_type == "errorbar":
            # Combine ErrorBar options into main options
            kw[mainopt] = dict(kw_eb, **kw_mm)
        else:
            # Combine FillBetween options into main options
            kw[mainopt] = dict(kw_fb, **kw_mm)
        # Output
        return kw

    # Process options for UQ plot
    def uq_options(self):
        r"""Process options for uncertainty quantification plots

        :Call:
            >>> kw = opts.uq_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to :func:`uq`
        :Versions:
            * 2019-03-04 ``@ddalle``: First version
            * 2019-12-23 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-17 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "uq" section
        kw = self.section_options("uq")
        # Save section name
        mainopt = "UncertaintyOptions"
        # Get type-specific options removed
        kw_eb = kw.pop("ErrorBarOptions", {})
        kw_fb = kw.pop("FillBetweenOptions", {})
        kw_mm = kw.get(mainopt, {})
        # Get the plot type
        mmax_type = kw.get("UncertaintyPlotType", "fillbetween").lower()
        mmax_type = mmax_type.replace("_", "")
        # Check type
        if mmax_type == "errorbar":
            # Combine ErrorBar options into main options
            kw[mainopt] = dict(kw_eb, **kw_mm)
        else:
            # Combine FillBetween options into main options
            kw[mainopt] = dict(kw_fb, **kw_mm)
        # Output
        return kw

    # Spine options
    def spine_options(self):
        r"""Process options for axes "spines"

        :Call:
            >>> kw = opts.spine_options()
        :Inputs:
            *opts*: :class:`MPLOpts`
                Options interface
        :Keys:
            %(keys)s
        :Outputs:
            *kw*: :class:`dict`
                Dictionary of options to each of four spines
        :Versions:
            * 2019-03-07 ``@jmeeroff``: First version
            * 2019-12-20 ``@ddalle``: From :mod:`tnakit.mpl.mplopts`
            * 2020-01-20 ``@ddalle``: Using :class:`KwargHandler`
        """
        # Use the "spines" section, cascading opts handled internally
        return self.section_options("spines")
  # >

# Document sublists
MPLOpts._doc_keys("axadjust_options", "axadjust")
MPLOpts._doc_keys("axadjust_col_options", "axadjust_col")
MPLOpts._doc_keys("axadjust_row_options", "axadjust_row")
MPLOpts._doc_keys("axformat_options", "axformat")
MPLOpts._doc_keys("axes_options", "axes")
MPLOpts._doc_keys("error_options", "error")
MPLOpts._doc_keys("figure_options", "fig")
MPLOpts._doc_keys("grid_options", "grid")
MPLOpts._doc_keys("imshow_options", "imshow")
MPLOpts._doc_keys("minmax_options", "minmax")
MPLOpts._doc_keys("plot_options", "plot")
MPLOpts._doc_keys("spine_options", "spines")
MPLOpts._doc_keys("uq_options", "uq")

# Special categories
MPLOpts._doc_keys("errorbar_options", ["ErrorBarOptions"])
MPLOpts._doc_keys("fillbetween_options", ["FillBetweenOptions"])
MPLOpts._doc_keys("legend_font_options", ["LegendFontOptions"])
MPLOpts._doc_keys("legend_options", ["LegendOptions"])
