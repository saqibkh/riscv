// C program to Count set 
// bits in an integer 
#include <stdio.h> 
#include <time.h>

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
	clock_t t;
        t = clock();

	int i = 923472389;
	printf("Number of bits = %d\n", countSetBits(i)); 

	t = clock() - t;
        double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
        printf("Total Execution time: %f seconds\n", time_taken);
	return 0; 
}
