%option reentrant bison-bridge
%option header-file="lex.yy.h"

%{
#include "y.tab.h"
#include "optr.h"

#define RET_NUM(_n) \
	yylval->nd = optr_alloc(OPTR_NODE_NUM); \
	yylval->nd->num = (_n >= 0) ? _n : -_n; \
	yylval->nd->sign = (_n >= 0) ? 1.f : -1.f; \
	return NUM;

#define RET_VAR(_c) \
	yylval->nd = optr_alloc(OPTR_NODE_VAR); \
	yylval->nd->var = _c; \
	return VAR;
%}

%%
"="      { return _EQ; }
"+"      { return _ADD; }
"-"      { return _MINUS; }
\\times  { return _TIMES; }
\\cdot   { return _CDOT; }
\\div    { return _DIV; }
"^"      { return _SUP; }
"_"      { return _SUB; }

"{"      { return _L_TEX; }
"}"      { return _R_TEX; }

\\frac   { return _FRAC; }

 /*
"("|"["  { return "("; }
")"|"]"  { return ")"; }
 */

[0-9]+\.[0-9]+ { float num; sscanf(yytext, "%f", &num); RET_NUM(num); }
[0-9]+         { int num; sscanf(yytext, "%d", &num); RET_NUM(num); }

[a-z]          { RET_VAR(yytext[0]); }
[A-Z]          { RET_VAR(yytext[0]); }

\n             { return _EOL; }

.              { /* omit */ }
%%
