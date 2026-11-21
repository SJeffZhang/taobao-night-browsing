"""Check FastCox against statsmodels PHReg (Breslow) and lifelines (cluster-robust) on real-data subsamples."""
import json, time, warnings
import numpy as np, pandas as pd
from adv_common import RES, load
from fastcox import FastCox
from statsmodels.duration.hazard_regression import PHReg
from lifelines import CoxPHFitter
import importlib

s = importlib.import_module('06_survival')
warnings.filterwarnings('ignore')


def main():
    d = s.prep(load([(0, 0)]))
    cols = s.DUM + s.CTRL + s.DAYD
    x = d.sample(40000, random_state=3).reset_index(drop=True)
    x['dur_h'] = np.round(x.dur_h, 2)  # force many ties so the Breslow tie handling is exercised
    out = {'n': len(x), 'events': int(x.event.sum()), 'distinct_event_times': int(x.dur_h[x.event == 1].nunique())}
    fc = FastCox(x.dur_h, x.event, x[cols]).fit(); fc.robust_cov(x.user_id)
    sm = PHReg(x.dur_h.to_numpy(), x[cols].to_numpy(float), status=x.event.to_numpy(), ties='breslow').fit(groups=x.user_id.to_numpy())
    out['vs_statsmodels'] = {'max_abs_coef_diff': float(np.abs(fc.beta - sm.params).max()),
                             'loglik_diff': float(fc.loglik - sm.llf),
                             'robust_se_ratio_range': [float((np.sqrt(np.diag(fc.cov)) / sm.bse).min()), float((np.sqrt(np.diag(fc.cov)) / sm.bse).max())]}
    xs = x.copy(); xs['st'] = xs.user_id % 3
    fcs = FastCox(xs.dur_h, xs.event, xs[cols], strata=xs.st).fit()
    sms = PHReg(xs.dur_h.to_numpy(), xs[cols].to_numpy(float), status=xs.event.to_numpy(), ties='breslow', strata=xs.st.to_numpy()).fit()
    out['stratified_vs_statsmodels'] = {'max_abs_coef_diff': float(np.abs(fcs.beta - sms.params).max()),
                                        'loglik_diff': float(fcs.loglik - sms.llf)}
    y = x.copy(); y['dur_h'] = y.dur_h + np.random.default_rng(1).uniform(0, 1e-4, len(y))  # no ties: Breslow = Efron
    fu = FastCox(y.dur_h, y.event, y[cols]).fit(); fu.robust_cov(y.user_id)
    lf = CoxPHFitter().fit(y[['dur_h', 'event', 'user_id'] + cols], 'dur_h', 'event', cluster_col='user_id')
    out['no_ties_vs_lifelines_cluster'] = {'max_abs_coef_diff': float(np.abs(fu.beta - lf.params_[cols].to_numpy()).max()),
                                           'robust_se_ratio_range': [float((np.sqrt(np.diag(fu.cov)) / lf.standard_errors_[cols].to_numpy()).min()),
                                                                     float((np.sqrt(np.diag(fu.cov)) / lf.standard_errors_[cols].to_numpy()).max())]}
    big = s.prep(load([(0, 4)]))
    t = time.time(); FastCox(big.dur_h, big.event, big[cols]).fit().robust_cov(big.user_id)
    out['timing_rows'] = len(big); out['timing_s'] = time.time() - t
    (RES / 'fastcox_verification.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
