#include <time.h>
#include <unistd.h>
#include "mhook.h"
#include "mcts.h"

int main()
{
	srand(time(NULL));

	struct expr_tr *root_tr = malloc(sizeof(struct expr_tr));
	struct state root;
	root_tr->val = 123.f;
	state_init(&root, root_tr);

	const int n_processors = sysconf(_SC_NPROCESSORS_ONLN);
	int n_threads = n_processors - 1;
	mcts(&root, n_threads, 440, 10, 4);

	state_free(&root);
	mhook_print_unfree();
}
