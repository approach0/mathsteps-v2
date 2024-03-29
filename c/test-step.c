#include <stdio.h>
#include <float.h>

#include "vt100-code.h"
#include "mhook.h"
#include "parser.h"
#include "step.h"
#include "common-axioms.h"
#include "render-math.h"

float g_test_last_val = -FLT_MAX;

#define TEST(_tex) \
	test(_tex, scanner)

#define TEST_RESET \
	g_test_last_val = -FLT_MAX

static void test(const char *tex, void *scanner)
{
	struct optr_node *tree = parser_parse(scanner, tex);

	if (tree) {
		float val = state_value__neg_complexity(tree);
		printf("[%.3f] %s\n", val, tex);
		optr_release(tree);

		if (val > g_test_last_val)
			printf(C_GREEN "-- pass.\n" C_RST);
		else
			printf(C_RED "-- failed.\n" C_RST);
		g_test_last_val = val;
	}
}

static void test__state_value(void *scanner)
{
	TEST("13 + 1");
	TEST("10 + 4");
	TEST_RESET;

	TEST("0 + 0 + 0");
	TEST("0");
	TEST_RESET;

	TEST("10 \\cdot x + 15 = 15");
	TEST("10 \\cdot x + 15 -15 = 0");
	TEST_RESET;

	TEST("100 \\times 25");
	TEST("2500");
	TEST_RESET;

	TEST("2(x+y)+1+2");
	TEST("2x+2y+3+4");
	TEST_RESET;

	TEST("-3");
	TEST("3");
	TEST_RESET;

	TEST("7 + 5");
	TEST("10 + 2");
	TEST_RESET;

	TEST("6 - 3");
	TEST("0 + 3");
	TEST_RESET;

	TEST("\\sqrt{27}");
	TEST("3\\sqrt{3}");
	TEST_RESET;

	TEST("\\sqrt{59049}");
	TEST("81\\sqrt{9}");
	TEST_RESET;

	TEST("-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2} + x \\times \\frac{50}{x + y} = 0");
	TEST("50 \\times x + (x + y) \\times (-x \\times 0.391 - 629 - x^{2} \\times 2 + y^{2}) = (x + y) \\times 0");
	TEST("x \\times 50 + (x + y) \\times (-629 - x^{2} \\times 2 + y^{2}) + x^{2} \\times 0.391 + x \\times 0.391 \\times y = 0");
	TEST("x \\times 50 + x^{2} \\times 0.391 + x \\times 0.391 \\times y + 2 \\times x^{2} \\times x + 2 \\times x^{2} \\times y - 629 \\times x - 629 \\times y + y^{2} \\times x + y^{2} \\times y = 0");
	TEST_RESET;

    TEST("4 - 3 \\frac{1}{2}");
    TEST("-\\frac{1}{2}");
    TEST_RESET;

    TEST("-13 \\times \\frac{2}{3} - 0.34 \\times \\frac{2}{7} - \\frac{1}{3} \\times 13 - \\frac{5}{7} \\times 0.34");
    TEST("(-\\frac{2}{7}-\\frac{5}{7}) \\times 0.34 + (-\\frac{2}{3} - \\frac{1}{3}) \\times 13");
    TEST("(-1) \\times 0.34 + (-\\frac{2}{3} - \\frac{1}{3}) \\times 13");
    TEST_RESET;
}

#define MAX_STEPS 10

static void test__next_steps(void *scanner, struct Axiom **axioms, int m)
{
	struct Step steps[MAX_STEPS] = {0};

	char original_tex[] = "1 + 2 + 3 + 4 \\cdot 2 + 0";
	struct optr_node *tree = parser_parse(scanner, original_tex);

	steps[0] = tex2step(original_tex);
	int n = possible_next_steps(tree, axioms, m, steps + 1, MAX_STEPS);

	render_steps_to_html_file(steps, n + 1, 1);

	printf("[origin] %s\n", original_tex);
	printf("%d possible_next_steps: \n", n);
	for (int i = 1; i < n + 1; i++) {
		printf("[step %d] ", i);
		print_step(&steps[i], 0);
		optr_release(steps[i].tree);
	}

	optr_release(tree);
}

static void test__baseline(void *scanner, struct Axiom **axioms, int m)
{
	struct Step steps[MAX_STEPS];

	//char original_tex[] = "3 + 2 + 7 + 4 \\cdot 2";
	char original_tex[] = "\\frac{10 + 1}{2} \\times 2 + 3";
	struct optr_node *tree = parser_parse(scanner, original_tex);

	int n = mathsteps_baseline(tree, axioms, m, steps, MAX_STEPS);

	render_steps_to_html_file(steps, n, 0);

	for (int i = 0; i < n; i++) {
		printf("[step %d] ", i);
		print_step(&steps[i], 0);

		optr_release(steps[i].tree);
	}

	optr_release(tree);
}

int main()
{
	int m = 0;
	struct Axiom **axioms = common_axioms(&m);
	void *scanner = parser_new_scanner();

	//render_tex_to_html_file("a + \\frac b c", "output.html");
	//test__state_value(scanner);
	test__next_steps(scanner, axioms, m);
	//test__baseline(scanner, axioms, m);

	parser_dele_scanner(scanner);
	common_axioms_free(axioms, m);

	mhook_print_unfree();
	return 0;
}
