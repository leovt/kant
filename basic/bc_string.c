#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "bc_string.h"

BCString* alloc_str(unsigned long length){
	return (BCString*) malloc(sizeof(BCString) + length + 1);
}

BCString* cat_str(BCString* a, BCString* b){
	BCString* result = alloc_str(a->length + b->length);
	result->length = a->length + b->length;
	memcpy(&result->data[0], &a->data[0], a->length);
	memcpy(&result->data[a->length], &b->data[0], b->length);
	return result;
}

BCString* input_str(FILE* f){
	char buffer[100];
	fgets(buffer, 100, f);
	buffer[99] = '\0';
	unsigned int length = strlen(buffer);
	if (buffer[length-1] == '\n'){
		buffer[length-1] = '\0';
		length--;
	}
	BCString* result = alloc_str(length);
	result->length = length;
	memcpy(&result->data[0], buffer, length);
	return result;
}

int eq_str(BCString* a, BCString* b){
	if (a->length != b->length)
		return 0;
	if (a->length == 0 && b->length == 0)
		return 1;
	return memcmp(a->data, b->data, a->length) == 0;
}
