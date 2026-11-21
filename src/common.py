"""Shared fixed-effect helpers: high-dimensional FE absorption + two-way clustered covariance."""
import time
import numpy as np, pandas as pd
import pyhdfe  # noqa: E402  (installed via requirements.txt)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def cluster_cov(X, e, groups, k_total):
    """Two-way cluster-robust covariance (Cameron-Gelbach-Miller) with PSD repair."""
    n, k = X.shape
    bread = np.linalg.inv(X.T @ X)
    score = X * e[:, None]

    def meat(g):
        code = pd.factorize(g, sort=False)[0]; G = int(code.max() + 1)
        sums = np.column_stack([np.bincount(code, weights=score[:, j], minlength=G) for j in range(k)])
        return sums.T @ sums * (G / (G - 1)) * ((n - 1) / (n - k_total)), G

    M, G = meat(groups[0]); counts = [G]
    if len(groups) == 2:
        M2, G2 = meat(groups[1])
        inter = groups[0].astype(np.int64) * (1 << 32) + groups[1].astype(np.int64)
        M12, G12 = meat(inter)
        M = M + M2 - M12; counts += [G2, G12]
    cov = bread @ M @ bread; cov = (cov + cov.T) / 2
    eig = np.linalg.eigvalsh(cov)
    if eig.min() < 0:  # standard PSD repair for two-way clustering
        w, v = np.linalg.eigh(cov); cov = v @ np.diag(np.clip(w, 0, None)) @ v.T
    return cov, counts, float(eig.min())
