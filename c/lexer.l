%{
#include "y.tab.h"

%}

%%
"+"      { return ADD; }
 /* "-"      { return "-"; } */
\\times  { return TIMES; }
\\cdot   { return TIMES; }

 /* \\div    { return "D"; }
\\frac   { return "F"; }

"("|"["  { return "("; }
")"|"]"  { return ")"; }

"{"      { return "{"; }
"}"      { return "}"; }
 */

[0-9]+\.[0-9]+ { return NUM; }
[0-9]+         { return NUM; }

 /*[a-z]          { return "VAR"; }
[A-Z]          { return "VAR"; } */

\n             { return _EOL; }

.              { /* omit */ }
%%
