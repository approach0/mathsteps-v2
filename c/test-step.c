#include <stdio.h>
#include <float.h>

#include "vt100-code.h"
#include "mhook.h"
#include "parser.h"
#include "step.h"

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

static void test__state_value()
{
	void *scanner = parser_new_scanner();

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

	parser_dele_scanner(scanner);
}

int main()
{
	//test__state_value();

	mhook_print_unfree();
	return 0;
}
