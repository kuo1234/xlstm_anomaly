"""Analytical correlation-only VAR construction; no generated observations."""
import numpy as np
from scipy.linalg import solve_discrete_lyapunov


def regimes(permutation_seed=None):
    p = np.roll(np.eye(8), 1, axis=0)
    if permutation_seed is not None:
        order = np.random.default_rng(permutation_seed).permutation(8)
        p = p[np.ix_(order, order)]
    a = .8*p
    sigma = tuple((1-r)*np.eye(8)+r*np.ones((8,8)) for r in (.1,.5))
    q = tuple(s-a@s@a.T for s in sigma)
    return a, sigma, q


def verify(permutation_seed=None):
    a, sigma, q = regimes(permutation_seed)
    assert max(abs(np.linalg.eigvals(a))) < 1
    solved = []
    residuals = []
    for s, innovation in zip(sigma,q):
        for matrix in (s, innovation):
            assert np.max(abs(matrix-matrix.T)) <= 1e-12
            assert np.linalg.eigvalsh(matrix).min() > 1e-8
        residual = np.max(abs(s-a@s@a.T-innovation))
        assert residual <= 1e-10
        residuals.append(float(residual))
        independent = solve_discrete_lyapunov(a,innovation)
        assert np.max(abs(independent-s)) <= 1e-10
        solved.append(independent)
    assert np.max(abs(np.diag(solved[0])-np.diag(solved[1]))) <= 1e-10
    means = [np.linalg.solve(np.eye(8)-a, np.zeros(8)) for _ in sigma]
    assert np.max(abs(means[0]-means[1])) <= 1e-10
    corr = [s/np.sqrt(np.outer(np.diag(s),np.diag(s))) for s in solved]
    delta = float(np.max(abs((corr[1]-corr[0])[~np.eye(8,dtype=bool)])))
    assert delta >= .2
    transition_error = 0.
    # Both directions, including recurring control.
    for start, innovation in ((sigma[0],q[1]),(sigma[1],q[0])):
        covariance = start.copy()
        for _ in range(256):
            covariance = a@covariance@a.T+innovation
            transition_error = max(transition_error,float(np.max(abs(np.diag(covariance)-1))))
            assert transition_error <= 1e-10
    return dict(lyapunov_max_residual=max(residuals), correlation_difference=delta,
                transition_diagonal_max_error=transition_error)
