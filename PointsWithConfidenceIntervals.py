"""
    Creates point plots with confidence intervals for categories of data.
    Categories or variables are on the x-axis and the magnitude of the
    difference or effect is on the y-axis. Places a legend with the variable
    names in the "best" location. Also includes a title.

    CIPlot(): creates a plot with confidence intervals for each data point.

    ComparisonCIPlot(): creates a plot with confidence intervals for each data
        point. This will have mean magnitudes for each variation and variable
        side by side.

    Initilization inputs:
        variableColumn = name of variable of interest.
        style = plot syle type (default is bmh).
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class PlotWithCI(object):

    def __init__(self, variableColumn, style='bmh'):

        self.variableColumn = variableColumn

        # Other styles: 'fivethirtyeight', 'seaborn-pastel', 'ggplot'
        self.style = style

    # _________________________________________________________________________
    def _Colors(self, j):
        """
        Different color scheme from the default Matplotlib scheme.
        """

        colors = ['aqua',
                  'powderblue',
                  'wheat',
                  'seagreen',
                  'beige',
                  'cornflowerblue',
                  'lightsalmon',
                  'darkturquoise',
                  'burlywood',
                  'aquamarine',
                  'darkseagreen',
                  'bisque',
                  'greenyellow']

        if j < len(colors):
            return colors[j]

        # Take the modulo of j to find the remainder, that way you can input
        # any number.
        else:
            return colors[j % len(colors)]

    # _________________________________________________________________________
    def _FigAxUtil(self, index, variableNames, yLabel, title, yMin, yMax):
        """
        Sets up the title, x and y labels, resizes the text, adjusts the label
        angle and so on.
        """

        self.ax.set_ylabel(yLabel, fontsize=30)
        self.fig.suptitle(title, fontsize=30)

        self.ax.set_xticks(index)
        self.ax.set_xticklabels(variableNames, rotation=45, fontsize=15)
        self.ax.tick_params(labelsize=15)

        self.ax.set_xlim(xmin=index[0]-0.5, xmax=index[-1]+0.5)

        if yMin is not None:
            self.ax.set_ylim(bottom=yMin)

        if yMax:
            self.ax.set_ylim(top=yMax)

    # _________________________________________________________________________
    def CIPlot(self, df, title, yLabel, yMin=None, yMax=None):
        """
        Creates a plot with confidence intervals for each data point.

        Input:
            fig = figure object.
            ax = axis object.
            df = dataframe with the columns: variableColumn, "variation",
                 "mean", "confidence_interval".
            variableName = name of the variable column.
            title = plot title.
            yLabel = y-axis label.
            yMin = minimum limit for y-axis. Default is None.
            yMax = maximum limit for y-axis. Default is None.

        Output:
            bar plot with confidence intervals.
        """

        variableColumn = self.variableColumn

        # Find the different variable names in each variation, then add in any
        # that are missing in one variation or the other. Set the values to
        # zero for the missing variables.
        allVariables = df[variableColumn].unique()

        # -----------------------------------------------------------
        # Create bar plot and calculate significance - if turned on.

        index = np.arange(len(allVariables))

        with plt.style.context((self.style)):

            self.fig, self.ax = plt.subplots(figsize=(10, 10))

            # Iterate through each variable.
            for i, varName in enumerate(allVariables):

                varDf = df.loc[df[variableColumn] == varName, :]

                # Calculate means and confidence intervals for the different
                # variations.
                mean = varDf['mean'].values
                ci = varDf.confidence_interval.values

                self.ax.errorbar(i,
                                 mean,
                                 yerr=ci,
                                 fmt='o',
                                 capthick=4,
                                 capsize=10,
                                 ms=20)

            self._FigAxUtil(index, allVariables, yLabel, title, yMin, yMax)

    # _________________________________________________________________________
    def ComparisonCIPlot(self, df, title, yLabel, yMin=0, yMax=None):
        """
        Creates a plot with confidence intervals for each data point. This will
        have mean magnitudes for each variation and variable side by side.

        Input:
            df = dataframe with the columns: variableColumn, "variation",
                 "mean", "confidence_interval".
            variableName = name of the variable column.
            title = plot title.
            yLabel = y-axis label.
            yMin = minimum limit for y-axis. Default is None.
            yMax = maximum limit for y-axis. Default is None.

        Output:
            bar plot with confidence intervals.
        """

        variableColumn = self.variableColumn

        # Find the different variable names in each variation, then add in any
        # that are missing in one variation or the other. Set the values to
        # zero for the missing variables.
        variations = df.variation.unique()
        allVariables = df[variableColumn].unique()

        # -----------------------------------------------------------
        # Create bar plot and calculate significance - if turned on.

        # Tick mark location.
        tickIndex = np.arange(len(allVariables)) + 1
        dataIndex = []

        # Data point locations (+-0.25 either side of the tick marks).
        for i in tickIndex:
            x = (i - 0.1, i + 0.1)
            dataIndex += [x]

        with plt.style.context((self.style)):

            self.fig, self.ax = plt.subplots(figsize=(10, 10))

            # Iterate through each variable.
            for i, varName in enumerate(allVariables):

                # For the legend, to avoid repeated variation labels.
                colorPatch = []

                for j, variation in enumerate(variations):

                    varDf = df.loc[(df[variableColumn] == varName)
                                   & (df['variation'] == variation), :]

                    # Calculate means and confidence intervals for the
                    # different variations.
                    mean = varDf['mean'].values
                    ci = varDf.confidence_interval.values

                    # Creating a location so that the data points are on either
                    # side of the tick mark.
                    loc = dataIndex[i][j]
                    color = self._Colors(j+5)
                    self.ax.errorbar(loc,
                                     mean,
                                     yerr=ci,
                                     fmt='o',
                                     capthick=4,
                                     capsize=10,
                                     ms=10,
                                     color=color)

                    colorPatch += [mpatches.Patch(color=color,
                                                  label=variation)]

            plt.legend(handles=colorPatch, loc=0, fontsize=20)
            self._FigAxUtil(tickIndex, allVariables, yLabel, title, yMin, yMax)
