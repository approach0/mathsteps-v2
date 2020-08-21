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

	buf = yy_scan_string("1 + 2", scanner);
	yyparse(scanner);

	yy_delete_buffer(buf, scanner);
	yylex_destroy(scanner);

	mhook_print_unfree();
	return 0;
}
