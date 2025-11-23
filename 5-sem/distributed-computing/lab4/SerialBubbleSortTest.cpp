#include <algorithm>
#include <cstdio>

using namespace std;

// Function for formatted data output
void PrintData(double *pData, int DataSize) {
    for(int i = 0; i < DataSize; i++)
        printf("%7.4f ", pData[i]);
    printf("\n");
}

// Sorting by the standard library algorithm
void SerialStdSort(double *pData, int DataSize) {
    sort(pData, pData + DataSize);
}

int main() {
    int DataSize = 5;
    double pData[5] = { 5.5, 2.3, 8.1, 3.7, 4.6 };

    printf("Data before sorting:\n");
    PrintData(pData, DataSize);

    SerialStdSort(pData, DataSize);

    printf("\nData after sorting:\n");
    PrintData(pData, DataSize);

    return 0;
}

