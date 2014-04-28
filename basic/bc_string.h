typedef struct BCString{
	unsigned long length;
	char data[];
} BCString;

BCString* alloc_str(unsigned long length);
BCString* cat_str(BCString* a, BCString* b);
int eq_str(BCString* a, BCString* b);
BCString* input_str(FILE* f);
