import numpy as np
from ngboost.ngboost import NGBoost
from ngboost.distns import RegressionDistn, ClassificationDistn
from ngboost.distns import Bernoulli, Normal, LogNormal
from ngboost.scores import LogScore
from ngboost.learners import default_tree_learner
from sklearn.base import BaseEstimator

class NGBRegressor(NGBoost, BaseEstimator):
    '''
    Constructor for NGBoost regression models.

    NGBRegressor is a wrapper for the generic NGBoost class that facilitates regression. Use this class if you want to predict an outcome that could take an infinite number of (ordered) values.

    Parameters:
        Dist              : assumed distributional form of Y|X=x. A distribution from ngboost.distns, e.g. Normal
        Score             : rule to compare probabilistic predictions P̂ to the observed data y. A score from ngboost.scores, e.g. LogScore
        Base              : base learner to use in the boosting algorithm. Any instantiated sklearn regressor, e.g. DecisionTreeRegressor()
        natural_gradient  : logical flag indicating whether the natural gradient should be used
        n_estimators      : the number of boosting iterations to fit
        learning_rate     : the learning rate
        minibatch_frac    : the percent subsample of rows to use in each boosting iteration
        verbose           : flag indicating whether output should be printed during fitting
        verbose_eval      : increment (in boosting iterations) at which output should be printed
        tol               : numerical tolerance to be used in optimization
        random_state      : seed for reproducibility. See https://stackoverflow.com/questions/28064634/random-state-pseudo-random-number-in-scikit-learn
    Output:
        An NGBRegressor object that can be fit.
    '''

    def __init__(self,
                 Dist=Normal,
                 Score=LogScore,
                 Base=default_tree_learner,
                 natural_gradient=True,
                 n_estimators=500,
                 learning_rate=0.01,
                 minibatch_frac=1.0,
                 verbose=True,
                 verbose_eval=100,
                 tol=1e-4,
                 random_state=None):
        assert issubclass(Dist, RegressionDistn), f'{Dist.__name__} is not useable for regression.'

        if not hasattr(Dist, 'scores'): # user is trying to use a dist that only has censored scores implemented
            Dist = Dist.uncensor_score_implementation(Score) # implement the uncensored version of the score and make the dist aware of it

        super().__init__(Dist, Score, Base, natural_gradient, n_estimators, learning_rate,
                         minibatch_frac, verbose, verbose_eval, tol, random_state)

class NGBClassifier(NGBoost, BaseEstimator):
    '''
    Constructor for NGBoost classification models.

    NGBRegressor is a wrapper for the generic NGBoost class that facilitates classification. Use this class if you want to predict an outcome that could take a discrete number of (unordered) values.

    Parameters:
        Dist              : assumed distributional form of Y|X=x. A distribution from ngboost.distns, e.g. Bernoulli
        Score             : rule to compare probabilistic predictions P̂ to the observed data y. A score from ngboost.scores, e.g. LogScore
        Base              : base learner to use in the boosting algorithm. Any instantiated sklearn regressor, e.g. DecisionTreeRegressor()
        natural_gradient  : logical flag indicating whether the natural gradient should be used
        n_estimators      : the number of boosting iterations to fit
        learning_rate     : the learning rate
        minibatch_frac    : the percent subsample of rows to use in each boosting iteration
        verbose           : flag indicating whether output should be printed during fitting
        verbose_eval      : increment (in boosting iterations) at which output should be printed
        tol               : numerical tolerance to be used in optimization
        random_state      : seed for reproducibility. See https://stackoverflow.com/questions/28064634/random-state-pseudo-random-number-in-scikit-learn
    Output:
        An NGBRegressor object that can be fit.
    '''
    def __init__(self,
                 Dist=Bernoulli,
                 Score=LogScore,
                 Base=default_tree_learner,
                 natural_gradient=True,
                 n_estimators=500,
                 learning_rate=0.01,
                 minibatch_frac=1.0,
                 verbose=True,
                 verbose_eval=100,
                 tol=1e-4,
                 random_state=None):
        assert issubclass(Dist, ClassificationDistn), f'{Dist.__name__} is not useable for classification.'
        super().__init__(Dist, Score, Base, natural_gradient, n_estimators, learning_rate,
                         minibatch_frac, verbose, verbose_eval, tol, random_state)

    def predict_proba(self, X, max_iter=None):
        return self.pred_dist(X, max_iter=max_iter).class_probs()

    def staged_predict_proba(self, X, max_iter=None):
        return [dist.class_probs() for dist in self.staged_pred_dist(X, max_iter=max_iter)]

class NGBSurvival(NGBoost, BaseEstimator):
    '''
    Constructor for NGBoost survival models.

    NGBRegressor is a wrapper for the generic NGBoost class that facilitates survival analysis. Use this class if you want to predict an outcome that could take an infinite number of (ordered) values, but right-censoring is present in the observed data.

     Parameters:
        Dist              : assumed distributional form of Y|X=x. A distribution from ngboost.distns, e.g. LogNormal
        Score             : rule to compare probabilistic predictions P̂ to the observed data y. A score from ngboost.scores, e.g. LogScore
        Base              : base learner to use in the boosting algorithm. Any instantiated sklearn regressor, e.g. DecisionTreeRegressor()
        natural_gradient  : logical flag indicating whether the natural gradient should be used
        n_estimators      : the number of boosting iterations to fit
        learning_rate     : the learning rate
        minibatch_frac    : the percent subsample of rows to use in each boosting iteration
        verbose           : flag indicating whether output should be printed during fitting
        verbose_eval      : increment (in boosting iterations) at which output should be printed
        tol               : numerical tolerance to be used in optimization
        random_state      : seed for reproducibility. See https://stackoverflow.com/questions/28064634/random-state-pseudo-random-number-in-scikit-learn
    Output:
        An NGBRegressor object that can be fit.
    '''
    def __init__(self,
                 Dist=LogNormal,
                 Score=LogScore,
                 Base=default_tree_learner,
                 natural_gradient=True,
                 n_estimators=500,
                 learning_rate=0.01,
                 minibatch_frac=1.0,
                 verbose=True,
                 verbose_eval=100,
                 tol=1e-4,
                 random_state=None):

        assert issubclass(Dist, RegressionDistn), f'{Dist.__name__} is not useable for regression.'
        if not hasattr(Dist,'censored_scores'):
            raise ValueError(f'The {Dist.__name__} distribution does not have any censored scores implemented.')

        # assert issubclass(Dist, RegressionDistn), f'{Dist.__name__} is not useable for survival.'
        super().__init__(Dist.censor(), Score, Base, natural_gradient, n_estimators, learning_rate,
                         minibatch_frac, verbose, verbose_eval, tol, random_state)

    def build_Y(T,E):
        if T is None or E is None:
            return None
        Y = np.empty(dtype=[('Event', np.bool), ('Time', np.float64)],
                     shape=T.shape[0])
        Y['Event'] = (1-E).astype(bool)
        Y['Time'] = T.astype(float)
        return Y

    def fit(self, X, T, E, X_val = None, T_val = None, E_val = None, **kwargs):
        '''
        Fits an NGBoost survival model to the data. For additional parameters see ngboost.NGboost.fit

        Parameters:
            X                       : numpy array of predictors (n x p)
            T                       : numpy array of times to event or censoring (n). Should be floats 
            E                       : numpy array of event indicators (n). E[i] = 1 <=> T[i] is the time of an event, else censoring time
            T_val                   : validation-set times, if any
            E_val                   : validation-set event idicators, if any
        '''

        super().fit(X, build_Y(T, E), X_val = X_val, Y_val = build_Y(T_val, E_val), **kwargs)
