import sympy as sp


def parse_function(expr: str):
	z = sp.symbols("z")

	try:
		expr = expr.replace("^", "**")
		sym_expr = sp.sympify(expr)
		f = sp.lambdify(z, sym_expr, modules=["numpy"])
		latex_str = sp.latex(sym_expr)
		return f, latex_str

	except Exception as e:
		print("Parse error:", e)
		return None, None
