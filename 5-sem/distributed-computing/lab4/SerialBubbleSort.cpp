#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <algorithm>

using namespace std;

const double RandomDataMultiplier = 1000.0;

// Функції
void ProcessInitialization(double *&pData, int &DataSize);
void ProcessTermination(double *pData);
void DummyDataInitialization(double *&pData, int &DataSize);
void RandomDataInitialization(double *&pData, int &DataSize);
void SerialBubble(double *pData, int DataSize);
void SerialStdSort(double *pData, int DataSize);
void PrintData(double *pData, int DataSize);

int main(int argc, char *argv[]) {
    double *pData = nullptr;
    int DataSize = 0;
    time_t start, finish;
    double duration = 0.0;

    printf("Serial bubble sort program\n");

    // Ініціалізація даних
    ProcessInitialization(pData, DataSize);

    start = clock();

    SerialBubble(pData, DataSize);

    finish = clock();

    duration = (finish - start) / double(CLOCKS_PER_SEC);
    printf("Time of execution: %f\n", duration);

    // Завершення процесу
    ProcessTermination(pData);

    return 0;
}

// Функція ініціалізації даних
void ProcessInitialization(double *&pData, int &DataSize) {
    do {
        printf("Enter the size of data to be sorted: ");
        scanf("%d", &DataSize);

        if (DataSize <= 0)
            printf("Data size should be greater than zero\n");
    } while (DataSize <= 0);

    printf("Sorting %d data items\n", DataSize);

    pData = new double[DataSize];

    // Ініціалізація випадковими числами
    RandomDataInitialization(pData, DataSize);
}

// Функція завершення процесу
void ProcessTermination(double *pData) {
    delete[] pData;
}

// Просте заповнення даних (демонстраційне)
void DummyDataInitialization(double *&pData, int &DataSize) {
    for (int i = 0; i < DataSize; i++)
        pData[i] = DataSize - i;
}

// Ініціалізація випадковими числами
void RandomDataInitialization(double *&pData, int &DataSize) {
    srand((unsigned)time(0));

    for (int i = 0; i < DataSize; i++)
        pData[i] = double(rand()) / RAND_MAX * RandomDataMultiplier;
}

// Алгоритм сортування бульбашкою
void SerialBubble(double *pData, int DataSize) {
    double Tmp;

    for (int i = 1; i < DataSize; i++)
        for (int j = 0; j < DataSize - i; j++)
            if (pData[j] > pData[j + 1]) {
                Tmp = pData[j];
                pData[j] = pData[j + 1];
                pData[j + 1] = Tmp;
            }
}

// Сортування за допомогою стандартного алгоритму
void SerialStdSort(double *pData, int DataSize) {
    sort(pData, pData + DataSize);
}

// Функція для виводу даних
void PrintData(double *pData, int DataSize) {
    for (int i = 0; i < DataSize; i++)
        printf("%f ", pData[i]);
    printf("\n");
}

