import os
import posixpath
import signal
import subprocess
from pathlib import Path
from uuid import uuid4

from IPython.terminal.interactiveshell import TerminalInteractiveShell
from IPython.utils.capture import capture_output

TerminalInteractiveShell.orig_run = TerminalInteractiveShell.run_cell

JUPYTER_INITIAL_IMPORTS = """
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

from varro.sql import run_sql

import plotly.io as pio
pio.renderers.default = None
pio.templates.default = "plotly_white"
pio.templates["plotly_white"].layout.legend = dict(
    orientation="h",
    yanchor="top",
    y=-0.15,
    xanchor="center",
    x=0.5,
)
"""


def run_cell(self, cell, timeout=None):
    """
    Wrapper for original `run_cell`. No timeout. signal.alarm only fires on the main thread
    and is unreliable inside asyncio.
    """
    with capture_output() as io:
        result = self.orig_run(cell, silent=True)
    result.stdout = io.stdout
    result.outputs = io.outputs
    return result


TerminalInteractiveShell.run_cell = run_cell


def get_shell() -> TerminalInteractiveShell:
    "Get a `TerminalInteractiveShell` with minimal functionality"
    sh = TerminalInteractiveShell()
    sh.logger.log_output = sh.history_manager.enabled = False
    dh = sh.displayhook
    dh.finish_displayhook = dh.write_output_prompt = dh.start_displayhook = lambda: None
    dh.write_format_data = lambda format_dict, md_dict=None: None
    sh.logstart = sh.automagic = sh.autoindent = False
    sh.autocall = 0
    sh.system = lambda cmd: None
    return sh
