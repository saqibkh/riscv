#include<stdio.h>  
int main()    
{    
int r,sum=0,temp;    
int n = 15;
printf("\nNumber= %d\n", n);
temp=n;    
while(n>0)    
{    
r=n%10;    
sum=(sum*10)+r;    
n=n/10;    
}    
if(temp==sum)    
printf("palindrome number \n");    
else    
printf("not palindrome\n");   
return 0;  
}
