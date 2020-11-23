#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard library
import sys

# Third-party modules
import numpy as np

# Import DataKit module
import cape.attdb.rdb as rdb


# Read MAT file
db = rdb.DataKit("bullet-fm-mab.mat")

# Column to plot
col = "bullet.CN"
# Filter
I, _ = db.find(["mach"], 0.95)

# Other options
kw = {
    "ContourColorMap": "bwr",
    "ContourLevels": 20,
    "MarkerOptions": {
        "marker": "v",
        "markerfacecolor": "none",
        "markersize": 4,
    },
}

# Plot
h = db.plot_contour(col, I, xk="beta", yk="alpha", **kw)

# Save figure
h.fig.savefig("python%i-CN-levels.png" % sys.version_info.major)
