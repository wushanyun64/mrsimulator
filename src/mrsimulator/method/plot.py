# -*- coding: utf-8 -*-
from itertools import groupby

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

__author__ = "Matthew D. Giammar"
__email__ = "giammar.7@buckeyemail.osu.edu"


DURATION_WIDTH = 0.6  # Width of one ConstantDurationEvent
SPECTRAL_MULTIPLIER = 1  # Width multiplier for all SpectralEvents
MIXING_WIDTH = 0.3  # tip_angle of 360 degrees
# TODO: Ensure cannot run out of colors
COLORS = list(mcolors.TABLEAU_COLORS)
EVENT_COLORS = {  # TODO: add colors
    "ConstantDurationEvent": "orange",
    "SpectralEvent": "g",
    "MixingEvent": "b",
}
GRAPH_PROPERTIES = {
    "rotor_angle": {
        "ylim": (0, 90),
        "yticks": [15, 30, 45, 60, 75],
        "grid": {"axis": "y", "color": "black", "alpha": 0.2},
    }
}


def _make_x_data(df):
    """Returns list of x points to use in plotting"""
    points = [0]

    for i, row in df.iterrows():
        if row["type"] == "SpectralEvent":
            next_x = points[-1] + (row["fraction"] * SPECTRAL_MULTIPLIER)
            points.extend((next_x, next_x))
        elif row["type"] == "ConstantDurationEvent":
            next_x = points[-1] + DURATION_WIDTH
            points.extend((next_x, next_x))

    points.pop()
    return points


def _offset_x_data(df, x_data):
    """Offsets x_data based on MixingEvents"""
    offset_x = np.array([0] + x_data)
    ev_groups = [(_type, sum(1 for _ in group)) for _type, group in groupby(df["type"])]

    # Remove MixingEvents from end of sequence
    if ev_groups[-1][0] == "MixingEvent":
        ev_groups.pop()

    df_idx = 0
    # Extend first jump if first event(s) are MixingEvent
    if ev_groups[0][0] == "MixingEvent":
        gp__ = ev_groups[0][1]
        offset = sum(df["tip_angle"][0:gp__]) / 360.0 * MIXING_WIDTH
        offset_x[1] += offset
        # Increment event indexer by number of MixingEvents in first group
        df_idx += gp__
        ev_groups.pop(0)

    x_idx = 1
    for _type, num in ev_groups:
        if _type == "MixingEvent":
            up_lim__ = df_idx + num
            offset = sum(df["tip_angle"][df_idx:up_lim__]) / 360.0 * MIXING_WIDTH
            offset_x[x_idx] -= offset / 2
            offset_x[x_idx + 1] += offset / 2
            x_idx += 1
        else:
            if offset_x[x_idx] == offset_x[x_idx + 1]:
                x_idx += 1
            x_idx += (num * 2) - 1
        # Increment event indexer by number of Events in group
        df_idx += num

    return offset_x


def _add_rect_with_label(ax, x0, x1, label, ev_type):
    """Add a rectangle between x0 and x1 on ax representing event"""
    rect_kwargs = {"color": EVENT_COLORS[ev_type], "alpha": 0.2}
    anno_kwargs = {
        "color": "black",
        "ha": "center",
        "va": "center",
        "fontsize": 8,
        "rotation": 90 if ev_type == "MixingEvent" else 0,
    }
    rect = Rectangle((x0, 0), x1 - x0, 1, **rect_kwargs)
    ax.add_patch(rect)
    if label is not None:
        ax.annotate(label, ((x1 + x0 + 0.015) / 2, 0.5), **anno_kwargs)


def _format_mix_label(tip_angle, phase):
    """Helper method to format label for mixing events."""
    return "({0:.1f}, {1:.1f})".format(tip_angle, phase), tip_angle / 360 * MIXING_WIDTH


def _plot_spec_dim(ax, ev_groups, x_data, df):
    """Adds a line denoting a new spectral dimension with label"""
    anno_kwargs = {
        "annotation_clip": False,
        "color": "black",
        "ha": "center",
        "va": "center",
        "fontsize": 8,
    }
    ax.plot([0, 0], [0, 1], color="black")

    last_spec_dim_x = 0
    spec_dim_idx = 0
    df_idx = 0
    x_idx = 0
    for _type, num in ev_groups:
        for j in range(num):
            if x_data[x_idx] == x_data[x_idx + 1]:
                x_idx += 1
            if df["spec_dim_index"][df_idx + j] != spec_dim_idx:  # Next spec dim
                x_point = x_data[x_idx]
                if df["type"][df_idx + j] == "MixingEvent":
                    x_point += sum(df["tip_angle"][df_idx:j]) / 360.0 * MIXING_WIDTH
                ax.plot([x_point, x_point], [0, 1], color="black")
                ax.annotate(
                    # f"Spectral Dim. {spec_dim_idx}",
                    df["spec_dim_label"][df_idx + j - 1],
                    ((last_spec_dim_x + x_point) / 2, 1.1),
                    **anno_kwargs,
                )
                last_spec_dim_x = x_point
                spec_dim_idx += 1
            x_idx += 1
        df_idx += num

    # Plot last spectral dimension
    ax.plot([max(x_data), max(x_data)], [0, 1], color="black")
    ax.annotate(
        # f"Spectral Dim. {spec_dim_idx}",
        df["spec_dim_label"][df_idx - 1],
        ((last_spec_dim_x + max(x_data)) / 2, 1.1),
        **anno_kwargs,
    )


def _plot_sequence_diagram(ax, x_data, df):
    """Helper method to plot sequence diagram of method on ax"""
    ev_groups = [(_type, sum(1 for _ in group)) for _type, group in groupby(df["type"])]

    if ev_groups[-1][0] == "MixingEvent":
        x_data = np.append(x_data, x_data[-1])
        # Total angle / 360 * MIXING_WIDTH
        gp__ = -ev_groups[0][1]
        offset = sum(df["tip_angle"][gp__:]) / 180 * MIXING_WIDTH
        x_data[-2] -= offset

    _plot_spec_dim(ax, ev_groups, x_data, df)

    df_idx = 0
    x_idx = 0
    for _type, num in ev_groups:
        if _type == "MixingEvent":
            # Leftmost x point of next MixingEvent rectangle
            left_x = x_data[x_idx]
            # Iterate over each MixingEvent in group and plot rectangle
            for j in range(num):
                text, width = _format_mix_label(
                    df["tip_angle"][df_idx + j], df["phase"][df_idx + j]
                )
                _add_rect_with_label(ax, left_x, left_x + width, text, "MixingEvent")
                left_x += width
            x_idx += 1
        else:
            for j in range(num):
                # Increment x_idx if no mixing event between events
                if x_data[x_idx] == x_data[x_idx + 1]:
                    x_idx += 1
                _add_rect_with_label(
                    ax,
                    x_data[x_idx],
                    x_data[x_idx + 1],
                    df["label"][df_idx + j],
                    df["type"][df_idx + j],
                )
                x_idx += 1

        df_idx += num

    ax.axis("off")


def _plot_p_or_d(ax, x_data, y_data, name):
    """Helper method to plot p or d data on axis"""
    # Clean nan from y_data
    y_data = np.array(y_data[[np.any(~np.isnan(d)) for d in y_data]].tolist())

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

    # Ensure no errors thrown when plotting data
    if len(x_data) != len(y_data) * 2:
        # Warn misshapen data?
        return

    ax.plot(
        x_data,
        [_ for num in y_data for _ in (num, num)],
        color="b",
        alpha=0.6,
    )
    ax.set_ylabel(name.replace("_", " "))


def _format_subplot(ax, **kwargs):
    """Attitional subplot formatting based on parameter type"""
    kwargs = kwargs["kwargs"]
    if "ylim" in kwargs:
        ax.set_ylim(kwargs["ylim"])
    if "yticks" in kwargs:
        ax.set_yticks(kwargs["yticks"])
    if "grid" in kwargs:
        ax.grid(**kwargs["grid"])


def _check_columns(df):
    """Helper method to ensure required columns are present"""
    required = [
        "type",
        "label",
        "spec_dim_index",
        "spec_dim_label",
        "duration",
        "fraction",
        "mixing_query",
    ]

    # Required columns are not present in df
    if not (set(required)).issubset(set(df.columns)):
        raise ValueError("Some required columns were not present in the DataFrame.")

    if "freq_contrib" in df.columns:
        required += ["freq_contrib"]

    params = list(df.columns.drop(required))

    # Move p and d to front of params
    if "d" in params:
        params.insert(0, params.pop(params.index("d")))
    if "p" in params:
        params.insert(0, params.pop(params.index("p")))

    return params


def _add_tip_angle_and_phase(df):
    """Add tip_angle and phase columns to dataframe from mixing_query"""
    # NOTE Only columns for ch1 are created
    # NOTE What should empty MixingQuerys add? (MixingQuery default?)
    # BUG: Empty mixing queries (i.e. "mixing_query": {}) gives query of `None` causing
    #       error to be thrown
    df["tip_angle"] = [
        query.ch1.tip_angle * 180 / np.pi
        if query.__class__.__name__ == "MixingQuery"
        else np.nan
        for query in df["mixing_query"]
    ]
    df["phase"] = [
        query.ch1.phase * 180 / np.pi
        if query.__class__.__name__ == "MixingQuery"
        else np.nan
        for query in df["mixing_query"]
    ]


def plot(df) -> plt.figure:
    """Create figure of symmetry pathways for DataFrame representation of method"""
    params = _check_columns(df)
    _add_tip_angle_and_phase(df)

    if len(params) == 0:
        # Warn passed empty dataframe?
        return plt.figure()

    x_data = _make_x_data(df)

    if len(x_data) == 0:
        # Warn only mixing events
        return plt.figure()

    offset_x_data = _offset_x_data(df, x_data)
    fig, axs = plt.subplots(
        nrows=len(params) + 1,
        ncols=1,
        figsize=(max(x_data) * 2, (len(params) + 1) * 1.5),
        sharex=True,
        gridspec_kw={"hspace": 0.0},
    )

    axs[0].set_xlim(0, x_data[-1])
    axs[-1].get_xaxis().set_visible(False)

    # Plot sequence diagram
    _plot_sequence_diagram(axs[0], offset_x_data, df)

    # Iterate through axes and plot data
    for i, ax in enumerate(axs[1:], 0):
        print(params[i])
        if params[i] == "p" or params[i] == "d":
            _plot_p_or_d(ax, offset_x_data, df[params[i]], params[i])
        else:
            _plot_data(ax, x_data, df[params[i]], params[i])
        if params[i] in GRAPH_PROPERTIES:
            _format_subplot(ax, kwargs=GRAPH_PROPERTIES[params[i]])

    return fig
