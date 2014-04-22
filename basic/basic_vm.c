#include <stdlib.h>
#include <stdio.h>

struct BCHead{
	unsigned short int code_length;
	unsigned short int nb_int;
	unsigned short int nb_str;
	unsigned short int nb_const_int;
	unsigned short int nb_const_str;
};

typedef struct BCString{
	unsigned long length;
	char data[];
} BCString;

BCString* alloc_str(unsigned long length){
	return (BCString*) malloc(sizeof(BCString) + length + 1);
}

int main(int argc, char* argv[]){
	if (argc != 2){
		fputs("Usage: basic_vm FILENAME", stderr);
		return EXIT_FAILURE;
	}

	FILE* f = fopen(argv[1], "rb");
	struct BCHead head;
	fread(&head, sizeof(head), 1, f);
	printf("code_length = %hu\n", head.code_length);
	printf("nb_int = %hu\n", head.nb_int);
	printf("nb_str = %hu\n", head.nb_str);
	printf("nb_const_int = %hu\n", head.nb_const_int);
	printf("nb_const_str = %hu\n", head.nb_const_str);

	int *const_int = malloc(head.nb_const_int * sizeof(int));
	fread(const_int, sizeof(int), head.nb_const_int, f);


	BCString **const_str = malloc(head.nb_const_str * sizeof(BCString*));

	for (int i=0; i<head.nb_const_str; i++){
		unsigned int length = 0;
		fread(&length, sizeof(length), 1, f);
		const_str[i] = alloc_str(length);
		const_str[i]->length = length;
		fread(&const_str[i]->data, 1, length, f);
		const_str[i]->data[length] = '\0';
	}

	for (int i=0; i<head.nb_const_int; i++){
		printf("const_int[%d] = %d\n", i, const_int[i]);
	}
	for (int i=0; i<head.nb_const_str; i++){
		printf("const_str[%d] = %s\n", i, const_str[i]->data);
	}


	for (int i=0; i<head.nb_const_str; i++){
		free(const_str[i]);
	}
	free(const_str);
	free(const_int);
	fclose(f);
}

