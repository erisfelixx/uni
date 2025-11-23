#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <ctime>

using namespace std;

// Function for copying the sorted data
void CopyData(double *pData, int DataSize, double *pDataCopy) {
    copy(pData, pData + DataSize, pDataCopy);
}

// Function for comparing the data
bool CompareData(double *pData1, double *pData2, int DataSize) {
    return equal(pData1, pData1 + DataSize, pData2);
}

// Serial bubble sort algorithm
void SerialBubbleSort(double *pData, int DataSize) {
    double Tmp;

    for(int i = 1; i < DataSize; i++)
        for(int j = 0; j < DataSize - i; j++)
            if(pData[j] > pData[j + 1]) {
                Tmp = pData[j];
                pData[j] = pData[j + 1];
                pData[j + 1] = Tmp;
            }
}

// Sorting by the standard library algorithm
void SerialStdSort(double *pData, int DataSize) {
    sort(pData, pData + DataSize);
}

// Function for formatted data output
void PrintData(double *pData, int DataSize) {
    for(int i = 0; i < DataSize; i++)
        printf("%7.4f ", pData[i]);
    printf("\n");
}

// Main testing function
int main() {
    int DataSize;
    printf("Enter the size of the data to be sorted: ");
    scanf("%d", &DataSize);

    double *pData = new double[DataSize];
    double *pDataCopy = new double[DataSize];

    // Random data initialization
    srand((unsigned)time(0));
    for (int i = 0; i < DataSize; i++) {
        pData[i] = double(rand()) / RAND_MAX * 1000.0;  // Random data between 0 and 1000
    }

    // Copy the original data for comparison later
    CopyData(pData, DataSize, pDataCopy);

    // Serial sorting
    printf("Sorting using serial bubble sort...\n");
    SerialBubbleSort(pData, DataSize);
    printf("Data after serial bubble sort:\n");
    PrintData(pData, 10);  // Print the first 10 elements to verify
    
    // Reset data for standard library sort
    CopyData(pDataCopy, DataSize, pData);

    // Standard library sort
    printf("Sorting using standard sort...\n");
    SerialStdSort(pData, DataSize);
    printf("Data after standard sort:\n");
    PrintData(pData, 10);  // Print the first 10 elements to verify

    // Compare the results
    if (CompareData(pDataCopy, pData, DataSize)) {
        printf("The sorting results are identical.\n");
    } else {
        printf("The sorting results differ.\n");
    }

    // Clean up
    delete[] pData;
    delete[] pDataCopy;

    return 0;
}

