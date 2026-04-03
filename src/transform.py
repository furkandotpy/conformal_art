from collections.abc import Callable

import numpy as np


def warp_image_rgb(
	img_np: np.ndarray,
	f,
	*,
	plane_lo: float = -2.0,
	plane_hi: float = 2.0,
	iterations: int = 5,
	damping: float = 0.5,
	progress: Callable[[int], None] | None = None,
) -> np.ndarray:
	def report(p: int) -> None:
		if progress is not None:
			progress(max(0, min(100, p)))

	report(0)
	height, width = img_np.shape[:2]

	x = np.linspace(plane_lo, plane_hi, width)
	y = np.linspace(plane_lo, plane_hi, height)
	X, Y = np.meshgrid(x, y)
	W = X + 1j * Y
	report(8)

	Z = W.copy()

	for i in range(iterations):
		try:
			Z = Z - (f(Z) - W) * damping
		except Exception:
			break
		report(8 + int(82 * (i + 1) / iterations))

	span = plane_hi - plane_lo
	zx = np.clip(((Z.real - plane_lo) / span * (width - 1)).astype(int), 0, width - 1)
	zy = np.clip(((Z.imag - plane_lo) / span * (height - 1)).astype(int), 0, height - 1)
	report(96)

	out = img_np[zy, zx]
	report(100)
	return out
