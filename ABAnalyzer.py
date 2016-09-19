"""
    This is a basic frequentist A-B test analysis script.  It can create two
    types of plots: an estimate of the mean effect size for the two
    variations with confidence interval bars, and an estimate of the magnitude
    of the mean of the variable in question in each variation separately, also
    with confidence interval bars. There is also an option to print out the
    calculated significance levels for the effect size.

    The two functions to call are: ABChangeAnalysis and ABMagnitudeAnalysis.

    Inputs:
        df = dataframe with columns: variableColumn, 'p', 'population', and
             'variation'.
        confidenceInterval = 0.95, 0.9, whatever you'd like.
        variableColumn = name of the effect you are concentrating on.
        printSignificance = True (default) or False.
# _____________________________________________________________________________
"""

import numpy as np
import pandas as pd
import scipy.stats as stats
import PointsWithConfidenceIntervals as plotCI


class ABAnalyzer(object):

    def __init__(self, df, confidenceInterval,
                 variableColumn, printSignificance=True):

        self.df = df
        self.confidenceInterval = confidenceInterval
        self.variableColumn = variableColumn
        self.printSignificance = printSignificance

        # Initialize ploting object.
        self.plot = plotCI.PlotWithCI(variableColumn)

    # _________________________________________________________________________
    def SignificanceTest(self, varDf, twoSided=True):
        """
        Takes in a dataframe and calculates the significance level. Assumes the
        variation name column is called "variation", the binomial probability
        is "p", and the experiment population is "population". twoSided refers
        to whether or not this is a two sided test or not.

        Output:
            significance
        """

        df = varDf

        variationNames = df.variation.unique()
        p = []
        n = []

        # Estimated mean, variance, and number of subjects.
        for variation in variationNames:

            p += [df.loc[df.variation == variation, 'p'].values]
            n += [df.loc[df.variation == variation, 'population'].values]

        # Pooled variance.
        pHat = (n[0]*p[0] + n[1]*p[1])/(n[0] + n[1])
        sHat2 = (pHat*(1 - pHat)*(1.0/n[0] + 1.0/n[1]))
        sHat = sHat2**0.5

        z = np.absolute((p[0] - p[1])/sHat)
        significance = stats.norm.cdf(z)

        # Adjust significance for a two sided test. For example, something that
        # claims 95% is actually 90% (it satisfies an alpha=10% but not
        #  alpha=5%).
        if twoSided:
            significance = 1 - (1 - significance)*2

        return significance

    # _________________________________________________________________________
    def DifferenceMeansAndCIs(self, df, variations):
        """
        Takes in a dataframe and calculates the sample mean and variance for
        each variation. Assumes the variation name column is called
        "variation", the binomial probability is "p", and the experiment
        population is "population".

        Output:
            estimatesDic = Dictionary of mean and confidence intervals for each
                           variation.
        """

        confidenceInterval = self.confidenceInterval

        variationNames = variations
        p = []
        n = []

        # Estimated mean, variance, and number of subjects.
        for variation in variationNames:

            p += [df.loc[df.variation == variation, 'p'].values]
            n += [df.loc[df.variation == variation, 'population'].values]

        pHat = (n[0]*p[0] + n[1]*p[1])/(n[0] + n[1])
        # Pooled variance.
        sHat2 = (pHat*(1 - pHat)*(1.0/n[0] + 1.0/n[1]))
        sHat = sHat2**0.5

        pDiff = p[1] - p[0]

        # We want confidence intervals, both sides, which means we need to
        # treat this like a two-sided z-test, so we'll look up the z value
        # for 97.5 if we want 95% confidence.
        a = 1 - (1 - confidenceInterval)/2

        # ppf is an inverse CDF function.
        ci = stats.norm.ppf(a)*sHat

        estimatesList = [pDiff, ci]

        return estimatesList

    # _________________________________________________________________________
    def MeansAndCIs(self, df, variations):
        """
        Takes in a dataframe and calculates the sample mean and variance for
        each variation. Assumes the variation name column is called
        "variation", the binomial probability is "p", and the experiment
         population is "population".

        Output:
            estimatesDic = Dictionary of mean and confidence intervals for each
                           variation.
        """

        confidenceInterval = self.confidenceInterval

        variationNames = variations
        estimatesDic = {}

        # Estimated mean, variance, and number of subjects.
        for variation in variationNames:

            p = df.loc[df.variation == variation, 'p'].values[0]
            n = df.loc[df.variation == variation, 'population'].values[0]

            sHat2 = p*(1 - p)/n
            sHat = sHat2**0.5

            # We want confidence intervals, both sides, which means we need to
            # treat this like a two-sided z-test, so we'll look up the z value
            # for 97.5 if we want 95% confidence.
            a = 1 - (1 - confidenceInterval)/2

            # ppf is an inverse CDF function.
            ci = stats.norm.ppf(a)*sHat

            estimatesDic[variation] = [p, ci]

        return estimatesDic

    # _________________________________________________________________________
    def _FindMissingVariables(self, missingValue=0):
        """
        Finds any variables that are in one variation but not in another; for
        instance when a new feature is added.

        Input:
            df = dataframe with columns: variableColumn, "variation", "p", and
                 "population".
            variableColumn = name of the variable column (ex: module, page,
                             etc).

        Output:
            Modified dataframe that contains the missing variables in the
            appropriate variation with 0 as the default value.
        """

        df = self.df
        variableColumn = self.variableColumn

        variations = df.variation.unique()
        allVariables = df[variableColumn].unique()

        for variant in variations:
            variables = df.loc[df.variation == variant,
                               variableColumn].unique()
            missingVariables = [x for x in allVariables if x not in variables]

            population = df.loc[df.variation == variant, 'population'].max()

            # Add zeros in.
            for missingVariable in missingVariables:
                columnNames = [variableColumn, 'p', 'variation', 'population']
                newRowDf = pd.DataFrame([[missingVariable,
                                          missingValue,
                                          variant,
                                          population]],
                                        columns=columnNames)

                df = df.append(newRowDf, ignore_index=True)

        return df

    # _________________________________________________________________________
    def ABChangeAnalysis(self, title, yMin=None, yMax=None):
        """
        Creates a bar plot with confidence intervals for each bar.

        Input:
            df = dataframe with the a "variation" column and a variable column.
            variableName = name of the variable column.

        Output:
            bar plot with confidence intervals.
        """

        df = self.df
        variableColumn = self.variableColumn

        # Find the different variable names in each variation, then add in any
        # that are missing in one variation or the other. Set the values to
        # zero for the missing variables.
        variations = df.variation.unique()
        allVariables = df[variableColumn].unique()

        df = self._FindMissingVariables()

        # -----------------------------------------------------------
        # Create bar plot and calculate significance - if turned on.

        diffRowsList = []

        # Iterate through each variable.
        for i, varName in enumerate(allVariables):

            columnList = ['p', 'variation', 'population']
            varDf = df.loc[df[variableColumn] == varName, columnList]

            if self.printSignificance:
                significance = self.SignificanceTest(varDf)
                print 'Significance for ' + varName + ' = ' \
                      + str(significance[0])

            # Calculate means and confidence intervals for the different
            # variations.
            pHat, ci = self.DifferenceMeansAndCIs(varDf, variations)
            diffRowsList.append([varName, pHat[0], ci[0]])

        # Calculate means and confidence intervals for differences between
        # variations.
        columns = [variableColumn, 'mean', 'confidence_interval']
        df = pd.DataFrame(diffRowsList, columns=columns)

        self.plot.CIPlot(df, title, 'Difference', yMin=yMin, yMax=yMax)

    # _________________________________________________________________________
    def ABMagnitudeAnalysis(self, title):
        """
        Creates a bar plot with confidence intervals for each bar.

        Input:
            df = dataframe with the a "variation" column and a variable column.
            variableName = name of the variable column.

        Output:
            bar plot with confidence intervals.
        """

        df = self.df
        variableColumn = self.variableColumn

        # Find the different variable names in each variation, then add in any
        # that are missing in one variation or the other. Set the values to
        # zero for the missing variables.
        variations = df.variation.unique()
        allVariables = df[variableColumn].unique()

        # -----------------------------------------------------------
        # Create bar plot and calculate significance - if turned on.

        absRowsList = []

        df = self._FindMissingVariables()

        # Iterate through each variable.
        for i, varName in enumerate(allVariables):

            columnList = ['p', 'variation', 'population']
            varDf = df.loc[df[variableColumn] == varName, columnList]

            # Calculate means and confidence intervals for the magnitudes of
            # each variable in each variation.
            resultsDic = self.MeansAndCIs(varDf, variations)

            for variation in resultsDic:
                p = resultsDic[variation][0]
                ci = resultsDic[variation][1]
                absRowsList.append([variation, varName, p, ci])

        # Calculate means and confidence intervals for each variable so that we
        # can know what maginitudes we're dealing with, not just the changes.
        columns = ['variation', variableColumn, 'mean', 'confidence_interval']
        df = pd.DataFrame(absRowsList, columns=columns)

        self.plot.ComparisonCIPlot(df, title, 'Magnitude')
