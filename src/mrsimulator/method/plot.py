# -*- coding: utf-8 -*-
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

__author__ = "Matthew D. Giammar"
__email__ = "giammar.7@buckeyemail.osu.edu"


DURATION_WIDTH = 0.4
MIXING_WIDTH = 0.04
# TODO: Ensure cannot run out of colors
COLORS = list(mcolors.TABLEAU_COLORS)


def _make_x_data(df):
    """Returns list of x points to use in plotting"""
    # TODO: Find value for constant duration event (tau/2)?
    points = [0]

    for i, row in df.iterrows():
        if row["type"] == "SpectralEvent":
            next_x = points[-1] + row["fraction"]
            points.extend((next_x, next_x))
        elif row["type"] == "ConstantDurationEvent":
            next_x = points[-1] + DURATION_WIDTH
            points.extend((next_x, next_x))

    points.pop()
    return points


def _offset_x_data(df, x_data):
    """Offsets x_data based on MixingEvents"""
    # NOTE: Mixing event at end of sequence will not be concidered
    offset_x = [0] + x_data
    first_non_mix_ev_idx = np.where(df["type"] != "MixingEvent")[0][0]

    # Mixing event at begining
    if df["type"][0] == "MixingEvent":
        offset_x[1] += MIXING_WIDTH * 2 * first_non_mix_ev_idx

    mix_count = 0
    idx = 0
    for ev_type in df["type"][first_non_mix_ev_idx:]:
        print(idx, ev_type)
        if ev_type == "MixingEvent":
            mix_count += 1
            continue
        if mix_count != 0:
            offset_x[idx * 2] -= MIXING_WIDTH * mix_count
            offset_x[idx * 2 + 1] += MIXING_WIDTH * mix_count
        idx += 1
        mix_count = 0

    return offset_x


def _plot_sequence_diagram(ax, x_data, df):
    """Helper method to plot sequence diagram of method on ax"""
    plot_pulse = False
    x_idx = 0

    def decay(x):
        """Expoenntial sinusodial decay"""
        # NOTE: Should array be zero anchored?
        # TODO: Better graphic for spectral event?
        x = x - x[0]
        return np.exp(-10 * x) * np.sin(28 * np.pi * x)

    def add_rect(ax, anchor, width, height, label):
        """Rectangle defining method diagram reigon"""

    # TODO: Incorperate muliple adjacent mixing events
    for i, row in df.iterrows():
        # TODO: Improve diagram with first event as mixing
        if i == 0 and row["type"] == "MixingEvent":
            ax.add_patch(
                Rectangle(
                    (x_data[x_idx], -0.7), x_data[x_idx + 1] - x_data[x_idx], 1.65
                )
            )
            x_idx += 1
            continue
        if row["type"] == "SpectralEvent":
            if plot_pulse:
                # print("spec pulse", x_data[x_idx], x_data[x_idx + 1])
                ax.add_patch(
                    Rectangle(
                        (x_data[x_idx], -0.7), x_data[x_idx + 1] - x_data[x_idx], 1.65
                    )
                )
                x_idx += 1

            # print("spec", x_data[x_idx], x_data[x_idx + 1])
            arr = np.linspace(x_data[x_idx], x_data[x_idx + 1], 150)
            ax.plot(arr, decay(arr), color="black")
            x_idx += 1
        elif row["type"] == "ConstantDurationEvent":
            if plot_pulse:
                # print("dur pulse", x_data[x_idx], x_data[x_idx + 1])
                ax.add_patch(
                    Rectangle(
                        (x_data[x_idx], -0.7), x_data[x_idx + 1] - x_data[x_idx], 1.65
                    )
                )
                x_idx += 1

            # print("dur", x_data[x_idx], x_data[x_idx + 1])
            ax.text(x=x_data[x_idx], y=0, s="tau/2")  # Use label
            x_idx += 1
        plot_pulse = row["type"] == "mixing"


def _plot_p_or_d(ax, x_data, y_data, name):
    """Helper method to plot p or d data on axis"""
    # Clean nan from y_data
    y_data = np.array(y_data[[np.any(~np.isnan(d)) for d in y_data]].tolist())
    # print(len(y_data), y_data)

    # Ensure no errors thrown when plotting data
    if len(x_data) - 1 != len(y_data) * 2:
        # Warn misshapen data?
        return

    for i in range(len(y_data[0])):
        ax.plot(
            x_data,
            [0] + [_ for num in y_data[:, i] for _ in (num, num)],
            color=COLORS[i],
            alpha=0.8,
            linewidth=2,
        )
    _range = max(  # Furthest point from origin
        abs(min([num for tup in y_data for num in tup])),
        abs(max([num for tup in y_data for num in tup])),
    )
    if name == "d" or _range > 5:
        # Even integers on y-axis
        _range = _range if _range % 2 == 0 else _range + 1  # Round up to next even int
        ax.set_ylim(-(_range + 2), _range + 2)
        ax.set_yticks(np.arange(-_range, _range + 1, step=2))
    else:
        ax.set_ylim(-(_range + 1), _range + 1)
        ax.set_yticks(np.arange(-_range, _range + 1, step=1))
    ax.grid(axis="y", color="black", alpha=0.2)
    ax.set_ylabel(name)


def _plot_data(ax, x_data, y_data, name):
    """Helper method to plot data and do formatting on ax"""
    # Clean nan from y_data
    y_data = np.array(y_data[[np.any(~np.isnan(d)) for d in y_data]].tolist())
    # print(len(y_data), y_data)

    # Ensure no errors thrown when plotting data
    if len(x_data) != len(y_data) * 2:
        # Warn misshapen data?
        return

    # if name == "p" or name == "d":
    #     # y_data is a np.2darray by chanel number
    #     for i in range(len(y_data[0])):
    #         ax.plot(
    #             x_data,
    #             [0] + [_ for num in y_data[:, i] for _ in (num, num)],
    #             color=COLORS.pop(),
    #             alpha=0.6,
    #             linewidth=2,
    #         )
    #     # TODO: Clean up formatting of y-ticks
    #     _range = max(  # Furthest point from origin
    #         abs(min([num for tup in y_data for num in tup])),
    #         abs(max([num for tup in y_data for num in tup])),
    #     )
    #     _range = _range if _range % 2 == 0 else _range + 1  # Round up to next even
    #     ax.set_ylim(-(_range + 2), _range + 2)
    #     ax.set_yticks(np.arange(-_range - 1, _range + 2, step=1 if _range < 5 else 2))
    #     ax.grid(axis="y", color="black", alpha=0.2)
    ax.plot(
        x_data,
        [_ for num in y_data for _ in (num, num)],
        color="b",
        alpha=0.6,
    )
    # y-axis formatting
    ax.set_ylabel(name.replace("_", " "))
    # Can y-axis numbers format better
    # ax.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter("%.2f"))


def plot(df) -> plt.figure:
    """Create Plotly figure of symmetry pathways for method

    Args:
        DataFrame df: dataframe representation of method events to be plot

    Returns:
        figure fig: Matplotlib figure

    Example:
        TODO add example code
    """
    params = list(df.columns.drop(["type", "label", "duration", "fraction"]))
    # Move p and d to front of params
    if "d" in params:
        params.insert(0, params.pop(params.index("d")))
    if "p" in params:
        params.insert(0, params.pop(params.index("p")))

    if len(params) == 0:
        # Warn passed empty dataframe?
        return plt.figure()

    x_data = _make_x_data(df)
    offset_x_data = _offset_x_data(df, x_data)
    fig, axs = plt.subplots(
        nrows=len(params) + 1,
        ncols=1,
        figsize=(max(x_data) * 2.5, len(params) * 1.5 + 2),
        sharex=True,
        gridspec_kw={"hspace": 0.0},
    )

    axs[0].set_xlim(0, x_data[-1])
    axs[-1].get_xaxis().set_visible(False)

    # Plot sequence diagram
    # _plot_sequence_diagram(axs[0], offset_x_data, df)

    # Iterate through axes and plot data
    for i, ax in enumerate(axs[1:], 0):
        if params[i] == "p" or params[i] == "d":
            _plot_p_or_d(ax, offset_x_data, df[params[i]], params[i])
        else:
            _plot_data(ax, x_data, df[params[i]], params[i])

    fig.tight_layout()
    return fig
