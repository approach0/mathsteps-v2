#include "y.tab.h"
#include "lex.yy.h"

#include "optr.h"

void *parser_new_scanner(void)
{
	yyscan_t scanner;
	if (yylex_init(&scanner))
		return NULL;
	
	return scanner;
}

struct optr_node *parser_parse(void *scanner, const char *tex)
{
	YY_BUFFER_STATE buf = yy_scan_string(tex, scanner);

	struct optr_node *root;
	int pound_cnt = 0;
	yyparse(scanner, &root, &pound_cnt);

	yy_delete_buffer(buf, scanner);
	return root;
}

void parser_dele_scanner(void *scanner)
{
	yylex_destroy(scanner);
}
