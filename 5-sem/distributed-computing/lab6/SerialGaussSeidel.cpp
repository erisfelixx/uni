#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>

//
// Послідовний метод Гауса–Зейделя
// Оновлює значення у внутрішніх вузлах,
// поки зміна не стане меншою за Eps
//
void ResultCalculation(double* pMatrix, int Size, double &Eps, int &Iterations) {
    double dm, dmax, temp;
    int i, j;

    Iterations = 0;

    do {
        dmax = 0;   // максимальна зміна за поточну ітерацію

        // проходимо всі внутрішні точки сітки (без граничних)
        for (i = 1; i < Size - 1; i++) {
            for (j = 1; j < Size - 1; j++) {

                // зберігаємо старе значення вузла
                temp = pMatrix[Size * i + j];

                // нове значення — середнє значення чотирьох сусідів
                pMatrix[Size * i + j] = 0.25 * (
                    pMatrix[Size * i + j + 1] +     // правий
                    pMatrix[Size * i + j - 1] +     // лівий
                    pMatrix[Size * (i + 1) + j] +   // нижній
                    pMatrix[Size * (i - 1) + j]     // верхній
                );

                // модуль зміни в поточному вузлі
                dm = fabs(pMatrix[Size * i + j] - temp);

                // оновлюємо максимальну зміну за ітерацію
                if (dmax < dm)
                    dmax = dm;
            }
        }

        Iterations++;
    }
    while (dmax > Eps);   // продовжуємо, доки не досягнута потрібна точність
}

//
// Звільнення пам'яті
//
void ProcessTermination(double* pMatrix) {
    delete[] pMatrix;
}

//
// Форматований вивід матриці на екран
//
void PrintMatrix(double* pMatrix, int RowCount, int ColCount) {
    int i, j;

    for (i = 0; i < RowCount; i++) {
        for (j = 0; j < ColCount; j++)
            printf("%7.4f ", pMatrix[i * ColCount + j]);
        printf("\n");
    }
}

//
// Початкова ініціалізація сітки:
// граничні вузли = 100, внутрішні = 0
//
void DummyDataInitialization(double* pMatrix, int Size) {
    int i, j;

    for (i = 0; i < Size; i++) {
        for (j = 0; j < Size; j++) {

            // граничні умови (Діріхле)
            if (i == 0 || i == Size - 1 || j == 0 || j == Size - 1)
                pMatrix[i * Size + j] = 100;
            else
                pMatrix[i * Size + j] = 0;
        }
    }
}

//
// Зчитування параметрів, виділення пам’яті, початкова ініціалізація сітки
//
void ProcessInitialization(double* &pMatrix, int &Size, double &Eps) {

    // введення розміру сітки
    do {
        printf("\nEnter the grid size: ");
        scanf("%d", &Size);
        if (Size <= 2)
            printf("\nSize of grid must be greater than 2!\n");
    }
    while (Size <= 2);

    // введення потрібної точності
    do {
        printf("\nEnter the required accuracy: ");
        scanf("%lf", &Eps);
        if (Eps <= 0)
            printf("\nAccuracy must be greater than 0!\n");
    }
    while (Eps <= 0);

    // виділення пам'яті під матрицю
    pMatrix = new double[Size * Size];

    // початкове заповнення матриці
    DummyDataInitialization(pMatrix, Size);
}

int main() {
    double* pMatrix;   // матриця вузлів сітки
    int Size;          // розмір сітки (Size x Size)
    double Eps;        // потрібна точність
    int Iterations;    // кількість виконаних ітерацій

    clock_t start, finish; // змінні для вимірювання часу
    double duration;       // час виконання в секундах

    printf("Serial Gauss - Seidel algorithm\n");

    // ініціалізація: вводимо параметри, виділяємо пам'ять, задаємо початкові значення
    ProcessInitialization(pMatrix, Size, Eps);

    // --- ВИВІД ПОЧАТКОВОЇ МАТРИЦІ (закоментовано, можна включити для відладки) ---
    // printf("\nInitial Matrix:\n");
    // PrintMatrix(pMatrix, Size, Size);

    // вимірювання часу тільки для самого алгоритму Гауса–Зейделя
    start = clock();
    ResultCalculation(pMatrix, Size, Eps, Iterations);
    finish = clock();

    // обчислюємо тривалість у секундах
    duration = (double)(finish - start) / CLOCKS_PER_SEC;

    // вивід результатів
    printf("\nNumber of iterations: %d\n", Iterations);
    printf("Execution time: %f seconds\n", duration);

    // --- ВИВІД РЕЗУЛЬТУЮЧОЇ МАТРИЦІ (також закоментовано) ---
    // printf("\nResult Matrix:\n");
    // PrintMatrix(pMatrix, Size, Size);

    // звільнення пам'яті
    ProcessTermination(pMatrix);

    return 0;
}
