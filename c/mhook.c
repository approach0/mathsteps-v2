#include <stdio.h>
#include <pthread.h>
#include "mhook.h"

static int64_t unfree = 0;
static int64_t tot_allocs = 0;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

int64_t mhook_unfree()
{
	return unfree;
}

int64_t mhook_tot_allocs()
{
	return unfree;
}

void mhook_print_unfree()
{
	printf("Total memory allocs: %ld.\n", tot_allocs);
	printf("Unfree memory allocs: %ld.\n", unfree);
}

/* malloc() hook */
void *__real_malloc(size_t);

void *__wrap_malloc(size_t c)
{
	void *p = __real_malloc(c);

	if (p) {
		pthread_mutex_lock(&mutex);
		unfree++;
		tot_allocs++;
		pthread_mutex_unlock(&mutex);
	}

	return p;
}

/* calloc() hook */
void *__real_calloc(size_t, size_t);

void *__wrap_calloc(size_t nmemb, size_t size)
{
	void *p = __real_calloc(nmemb, size);

	if (p) {
		pthread_mutex_lock(&mutex);
		unfree++;
		tot_allocs++;
		pthread_mutex_unlock(&mutex);
	}

	return p;
}

/* realloc() hook */
void *__real_realloc(void *, size_t);

void *__wrap_realloc(void *ptr, size_t sz)
{
	void *p = __real_realloc(ptr, sz);

	if (p) {
		pthread_mutex_lock(&mutex);
		if (ptr == NULL) {
			/* equivalent to malloc */
			unfree++;
			tot_allocs++;
		} else if (sz == 0) {
			/* equivalent to free */
			unfree--;
		} else {
			; /* realloc takes care of the old buffer */
		}
		pthread_mutex_unlock(&mutex);
	}

	return p;
}

/* strdup() hook */
void *__real_strdup(const char *);

void *__wrap_strdup(const char *s)
{
	void *p = __real_strdup(s);

	if (p) {
		pthread_mutex_lock(&mutex);
		unfree++;
		tot_allocs++;
		pthread_mutex_unlock(&mutex);
	}

	return p;
}

/* free() hook */
void __real_free(void*);

void __wrap_free(void *p)
{
	if (p) {
		pthread_mutex_lock(&mutex);
		unfree--;
		pthread_mutex_unlock(&mutex);
	}

	__real_free(p);
}
