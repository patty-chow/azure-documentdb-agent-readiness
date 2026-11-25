import numpy as np

def test_cos_sim_basic():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([1.0, 0.0, 0.0])
    sim = float((a @ b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    assert sim == 1.0
