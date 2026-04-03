import numpy as np


def create_grid(lo: float = -2.0, hi: float = 2.0, n: int = 50):
	x = np.linspace(lo, hi, n)
	y = np.linspace(lo, hi, n)

	lines = []

	for xi in x:
		lines.append(xi + 1j * y)

	for yi in y:
		lines.append(x + 1j * yi)

	return lines
