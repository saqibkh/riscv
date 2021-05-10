// C program for implementation of Bubble sort 
#include <stdio.h> 
#include <time.h>

void swap(int *xp, int *yp) 
{ 
	int temp = *xp; 
	*xp = *yp; 
	*yp = temp; 
} 

// A function to implement bubble sort 
void bubbleSort(int arr[], int n) 
{ 
int i, j; 
for (i = 0; i < n-1; i++)	 

	// Last i elements are already in place 
	for (j = 0; j < n-i-1; j++) 
		if (arr[j] > arr[j+1]) 
			swap(&arr[j], &arr[j+1]); 
} 

/* Function to print an array */
void printArray(int arr[], int size) 
{ 
	int i; 
	for (i=0; i < size; i++) 
		printf("%d ", arr[i]); 
	printf("\n"); 
} 

// Driver program to test above functions 
int main() 
{ 
	clock_t t;
        t = clock();

	int arr[] = {64, 34, 25, 12, 22, 11, 90, 45, 34, 71, 50}; 
	int n = sizeof(arr)/sizeof(arr[0]); 
	bubbleSort(arr, n); 
	printf("Sorted array: \n"); 
	printArray(arr, n); 

	t = clock() - t;
        double time_taken = ((double)t)/CLOCKS_PER_SEC; // in seconds
        printf("Total Execution time: %f seconds\n", time_taken);
	return 0; 
}
