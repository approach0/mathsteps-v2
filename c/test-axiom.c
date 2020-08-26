#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

#include "mhook.h"
#include "axiom.h"

char *_ltrim(char *s)
{
    while(isspace(*s)) s++;
    return s;
}

char *_rtrim(char *s)
{
    char* back = s + strlen(s);
    while(isspace(*--back));
    *(back+1) = '\0';
    return s;
}

char *trim(char *s)
{
    return _rtrim(_ltrim(s));
}

int cnt_occur(char *s)
{
	int count = 0;
	while ((s = strchr(s, '\n')) != NULL) {
		count++;
		s++;
	}
	return count;
}

int main()
{
	struct Axiom *a = axiom_new("distribute rules");

	char *all, *now, *field;
	all = now = strdup("ab \n cd \n ef");
	printf("cnt = %d\n", cnt_occur(all));
	while ((field = strsep(&now, "\n"))) {
		printf("[%s]\n", trim(field));
	}
	printf("%s\n", all);
	free(all);

	axiom_add_static_rule(a, "a + 0", "a", NULL);
	//axiom_print(a);

	axiom_free(a);
	mhook_print_unfree();
	return 0;
}
