#include "y.tab.h"
#include "lex.yy.h"

#include "optr.h"
#include "mhook.h"

int main()
{
	yyscan_t scanner;
	if (yylex_init(&scanner))
		return 1;
	
	YY_BUFFER_STATE buf = NULL;

	//char test[] = "0 - (1 + 2)";
	//char test[] = "2(-3)(-4)";
	char test[] = "-(-2(-3)) 5";

	//char test[] = "a[c \\div 2b] = -(-5 + 1 - 3.14) + A \\times x - 2ax";
	//char test[] = "a^{1 + 2}";
	//char test[] = "\\frac 12 a";
	//char test[] = "12 + x *{12}";
	//char test[] = "\\sqrt 12 + 3";

	printf("TeX: %s\n", test);
	buf = yy_scan_string(test, scanner);

	struct optr_node *root;
	yyparse(scanner, &root);

	if (root) {
		optr_print(root);
		optr_release(root);
	}

	yy_delete_buffer(buf, scanner);
	yylex_destroy(scanner);

	mhook_print_unfree();
	return 0;
}
