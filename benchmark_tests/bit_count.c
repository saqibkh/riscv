// C program to Count set 
// bits in an integer 
#include <stdio.h> 

/* Function to get no of set bits in binary 
representation of positive integer n */
unsigned int countSetBits(unsigned int n) 
{ 
	unsigned int count = 0; 
	while (n) { 
		count += n & 1; 
		n >>= 1; 
	} 
	return count; 
} 

/* Program to test function countSetBits */
int main() 
{
	int i = 923472389;
	printf("Number of bits = %d\n", countSetBits(i));
	return 0; 
}
