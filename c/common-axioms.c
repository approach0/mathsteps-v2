#include <stdio.h>
#include <stdlib.h>

#include "dynamic-axioms.h"
#include "common-axioms.h"

struct Axiom **common_axioms(int *n)
{
	struct Axiom **ret = malloc(sizeof(struct Axiom*) * MAX_AXIOMS);
	int cnt = 0;

	{
		struct Axiom *a = axiom_new("Cancel term");

		axiom_add_rule(a, "# (n - n)", "0", NULL);
		axiom_add_rule(a, "# (a - \\frac{a}{1})", "0", NULL);
		axiom_add_rule(a, "# (-a + \\frac{a}{1})", "0", NULL);

		axiom_add_test(a, "-(2 - 2)");
		axiom_add_test(a, "\\frac{a^{2}}{1} - a^{2}");

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Multiplying zero result in zero");

		axiom_add_rule(a, "# 0 \\cdot *{a}", "0", NULL);
		axiom_add_rule(a, "#\\frac{#0}{x}", "0", NULL);

		axiom_add_test(a, "\\frac{0 \\times b^{2} \\times a}{2}");
		axiom_add_test(a, "a \\times b^{2} \\times 0");
		axiom_add_test(a, "- a \\times 0 \\times b^{2}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Eliminate zero terms");

		axiom_add_rule(a, "#(#0 + n)", "n", NULL);

		axiom_add_test(a, "0+3+2");
		axiom_add_test(a, "-(0+3+2)");

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Eliminate unit factor");

		axiom_add_rule(a, "# 1 \\times *{x}", "#1 *{x}", NULL);

		axiom_add_test(a, "1 \\cdot 4");
		axiom_add_test(a, "-4 \\times 1");
		axiom_add_test(a, "- (a+b) \\cdot 1");
		axiom_add_test(a, "- 1 \\cdot 4 \\cdot 1");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Root-power cancels out");

		axiom_add_rule(a, "#(#\\sqrt{x})^{2}", "#1 x", NULL);

		axiom_add_test(a, "-(\\sqrt{x})^{2}");
		axiom_add_test(a, "+(-\\sqrt{x})^{2}");
		axiom_add_test(a, "(\\sqrt{x})^{2}");
		axiom_add_test(a, "-(-\\sqrt{x})^{2}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("One squared is still one");

		axiom_add_rule(a, "#(# 1)^{2}", "#1 1", NULL);

		axiom_add_test(a, "-(1)^{2}");
		axiom_add_test(a, "+(-1)^{2}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Negative squared is its positive squared");

		axiom_add_rule(a, "#(-a)^{2}", "#1 a^{2}", NULL);

		axiom_add_test(a, "(-3)^{2} - (6 \\div (-\\frac{2}{3})^{2}) -  (-2)^{2}");

		a->is_root_sign_reduce = 1;
#ifndef FULL_COMMON_AXIOMS
		a->is_strict_simplify = 1;
#endif

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Division to inverse multiplication");

		axiom_add_rule(a, "# (#\\frac{w}{x}) \\div (# \\frac{y}{z})", "#0 \\frac{wz}{xy}", NULL);
		axiom_add_rule(a, "# x \\div (# \\frac{y}{z})", "#0 \\frac{xz}{y}", NULL);

		axiom_add_test(a, "- 3 \\div (-\\frac{1}{2})");
		axiom_add_test(a, "\\frac{2}{3} \\div \\frac{4}{5}");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Division to fraction form");

		axiom_add_rule(a, "# (#x) \\div (#y)", "#0 \\frac{x}{y}", NULL);

		axiom_add_test(a, "-1 \\div 2x + 3");
		axiom_add_test(a, "6 \\div (-3)");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Cancel factor with denominator");

		axiom_add_rule(a, "# x \\times \\frac{a}{x}", "#1 a", NULL);

		axiom_add_test(a, "-3 \\times \\frac{-2}{3}");
		axiom_add_test(a, "3 \\times \\frac{-2}{3}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Absolute operator distribution");

		axiom_add_rule(a,
			"# \\left| # \\frac{a}{b} \\right|",
			"#1 \\frac{\\left| a \\right|}{\\left| b \\right|}",
		NULL);

		axiom_add_test(a, "\\left| - \\frac{1}{2} \\right|");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Square root distribution");

		axiom_add_rule(a,
			"# \\sqrt{\\frac{a}{b}}",
			"#1 \\frac{\\sqrt{a}}{\\sqrt{b}}",
		NULL);

		axiom_add_test(a, "- \\sqrt{\\frac{1}{2}}");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Cancel common factor in a fraction");

		axiom_add_rule(a,
			"# \\frac{# x *{i} }{# x *{j} }",
			"#1 \\frac{#2 *{i}}{#3 *{j}}",
		NULL);
		axiom_add_rule(a,
			"# \\frac{# x }{# x *{i} }",
			"#0 \\frac{1}{*{i}}",
		NULL);
		axiom_add_rule(a,
			"# \\frac{# x *{i} }{# x }",
			"#0 *{i}",
		NULL);
		axiom_add_rule(a,
			"# \\frac{# x}{# x}",
			"#0 1",
		NULL);

		axiom_add_test(a, "- \\frac{by}{ay}");
		axiom_add_test(a, "- \\frac{-bx}{xa}");
		axiom_add_test(a, "- \\frac{-bxy}{-xay}");
		axiom_add_test(a, "- \\frac{-x}{ax}");
		axiom_add_test(a, "\\frac{-x}{xay}");
		axiom_add_test(a, "\\frac{3xy}{-xy}");
		axiom_add_test(a, "-\\frac{-a}{-a}");
		axiom_add_test(a, "\\frac{-(a + b)}{a + b}");
		axiom_add_test(a, "-\\frac{-(3 + \\frac{1}{3})}{-(3 + \\frac{1}{3}) \\times x}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Multiplication to square form");

		axiom_add_rule(a,
			"#(#X)(#X)",
			"#0 X^{2}",
		NULL);

		axiom_add_test(a, "xx");

		a->is_root_sign_reduce = 1;
		a->is_symmetric_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_add();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_mul();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_pow();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_sqrt();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_abs();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_fraction_add_decimal();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_simplify_fraction();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_fraction_collapse();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Equation shifting");

		axiom_add_rule(a,
			"x = z",
			"x - z = 0",
		NULL);

		axiom_add_test(a, "1 - 2 = -3 + 5");
		axiom_add_test(a, "ax = bx");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Merge term");
		struct Rule *r;

		r = axiom_add_rule(a,
			"#(x + x)",
			"2x",
		NULL);
		r->is_symmetric_reduce = 1;

		axiom_add_rule(a,
			"#(#x # kx)",
			"(#2 1 #3 k) x",
		NULL);

		axiom_add_rule(a,
			"#(#x # xk)",
			"(#2 1 #3 k) x",
		NULL);

		axiom_add_rule(a,
			"#(#x *{a} # x *{b})",
			"(#2 *{a} #3 *{b}) x",
		NULL);

		axiom_add_test(a, "a + a");
		axiom_add_test(a, "-a - a");
		axiom_add_test(a, "x^{2} + x^{2}");
		axiom_add_test(a, "-(-x + 3x)");
		axiom_add_test(a, "-x + 3x - 1x");
		axiom_add_test(a, "-(-x + 3x - 1x)");
		axiom_add_test(a, "x - 3 \\cdot x");
		axiom_add_test(a, "yx^{2} - x^{3}y");

		a->is_root_sign_reduce = 0;
		a->is_allow_complication = 1;
#ifndef FULL_COMMON_AXIOMS
		a->is_disabled = 1;
#endif

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Reverse the sign");

		axiom_add_rule(a, "+(x + *{a})", "-(-x - *{a})", NULL);

		axiom_add_test(a, "1 + 2 + 3");
		axiom_add_test(a, "(-a - b) x");
		axiom_add_test(a, "(-a + b)x");
		axiom_add_test(a, "(-a - b - c) x");
		axiom_add_test(a, "-3-\\frac{4}{17}");
		axiom_add_test(a, "(-3-\\frac{4}{17}) x");
		axiom_add_test(a, "(-3-\\frac{4}{17}) x + y");
		axiom_add_test(a, "(a - b - c) x");

		a->is_root_sign_reduce = 1;
		a->is_strict_simplify = 1;
#ifndef FULL_COMMON_AXIOMS
		a->is_disabled = 1;
#endif

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Simplify nested fraction");

		axiom_add_rule(a, "#\\frac{#\\frac{x}{y}}{#\\frac{a}{b}}", "#0 \\frac{bx}{ay}", NULL);
		axiom_add_rule(a, "#\\frac{#1}{#\\frac{x}{y}}", "#0 \\frac{y}{x}", NULL);
		axiom_add_rule(a, "#\\frac{#\\frac{x}{y}}{#1}", "#0 \\frac{x}{y}", NULL);
		axiom_add_rule(a, "#\\frac{a}{#\\frac{x}{y}}", "#0 \\frac{ay}{x}", NULL);
		axiom_add_rule(a, "#\\frac{#\\frac{x}{y}}{a}", "#0 \\frac{x}{ay}", NULL);

		axiom_add_test(a, "-\\frac{-\\frac{4}{3}}{-\\frac{4}{3}}");
		axiom_add_test(a, "-\\frac{-\\frac{4}{3}}{\\frac{1}{2}}");
		axiom_add_test(a, "-\\frac{-\\frac{4}{3}}{x}");
		axiom_add_test(a, "-\\frac{4}{-\\frac{4}{3}}");
		axiom_add_test(a, "\\frac{-8}{\\frac{1}{4}}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_fraction_add();
		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Fraction multiplication");
		struct Rule *r;

		r = axiom_add_rule(a, "#\\frac{#1}{x} \\frac{#1}{y}", "#0 \\frac{1}{xy}", NULL);
		r->is_symmetric_reduce = 1;

		axiom_add_rule(a, "#\\frac{#1}{x} \\frac{y}{#1}", "#0 \\frac{y}{x}", NULL);

		r = axiom_add_rule(a, "#\\frac{x}{#1} \\frac{y}{#1}", "#0 xy", NULL);
		r->is_symmetric_reduce = 1;

		r = axiom_add_rule(a, "#\\frac{a}{c} \\frac{b}{d}", "#1 \\frac{ab}{cd}", NULL);
		r->is_symmetric_reduce = 1;

		axiom_add_test(a, "-\\frac{1}{-2} \\cdot \\frac{-1}{2}");
		axiom_add_test(a, "-\\frac{1}{-2} \\cdot \\frac{-2}{1}");
		axiom_add_test(a, "-\\frac{2}{1} \\cdot \\frac{-2}{1}");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Ignore divided-by-one");

		axiom_add_rule(a, "#\\frac{k}{#1}", "#0 k", NULL);

		axiom_add_test(a, "\\frac{3}{-1}");

		a->is_root_sign_reduce = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Distribute power to factors");

		axiom_add_rule(a, "# (# a *{b})^{k}", "#1 (#2 a)^{k} \\times (*{b})^{k}", NULL);

		axiom_add_test(a, "-(-3xy)^{2}");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Distribute power to fraction numbers");

		axiom_add_rule(a, "#(-\\frac{#a}{#b})^{k}", "#1 (-1)^{k} \\frac{(#2 a)^{k}}{(#3 b)^{k}}", NULL);
		axiom_add_rule(a, "#(+\\frac{#a}{#b})^{k}", "#1 \\frac{(#2 a)^{k}}{(#3 b)^{k}}", NULL);

		axiom_add_test(a, "(-\\frac{-2}{3})^{2}");
		axiom_add_test(a, "-(\\frac{-2}{3})^{2}");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Multiply factor into numerator");

		axiom_add_rule(a, "# a \\times \\frac{# 1}{b}", "#0 \\frac{a}{b}", NULL);
		axiom_add_rule(a, "# a \\times \\frac{# c}{b}", "#0 \\frac{ac}{b}", NULL);

		axiom_add_test(a, "-\\frac{-1}{3} \\times 12");
		axiom_add_test(a, "12 \\cdot \\frac{3}{2}");
		axiom_add_test(a, "\\frac{9}{4} \\times (1 - \\frac{3}{4})");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;

		ret[cnt++] = a;
	}

	{
		struct Axiom *a = axiom_new("Multiplication distributive law");

		axiom_add_rule(a, "#a(x + *{w})", "#1 ax #1 a *{w}", NULL);

		axiom_add_test(a, "3(a + b)");
		axiom_add_test(a, "3(a + b + c) + 1");
		axiom_add_test(a, "(a - b)(-2)");
		axiom_add_test(a, "2(a + 3(b + c))");

		a->is_root_sign_reduce = 1;
		a->is_allow_complication = 1;
		a->max_output_num = 4;

		ret[cnt++] = a;
	}

//	{
//		struct Axiom *a = axiom_fraction_add_int();
//		ret[cnt++] = a;
//	}

	*n = cnt;
	return ret;
}

void common_axioms_free(struct Axiom *axioms[], int n)
{
	for (int i = 0; i < n; i++)
		axiom_free(axioms[i]);
	free(axioms);
}
