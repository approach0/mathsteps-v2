%option reentrant bison-bridge
%option header-file="lex.yy.h"

%{
#include "y.tab.h"
#include "optr.h"
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

[0-9]+\.[0-9]+ { yylval.nd = optr_alloc(OPTR_NODE_NUM); yylval.num = 123; return NUM; }
 */
[0-9]+         { return NUM; }

 /*[a-z]          { return "VAR"; }
[A-Z]          { return "VAR"; } */

\n             { return _EOL; }

.              { /* omit */ }
%%
