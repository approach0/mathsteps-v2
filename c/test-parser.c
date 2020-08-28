#include "mhook.h"
#include "parser.h"

wchar_t mbc2wc(const char *);

int print_code_table()
{
	printf("=== token code table ===\n");

#define PRINT_WCHAR_CODE(_char) \
	tmp = mbc2wc(_char); \
	printf("%s: 0x%x\n", _char, (unsigned int)tmp);

	wchar_t tmp;
	PRINT_WCHAR_CODE("=");
	PRINT_WCHAR_CODE("+");
	PRINT_WCHAR_CODE("÷");
	PRINT_WCHAR_CODE("×");
	PRINT_WCHAR_CODE("^");
	PRINT_WCHAR_CODE("/");
	PRINT_WCHAR_CODE("√");
	PRINT_WCHAR_CODE("ǁ");

	return 0;
}

int test_parsing()
{
	struct optr_node *root;
	void *scanner = parser_new_scanner();
	if (NULL == scanner)
		return 1;

	//char test[] = "0 - (1 + 2)";
	//char test[] = "2(-3)(-4)";
	//char test[] = "-(-2(-3)) 5";

	//char test[] = "a[c \\div 2b] = -(-5 + 1 - 3.14) + A \\times x - 2ax";
	//char test[] = "a^{1 + 2}";
	//char test[] = "\\frac 12 a";
	//char test[] = "12 + x *{12}";
	//char test[] = "\\sqrt 12 + 3";
	//char test[] = "\\sqrt 12 + 3";
	//char test[] = "\\left | 1 - 2 \\right|";
	char test[] = "# \\frac{a}{#2} # x + 1 - 2";

	printf("TeX: %s\n", test);
	root = parser_parse(scanner, test);

	if (root) {
		optr_print(root);
		optr_release(root);
	}

	strcpy(test, "1 + 2 - 3");
	printf("TeX: %s\n", test);
	root = parser_parse(scanner, test);

	if (root) {
		optr_print(root);
		optr_release(root);
	}

	parser_dele_scanner(scanner);
	mhook_print_unfree();
	return 0;
}

int test_tex_writing()
{
	struct optr_node *root;
	void *scanner = parser_new_scanner();
	if (NULL == scanner)
		return 1;

	char test[] = "1^{2} + 0 - \\frac{2}{-3} - \\sqrt{2} - 4 \\cdot (2 - 3) + \\left| -7 \\right|";
	char outTeX[1024];

	printf("TeX: %s\n", test);
	root = parser_parse(scanner, test);

	if (root) {
		optr_print(root);
		optr_write_tex(outTeX, root);
		printf("TeX: %s\n", outTeX);

		optr_release(root);
	}

	parser_dele_scanner(scanner);
	mhook_print_unfree();
	return 0;
}

int main()
{
	//return print_code_table();
	//return test_parsing();
	return test_tex_writing();
}
