#!/usr/bin/env python 
__author__ = "Jai Ram Rideout"
__copyright__ = "Copyright 2007-2012, The Cogent Project"
__credits__ = ["Jai Ram Rideout"]
__license__ = "GPL"
__version__ = "1.5.3-dev"
__maintainer__ = "Jai Ram Rideout"
__email__ = "jai.rideout@gmail.com"
__status__ = "Production"

"""This module contains functions for plotting distributions in various ways.

There are two different types of plotting functions:

generate_box_plots() plots several boxplots next to each other for easy
comparison.

generate_comparative_plots() plots groupings of distributions at data
points along the x-axis.
"""
from matplotlib import use
use('Agg', warn=False)
from itertools import cycle
from math import isnan
from matplotlib.colors import colorConverter
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle
from matplotlib.pyplot import boxplot, figure
from matplotlib.transforms import Bbox
from numpy import array, mean, random, sqrt, std

def generate_box_plots(distributions, x_values=None, x_tick_labels=None,
                       title=None, x_label=None, y_label=None,
                       x_tick_labels_orientation='vertical', y_min=None,
                       y_max=None, whisker_length=1.5, box_width=0.5,
                       box_color=None, figure_width=None, figure_height=None):
    """Returns a matplotlib.figure.Figure object containing a boxplot for each
    distribution.

    Arguments:
        - distributions: A list of lists containing each distribution.
        - x_values: A list indicating where each boxplot should be placed. Must
            be the same length as distributions if provided.
        - x_tick_labels: A list of labels to be used to label x-axis ticks.
        - title: A string containing the title of the plot.
        - x_label: A string containing the x-axis label.
        - y_label: A string containing the y-axis label.
        - x_tick_labels_orientation: A string specifying the orientation of the
            x-axis labels (either "vertical" or "horizontal").
        - y_min: The minimum value of the y-axis. If None, uses matplotlib's
            autoscale.
        - y_max: The maximum value of the y-axis. If None, uses matplotlib's
            autoscale.
        - whisker_length: The length of the whiskers as a function of the IQR.
            For example, if 1.5, the whiskers extend to 1.5 * IQR. Anything
            outside of that range is seen as an outlier.
        - box_width: The width of each box in plot units.
        - box_color: The color of the boxes. If None, boxes will be the same
          color as the plot background.
        - figure_width: the width of the plot figure in inches. If not
            provided, will default to matplotlib's default figure width.
        - figure_height: the height of the plot figure in inches. If not
            provided, will default to matplotlib's default figure height.
    """
    # Make sure our input makes sense.
    for distribution in distributions:
        if len(distribution) == 0:
            raise ValueError("Some of the provided distributions are empty.")
        try:
            list(map(float, distribution))
        except:
            raise ValueError("Each value in each distribution must be a "
                             "number.")

    _validate_x_values(x_values, x_tick_labels, len(distributions));

    # Create a new figure to plot our data on, and then plot the distributions.
    result, plot_axes = _create_plot()
    box_plot = boxplot(distributions, positions=x_values, whis=whisker_length,
                       widths=box_width)
    if box_color is not None:
        _color_box_plot(plot_axes, box_plot, box_color)

    # Set up the various plotting options, such as x- and y-axis labels, plot
    # title, and x-axis values if they have been supplied.
    _set_axes_options(plot_axes, title, x_label, y_label,
                      x_tick_labels=x_tick_labels,
                      x_tick_labels_orientation=x_tick_labels_orientation,
                      y_min=y_min, y_max=y_max)

    _set_figure_size(result, figure_width, figure_height)
    return result

def generate_comparative_plots(plot_type, data, x_values=None,
        data_point_labels=None, distribution_labels=None,
        distribution_markers=None, x_label=None, y_label=None, title=None,
        x_tick_labels_orientation='vertical', y_min=None, y_max=None,
        whisker_length=1.5, error_bar_type='stdv', distribution_width=0.4,
        group_spacing=0.5, figure_width=None, figure_height=None):
    """Returns a Figure containing plots grouped at points along the x-axis.

    Arguments:
        - plot_type: A string indicating what type of plot should be created.
            Can be one of 'bar', 'scatter', or 'box', where 'bar' is a bar
            chart, 'scatter' is a scatter plot, and 'box' is a box plot.
        - data: A list of lists that represent each data point along the
            x-axis. Each data point contains lists of data for each
            distribution in the group at that point. This nesting allows for
            the grouping of distributions at each data point.
        - x_values: A list indicating the spacing along the x-axis. Must
            be the same length as the number of data points if provided. If not
            provided, plots will be spaced evenly.
        - data_point_labels: A list of strings containing the label for each
            data point.
        - distribution_labels: A list of strings containing the label for each
            distribution in a data point grouping.
        - distribution_markers: A list of matplotlib-compatible strings or
            tuples that indicate the color or symbol to be used to distinguish
            each distribution in a data point grouping. Colors will be used for
            bar charts or box plots, while symbols will be used for scatter
            plots.
        - x_label: A string containing the x-axis label.
        - y_label: A string containing the y-axis label.
        - title: A string containing the title of the plot.
        - x_tick_labels_orientation: A string specifying the orientation of the
            x-axis labels (either "vertical" or "horizontal").
        - y_min: The minimum value of the y-axis. If None, uses matplotlib's
            autoscale.
        - y_max: The maximum value of the y-axis. If None, uses matplotlib's
            autoscale.
        - whisker_length: If plot_type is 'box', determines the length of the
            whiskers as a function of the IQR. For example, if 1.5, the
            whiskers extend to 1.5 * IQR. Anything outside of that range is
            seen as an outlier. If plot_type is not 'box', this parameter is
            ignored.
        - error_bar_type: A string specifying the type of error bars to use if
            plot_type is "bar". Can be either "stdv" (for standard deviation)
            or "sem" for the standard error of the mean. If plot_type is not
            "bar", this parameter is ignored.
        - distribution_width: The width in plot units of each individual
            distribution (e.g. each bar if the plot type is a bar chart, or the
            width of each box if the plot type is a boxplot).
        - group_spacing: The gap width in plot units between each data point
            (i.e. the width between each group of distributions).
        - figure_width: the width of the plot figure in inches. If not
            provided, will default to matplotlib's default figure width.
        - figure_height: the height of the plot figure in inches. If not
            provided, will default to matplotlib's default figure height.
    """
    # Set up different behavior based on the plot type.
    if plot_type == 'bar':
        plotting_function = _plot_bar_data
        distribution_centered = False
        marker_type = 'colors'
    elif plot_type == 'scatter':
        plotting_function = _plot_scatter_data
        distribution_centered = True
        marker_type = 'symbols'
    elif plot_type == 'box':
        plotting_function = _plot_box_data
        distribution_centered = True
        marker_type = 'colors'
    else:
        raise ValueError("Invalid plot type '%s'. Supported plot types are "
                "'bar', 'scatter', or 'box'." % plot_type)

    num_points, num_distributions = _validate_input(data, x_values,
            data_point_labels, distribution_labels)

    # Create a list of matplotlib markers (colors or symbols) that can be used
    # to distinguish each of the distributions. If the user provided a list of
    # markers, use it and loop around to the beginning if there aren't enough
    # markers. If they didn't provide a list, or it was empty, use our own
    # predefined list of markers (again, loop around to the beginning if we
    # need more markers).
    distribution_markers = _get_distribution_markers(marker_type,
                                                     distribution_markers,
                                                     num_distributions)

    # Now calculate where each of the data points will start on the x-axis.
    x_locations = _calc_data_point_locations(x_values, num_points,
            num_distributions, distribution_width, group_spacing)
    assert (len(x_locations) == num_points), "The number of x_locations " +\
            "does not match the number of data points."

    # Create the figure to put the plots on, as well as a list to store an
    # example of each distribution's plot (needed for the legend).
    result, plot_axes = _create_plot()

    # Iterate over each data point, and plot each of the distributions at that
    # data point. Increase the offset after each distribution is plotted,
    # so that the grouped distributions don't overlap.
    for point, x_pos in zip(data, x_locations):
        dist_offset = 0
        for dist_index, dist, dist_marker in zip(list(range(num_distributions)),
                                                 point, distribution_markers):
            dist_location = x_pos + dist_offset
            distribution_plot_result = plotting_function(plot_axes, dist,
                    dist_marker, distribution_width, dist_location,
                    whisker_length, error_bar_type)
            dist_offset += distribution_width

    # Set up various plot options that are best set after the plotting is done.
    # The x-axis tick marks (one per data point) are centered on each group of
    # distributions.
    plot_axes.set_xticks(_calc_data_point_ticks(x_locations,
            num_distributions, distribution_width, distribution_centered))
    _set_axes_options(plot_axes, title, x_label, y_label, x_values,
                      data_point_labels, x_tick_labels_orientation, y_min,
                      y_max)

    if distribution_labels is not None:
        _create_legend(plot_axes, distribution_markers, distribution_labels,
                       marker_type)

    _set_figure_size(result, figure_width, figure_height)

    # matplotlib seems to sometimes plot points on the rightmost edge of the
    # plot without adding padding, so we need to add our own to both sides of
    # the plot. For some reason this has to go after the call to draw(),
    # otherwise matplotlib throws an exception saying it doesn't have a
    # renderer.
    plot_axes.set_xlim(plot_axes.get_xlim()[0] - group_spacing,
                       plot_axes.get_xlim()[1] + group_spacing)
    return result

def _validate_input(data, x_values, data_point_labels, distribution_labels):
    """Returns a tuple containing the number of data points and distributions
    in the data.
    
    Validates plotting options to make sure they are valid with the supplied
    data.
    """
    if data is None or not data or isinstance(data, str):
        raise ValueError("The data must be a list type, and it cannot be "
                         "None or empty.")

    num_points = len(data)
    num_distributions = len(data[0])

    empty_data_error_msg = "The data must contain at least one data " + \
                           "point, and each data point must contain at " + \
                           "least one distribution to plot."
    if num_points == 0 or num_distributions == 0:
        raise ValueError(empty_data_error_msg)

    for point in data:
        if len(point) == 0:
            raise ValueError(empty_data_error_msg)
        if len(point) != num_distributions:
            raise ValueError("The number of distributions in each data point "
                             "grouping must be the same for all data points.")

    # Make sure we have the right number of x values (one for each data point),
    # and make sure they are numbers.
    _validate_x_values(x_values, data_point_labels, num_points)

    if (distribution_labels is not None and
        len(distribution_labels) != num_distributions):
        raise ValueError("The number of distribution labels must be equal "
                         "to the number of distributions.")
    return num_points, num_distributions

def _validate_x_values(x_values, x_tick_labels, num_expected_values):
    """Validates the x values provided by the user, making sure they are the
    correct length and are all numbers.
    
    Also validates the number of x-axis tick labels.
    
    Raises a ValueError if these conditions are not met.
    """
    if x_values is not None:
        if len(x_values) != num_expected_values:
            raise ValueError("The number of x values must match the number "
                             "of data points.")
        try:
            list(map(float, x_values))
        except:
            raise ValueError("Each x value must be a number.")

    if x_tick_labels is not None:
        if len(x_tick_labels) != num_expected_values:
            raise ValueError("The number of x-axis tick labels must match the "
                             "number of data points.")

def _get_distribution_markers(marker_type, marker_choices, num_markers):
    """Returns a list of length num_markers of valid matplotlib colors or
    symbols.

    The markers will be comprised of those found in marker_choices (if not None
    and not empty) or a list of predefined markers (determined by marker_type,
    which can be either 'colors' or 'symbols'). If there are not enough
    markers, the list of markers will be reused from the beginning again (as
    many times as are necessary).
    """
    if num_markers < 0:
        raise ValueError("num_markers must be greater than or equal to zero.")
    if marker_choices is None or len(marker_choices) == 0:
        if marker_type == 'colors':
            marker_choices = ['b', 'g', 'r', 'c', 'm', 'y', 'w']
        elif marker_type == 'symbols':
            marker_choices = \
                ['s', 'o', '^', '>', 'v', '<', 'd', 'p', 'h', '8', '+', 'x']
        else:
            raise ValueError("Invalid marker_type: '%s'. marker_type must be "
                             "either 'colors' or 'symbols'." % marker_type)
    if len(marker_choices) < num_markers:
        # We don't have enough markers to represent each distribution uniquely,
        # so let the user know. We'll add as many markers (starting from the
        # beginning of the list again) until we have enough, but the user
        # should still know because they may want to provide a new list of
        # markers.
        print ("There are not enough markers to uniquely represent each "
               "distribution in your dataset. You may want to provide a list "
               "of markers that is at least as large as the number of "
               "distributions in your dataset.")
        marker_cycle = cycle(marker_choices[:])
        while len(marker_choices) < num_markers:
            marker_choices.append(next(marker_cycle))
    return marker_choices[:num_markers]

def _calc_data_point_locations(x_values, num_points, num_distributions,
                               dist_width, group_spacing):
    """Returns a numpy array of x-axis locations for each of the data points to
    start at.

    Note: A numpy array is returned so that the overloaded "+" operator can be
    used on the array.
    
    The x locations are spaced according to the spacing between points, and the
    width of each distribution grouping at each point. The x locations are also
    scaled by the x_values that may have been supplied by the user. If none are
    supplied, the x locations are evenly spaced.
    """
    if dist_width <= 0 or group_spacing < 0:
        raise ValueError("The width of a distribution cannot be zero or "
                         "negative. The width of the spacing between groups "
                         "of distributions cannot be negative.")
    if x_values is None:
        # Evenly space the x locations.
        x_values = list(range(1, num_points + 1))

    assert (len(x_values) == num_points), "The number of x_values does not " +\
            "match the number of data points."

    # Calculate the width of each grouping of distributions at a data point.
    # This is multiplied by the current x value to give us our final
    # absolute horizontal position for the current point.
    return array([(dist_width * num_distributions + group_spacing) * x_val\
                     for x_val in x_values])

def _calc_data_point_ticks(x_locations, num_distributions, distribution_width,
                           distribution_centered):
    """Returns a 1D numpy array of x-axis tick positions.

    These positions will be centered on each data point.
    
    Set distribution_centered to True for scatter and box plots because their
    plot types naturally center over a given horizontal position. Bar charts 
    should use distribution_centered = False because the leftmost edge of a bar
    starts at a given horizontal position and extends to the right for the
    width of the bar.
    """
    dist_size = num_distributions - 1 if distribution_centered else\
            num_distributions
    return x_locations + ((dist_size * distribution_width) / 2)

def _create_plot():
    """Creates a plot and returns the associated Figure and Axes objects."""
    fig = figure()
    ax = fig.add_subplot(111)
    return fig, ax

def _plot_bar_data(plot_axes, distribution, distribution_color,
                   distribution_width, x_position, whisker_length,
                   error_bar_type):
    """Returns the result of plotting a single bar in matplotlib."""
    result = None

    # We do not want to plot empty distributions because matplotlib will not be
    # able to render them as PDFs.
    if len(distribution) > 0:
        avg = mean(distribution)
        if error_bar_type == 'stdv':
            error_bar = std(distribution)
        elif error_bar_type == 'sem':
            error_bar = std(distribution) / sqrt(len(distribution))
        else:
            raise ValueError("Invalid error bar type '%s'. Supported error "
                    "bar types are 'stdv' and 'sem'." % error_bar_type)
        result = plot_axes.bar(x_position, avg, distribution_width,
                               yerr=error_bar, ecolor='black',
                               facecolor=distribution_color)
    return result

def _plot_scatter_data(plot_axes, distribution, distribution_symbol,
                       distribution_width, x_position, whisker_length,
                       error_bar_type):
    """Returns the result of plotting a single scatterplot in matplotlib."""
    result = None
    x_vals = [x_position] * len(distribution)

    # matplotlib's scatter function doesn't like plotting empty data.
    if len(x_vals) > 0 and len(distribution) > 0:
        result = plot_axes.scatter(x_vals, distribution,
                                   marker=distribution_symbol, c='k')
    return result

def _plot_box_data(plot_axes, distribution, distribution_color,
                   distribution_width, x_position, whisker_length,
                   error_bar_type):
    """Returns the result of plotting a single boxplot in matplotlib."""
    box_plot = plot_axes.boxplot([distribution], positions=[x_position],
                                 widths=distribution_width,
                                 whis=whisker_length)
    _color_box_plot(plot_axes, box_plot, distribution_color)
    return box_plot

def _color_box_plot(plot_axes, box_plot, color):
    """Fill each box in the box plot with the specified color.

    The box_plot argument must be the dictionary returned by the call to
    matplotlib's boxplot function, and the color argument must be a valid
    matplotlib color.
    """
    # Note: the following code is largely taken from a matplotlib boxplot
    # example:
    # http://matplotlib.sourceforge.net/examples/pylab_examples/
    #     boxplot_demo2.html
    num_boxes = len(box_plot['boxes'])
    for box_num in range(num_boxes):
        box = box_plot['boxes'][box_num]
        boxX = []
        boxY = []
        # There are five points in the box. The first is the same as
        # the last.
        for j in range(5):
            boxX.append(box.get_xdata()[j])
            boxY.append(box.get_ydata()[j])
        boxCoords = list(zip(boxX,boxY))
        boxPolygon = Polygon(boxCoords, facecolor=color)
        plot_axes.add_patch(boxPolygon)

        # Draw the median lines back over what we just filled in with
        # color.
        median = box_plot['medians'][box_num]
        medianX = []
        medianY = []
        for j in range(2):
            medianX.append(median.get_xdata()[j])
            medianY.append(median.get_ydata()[j])
            plot_axes.plot(medianX, medianY, 'black')

def _set_axes_options(plot_axes, title=None, x_label=None, y_label=None,
                      x_values=None, x_tick_labels=None,
                      x_tick_labels_orientation='vertical', y_min=None,
                      y_max=None):
    """Applies various labelling options to the plot axes."""
    if title is not None:
        plot_axes.set_title(title)
    if x_label is not None:
        plot_axes.set_xlabel(x_label)
    if y_label is not None:
        plot_axes.set_ylabel(y_label)

    if (x_tick_labels_orientation != 'vertical' and
        x_tick_labels_orientation != 'horizontal'):
        raise ValueError("Invalid orientation for x-axis tick labels: %s. "
                         "Valid orientations are 'vertical' or 'horizontal'."
                         % x_tick_labels_rotation)

    # If labels are provided, always use them. If they aren't, use the x_values
    # that denote the spacing between data points as labels. If that isn't
    # available, simply label the data points in an incremental fashion,
    # i.e. 1, 2, 3,...,n, where n is the number of data points on the plot.
    if x_tick_labels is not None:
        labels = plot_axes.set_xticklabels(x_tick_labels,
                                           rotation=x_tick_labels_orientation)
    elif x_tick_labels is None and x_values is not None:
        labels = plot_axes.set_xticklabels(x_values,
                                           rotation=x_tick_labels_orientation)
    else:
        labels = plot_axes.set_xticklabels(
                    list(range(1, len(plot_axes.get_xticklabels()) + 1)),
                    rotation=x_tick_labels_orientation)

    # Set the y-axis range if specified.
    if y_min is not None:
        plot_axes.set_ylim(bottom=float(y_min))
    if y_max is not None:
        plot_axes.set_ylim(top=float(y_max))

def _create_legend(plot_axes, distribution_markers, distribution_labels,
                   marker_type):
    """Creates a legend on the supplied axes."""
    # We have to use a proxy artist for the legend because box plots currently
    # don't have a very useful legend in matplotlib, and using the default
    # legend for bar/scatterplots chokes on empty/null distributions.
    # Note: This code is based on the following examples:
    #   http://matplotlib.sourceforge.net/users/legend_guide.html
    #   http://stackoverflow.com/a/11423554
    if len(distribution_markers) != len(distribution_labels):
        raise ValueError("The number of distribution markers does not match "
                         "the number of distribution labels.")
    if marker_type == 'colors':
        legend_proxy = [Rectangle((0, 0), 1, 1, fc=marker)
                        for marker in distribution_markers]
        plot_axes.legend(legend_proxy, distribution_labels, loc='best')
    elif marker_type == 'symbols':
        legend_proxy = [Line2D(list(range(1)), list(range(1)), color='white',
                        markerfacecolor='black', marker=marker)
                        for marker in distribution_markers]
        plot_axes.legend(legend_proxy, distribution_labels, numpoints=3,
                         scatterpoints=3, loc='best')
    else:
        raise ValueError("Invalid marker_type: '%s'. marker_type must be "
                         "either 'colors' or 'symbols'." % marker_type)

def _set_figure_size(fig, width=None, height=None):
    """Sets the plot figure size and makes room for axis labels, titles, etc.

    If both width and height are not provided, will use matplotlib defaults.

    Making room for labels will not always work, and if it fails, the user will
    be warned that their plot may have cut-off labels.
    """
    # Set the size of the plot figure, then make room for the labels so they
    # don't get cut off. Must be done in this order.
    if width is not None and height is not None and width > 0 and height > 0:
        fig.set_size_inches(width, height)
    try:
        fig.tight_layout()
    except ValueError:
        print ("Warning: could not automatically resize plot to make room for "
               "axes labels and plot title. This can happen if the labels or "
               "title are extremely long and the plot size is too small. Your "
               "plot may have its labels and/or title cut-off. To fix this, "
               "try increasing the plot's size (in inches) and try again.")
