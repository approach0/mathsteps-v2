%option reentrant bison-bridge
%option header-file="lex.yy.h"

%{
#include "y.tab.h"
#include "optr.h"

#define RET_NUM(_n) \
	yylval->nd = optr_alloc(OPTR_NODE_NUM); \
	yylval->nd->num = _n; \
	return NUM;
%}

%%
"+"      { return _ADD; }
 /* "-"      { return "-"; } */
\\times  { return _TIMES; }
\\cdot   { return _TIMES; }

 /* \\div    { return "D"; }
\\frac   { return "F"; }

"("|"["  { return "("; }
")"|"]"  { return ")"; }

"{"      { return "{"; }
"}"      { return "}"; }
 */

[0-9]+\.[0-9]+ { float num; sscanf(yytext, "%f", &num); RET_NUM(num); }
[0-9]+         { int num; sscanf(yytext, "%d", &num); RET_NUM(num); }

 /*[a-z]          { return "VAR"; }
[A-Z]          { return "VAR"; } */

\n             { return _EOL; }

.              { /* omit */ }
%%
