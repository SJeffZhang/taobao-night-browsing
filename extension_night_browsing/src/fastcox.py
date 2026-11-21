"""Cox proportional hazards with Breslow ties, optional strata, and cluster-robust (Lin-Wei) covariance.

Scales to tens of millions of rows: rows are sorted once by (stratum, time desc) and risk-set sums are
cumulative sums over (stratum, time) groups. The Hessian uses sum_k d_k S2_k / S0_k = X' diag(w * C_A) X,
where C_A(t_i) = sum over event groups k in i's stratum with t_k <= t_i of d_k / S0_k.
"""
import numpy as np, pandas as pd
from scipy import stats


class FastCox:
    def __init__(self, time, event, X, strata=None):
        n = len(time)
        s = np.zeros(n, np.int64) if strata is None else pd.factorize(strata)[0].astype(np.int64)
        order = np.lexsort((-np.asarray(time, np.float64), s))
        self.order = order
        self.t = np.asarray(time, np.float64)[order]
        self.e = np.asarray(event, np.float64)[order]
        self.X = np.ascontiguousarray(np.asarray(X, np.float64)[order])
        self.s = s[order]
        new = np.ones(n, bool)
        new[1:] = (self.s[1:] != self.s[:-1]) | (self.t[1:] != self.t[:-1])
        self.gstart = np.flatnonzero(new)
        self.gid = np.cumsum(new) - 1
        self.gs = self.s[self.gstart]
        self.D = np.add.reduceat(self.e, self.gstart)
        self.SXe = np.add.reduceat(self.X * self.e[:, None], self.gstart)
        sn = np.ones(len(self.gstart), bool); sn[1:] = self.gs[1:] != self.gs[:-1]
        self.sstart = np.flatnonzero(sn)

    def _cum_within(self, a, reverse=False):
        """Cumulative sum over groups, reset at stratum boundaries (forward = descending time)."""
        a2 = a if a.ndim == 2 else a[:, None]
        if reverse:
            a2 = a2[::-1]
            starts = len(a) - 1 - np.r_[self.sstart[1:] - 1, len(a) - 1][::-1]
        else:
            starts = self.sstart
        c = np.cumsum(a2, axis=0)
        seg = np.repeat(np.arange(len(starts)), np.diff(np.r_[starts, len(a)]))
        off = np.vstack([np.zeros((1, a2.shape[1])), c[starts[1:] - 1]]) if len(starts) > 1 else np.zeros((1, a2.shape[1]))
        out = c - off[seg]
        if reverse:
            out = out[::-1]
        return out if a.ndim == 2 else out[:, 0]

    def _parts(self, beta):
        eta = self.X @ beta
        c = eta.max(); w = np.exp(eta - c)
        R0 = self._cum_within(np.add.reduceat(w, self.gstart))
        R1 = self._cum_within(np.add.reduceat(self.X * w[:, None], self.gstart))
        ev = self.D > 0
        ll = float(self.SXe.sum(0) @ beta - np.sum(self.D[ev] * (np.log(R0[ev]) + c)))
        xbar = R1 / R0[:, None]
        grad = self.SXe.sum(0) - (self.D[:, None] * xbar).sum(0)
        A = np.where(ev, self.D / R0, 0.0)
        CA = self._cum_within(A, reverse=True)[self.gid]
        H = -(self.X.T @ (self.X * (w * CA)[:, None]) - (xbar * self.D[:, None]).T @ xbar)
        return ll, grad, H, w, xbar, A

    def fit(self, max_iter=30, tol=1e-9):
        p = self.X.shape[1]; beta = np.zeros(p)
        ll, g, H, *_ = self._parts(beta)
        for it in range(max_iter):
            step = np.linalg.solve(-H, g)
            lam = 1.0
            while True:
                nb = beta + lam * step
                nll, ng, nH, *_ = self._parts(nb)
                if (np.isfinite(nll) and nll >= ll - 1e-12) or lam < 1e-6:
                    break
                lam /= 2
            done = abs(nll - ll) < tol * (1 + abs(ll))
            beta, ll, g, H = nb, nll, ng, nH
            if done:
                break
        self.beta, self.loglik, self.n_iter, self.H = beta, ll, it + 1, H
        self.converged = bool(done and np.all(np.isfinite(beta)))
        if not self.converged:
            raise RuntimeError(f'FastCox did not converge after {it + 1} iterations (loglik {ll})')
        return self

    def robust_cov(self, groups):
        """Lin-Wei sandwich, clustered by `groups` (original row order), CR1 small-sample factor."""
        ll, g, H, w, xbar, A = self._parts(self.beta)
        CA = self._cum_within(A, reverse=True)[self.gid]
        CB = self._cum_within(A[:, None] * xbar, reverse=True)[self.gid]
        U = self.e[:, None] * (self.X - xbar[self.gid]) - w[:, None] * (self.X * CA[:, None] - CB)
        code = pd.factorize(np.asarray(groups)[self.order])[0]; G = code.max() + 1
        S = np.column_stack([np.bincount(code, weights=U[:, j], minlength=G) for j in range(U.shape[1])])
        Hi = np.linalg.inv(-H)
        self.cov = Hi @ (S.T @ S) @ Hi * (G / (G - 1)); self.n_clusters = int(G)
        self.naive_cov = Hi
        return self.cov

    def summary(self, names):
        se = np.sqrt(np.diag(self.cov)); z = self.beta / se
        return pd.DataFrame({'term': names, 'coef': self.beta, 'se': se, 'hr': np.exp(self.beta),
                             'hr_ci_low': np.exp(self.beta - 1.96 * se), 'hr_ci_high': np.exp(self.beta + 1.96 * se),
                             'p': 2 * stats.norm.sf(np.abs(z))})
