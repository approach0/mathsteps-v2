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

	buf = yy_scan_string("ac \\div 2b = -5 + 1 - 3.14 + A \\times x - 2ax", scanner);

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
