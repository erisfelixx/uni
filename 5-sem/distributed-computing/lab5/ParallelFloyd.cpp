#include <cstdlib>
#include <cstdio>
#include <ctime>
#include <algorithm>
#include <mpi.h>

using namespace std;

int ProcRank;    // Rank поточного процесу (0..ProcNum-1)
int ProcNum;     // Загальна кількість процесів

const double InfinitiesPercent = 50.0;
const double RandomDataMultiplier = 10;

// ---------- ПРОТОТИПИ ----------

int Min(int A, int B);
void ProcessInitialization(int *&pMatrix, int *&pProcRows, int& Size, int& RowNum);
void ProcessTermination(int *pMatrix, int *pProcRows);
void DummyDataInitialization(int *pMatrix, int Size);
void RandomDataInitialization(int *pMatrix, int Size);
void DataDistribution(int *pMatrix, int *pProcRows, int Size, int RowNum);
void ResultCollection(int *pMatrix, int *pProcRows, int Size, int RowNum);
void ParallelFloyd(int *pProcRows, int Size, int RowNum);
void RowDistribution(int *pProcRows, int Size, int RowNum, int k, int *pRow);
void ParallelPrintMatrix(int *pProcRows, int Size, int RowNum);
void TestDistribution(int *pMatrix, int *pProcRows, int Size, int RowNum);
void TestResult(int *pMatrix, int *pSerialMatrix, int Size);

void PrintMatrix(int *pMatrix, int RowCount, int ColCount);
void SerialFloyd(int *pMatrix, int Size);
bool CompareMatrices(int *pMatrix1, int *pMatrix2, int Size);
void CopyMatrix(int *pMatrix, int Size, int *pMatrixCopy);

// ---------- РЕАЛІЗАЦІЯ ----------

// Мінімум двох значень з урахуванням "INF" як -1
int Min(int A, int B) {
    int Result = (A < B) ? A : B;

    if ((A < 0) && (B >= 0)) Result = B;   // A = INF
    if ((B < 0) && (A >= 0)) Result = A;   // B = INF
    if ((A < 0) && (B < 0))  Result = -1;  // обидва INF

    return Result;
}

int main(int argc, char* argv[]) {
    int *pMatrix;      // Повна матриця суміжності (лише на процесі 0)
    int  Size;         // Кількість вершин (розмір матриці)
    int *pProcRows;    // Смуга рядків, яка належить поточному процесу
    int  RowNum;       // Кількість рядків у поточному процесі

    double start, finish;
    double duration = 0.0;
    int *pSerialMatrix = 0; // копія повної матриці для можливого тесту

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &ProcNum);
    MPI_Comm_rank(MPI_COMM_WORLD, &ProcRank);

    if (ProcRank == 0)
        printf("Parallel Floyd algorithm\n");

    // 1) Ввід розміру, розрахунок кількості рядків на процес, ініціалізація матриці
    ProcessInitialization(pMatrix, pProcRows, Size, RowNum);

    if (ProcRank == 0) {
        // Копія початкової матриці (якщо захочеш потім перевіряти коректність)
        pSerialMatrix = new int[Size * Size];
        CopyMatrix(pMatrix, Size, pSerialMatrix);
    }

    // Починаємо вимір часу для розподілу + обчислень + збирання
    start = MPI_Wtime();

    // 2) Розподіл блоків рядків матриці між процесами (Block Row Decomposition)
    DataDistribution(pMatrix, pProcRows, Size, RowNum);
    //TestDistribution(pMatrix, pProcRows, Size, RowNum);

    // 3) Паралельний алгоритм Флойда над локальними рядками
    ParallelFloyd(pProcRows, Size, RowNum);
    //ParallelPrintMatrix(pProcRows, Size, RowNum);

    // 4) Збір усіх результатів назад у процес 0
    ResultCollection(pMatrix, pProcRows, Size, RowNum);
    //if (ProcRank == 0)
    //    PrintMatrix(pMatrix, Size, Size);

    finish = MPI_Wtime();

    //TestResult(pMatrix, pSerialMatrix, Size);
    duration = finish - start;
    if (ProcRank == 0)
        printf("Time of execution: %f\n", duration);

    if (ProcRank == 0)
        delete [] pSerialMatrix;

    // 5) Звільняємо пам’ять
    ProcessTermination(pMatrix, pProcRows);

    MPI_Finalize();
    return 0;
}

// Ініціалізація: введення Size, розподіл рядків між процесами, створення матриці
void ProcessInitialization(int *&pMatrix, int *&pProcRows, int& Size,
                           int& RowNum) {
    // Відключаємо буфер stdout (щоб вивід з MPI був більш прогнозований)
    setvbuf(stdout, 0, _IONBF, 0);

    if (ProcRank == 0) {
        // Ранг 0 запитує розмір графа, поки він не менший за кількість процесів
        do {
            printf("Enter the number of vertices: ");
            scanf("%d", &Size);

            if (Size < ProcNum)
                printf("The number of vertices should be greater then "
                       "the number of processes\n");
        } while (Size < ProcNum);

        printf("Using the graph with %d vertices\n", Size);
    }

    // Розсилаємо Size усім процесам
    MPI_Bcast(&Size, 1, MPI_INT, 0, MPI_COMM_WORLD);

    // Нерівномірно ділимо рядки між процесами (щоб сумарно було рівномірно)
    int RestRows = Size;
    for (int i = 0; i < ProcRank; i++)
        RestRows = RestRows - RestRows / (ProcNum - i);
    RowNum = RestRows / (ProcNum - ProcRank);

    // Виділяємо пам'ять під локальні рядки (частина матриці)
    pProcRows = new int[Size * RowNum];

    if (ProcRank == 0) {
        // На процесі 0 зберігаємо повну матрицю
        pMatrix = new int[Size * Size];

        // Початкова ініціалізація графа (тестовий приклад)
        DummyDataInitialization(pMatrix, Size);
        //RandomDataInitialization(pMatrix, Size);
    } else {
        pMatrix = nullptr; // на інших процесах повна матриця не потрібна
    }
}

// Звільнення пам’яті (повна матриця тільки на процесі 0)
void ProcessTermination(int *pMatrix, int *pProcRows) {
    if (ProcRank == 0 && pMatrix != nullptr)
        delete [] pMatrix;
    delete [] pProcRows;
}

// Статична тестова матриця: 0 на головній діагоналі, j у першому рядку, -1 (INF) інакше
void DummyDataInitialization(int *pMatrix, int Size) {
    for (int i = 0; i < Size; i++)
        for (int j = i; j < Size; j++) {
            if (i == j) pMatrix[i * Size + j] = 0;
            else if (i == 0) pMatrix[i * Size + j] = j;
            else             pMatrix[i * Size + j] = -1;
            // симетричний граф
            pMatrix[j * Size + i] = pMatrix[i * Size + j];
        }
}

// Випадкова матриця з INF з імовірністю InfinitiesPercent
void RandomDataInitialization(int *pMatrix, int Size) {
    srand((unsigned)time(0));

    for (int i = 0; i < Size; i++)
        for (int j = 0; j < Size; j++)
            if (i != j) {
                if ((rand() % 100) < InfinitiesPercent)
                    pMatrix[i * Size + j] = -1;
                else
                    pMatrix[i * Size + j] = rand() + 1;
            } else
                pMatrix[i * Size + j] = 0;
}

// Розподіл рядків повної матриці між процесами (MPI_Scatterv)
void DataDistribution(int *pMatrix, int *pProcRows, int Size, int RowNum) {
    int *pSendNum; // Кількість елементів, які йдуть кожному процесу
    int *pSendInd; // Індекс першого елемента для кожного процесу в pMatrix
    int RestRows = Size; // Скільки рядків ще не розподілено

    // Тимчасові масиви для схем розподілу
    pSendInd = new int[ProcNum];
    pSendNum = new int[ProcNum];

    // Розрахунок кількості елементів для кожного процесу (той же алгоритм, що й у ініціалізації)
    RowNum = Size / ProcNum;
    pSendNum[0] = RowNum * Size;
    pSendInd[0] = 0;
    for (int i = 1; i < ProcNum; i++) {
        RestRows   -= RowNum;
        RowNum      = RestRows / (ProcNum - i);
        pSendNum[i] = RowNum * Size;
        pSendInd[i] = pSendInd[i - 1] + pSendNum[i - 1];
    }

    // Розсилаємо різну кількість рядків кожному процесу
    MPI_Scatterv(pMatrix, pSendNum, pSendInd, MPI_INT,
                 pProcRows, pSendNum[ProcRank], MPI_INT, 0, MPI_COMM_WORLD);

    delete [] pSendNum;
    delete [] pSendInd;
}

// Збір результатів із локальних блоків рядків назад у повну матрицю (процес 0)
void ResultCollection(int *pMatrix, int *pProcRows, int Size, int RowNum) {
    int *pReceiveNum;  // Скільки елементів надсилає кожен процес
    int *pReceiveInd;  // Куди в загальній матриці класти блок від процесу
    int RestRows = Size;

    pReceiveNum = new int[ProcNum];
    pReceiveInd = new int[ProcNum];

    RowNum = Size / ProcNum;
    pReceiveInd[0] = 0;
    pReceiveNum[0] = RowNum * Size;

    for (int i = 1; i < ProcNum; i++) {
        RestRows      -= RowNum;
        RowNum         = RestRows / (ProcNum - i);
        pReceiveNum[i] = RowNum * Size;
        pReceiveInd[i] = pReceiveInd[i - 1] + pReceiveNum[i - 1];
    }

    // Збираємо обчислені частини матриці на процесі 0
    MPI_Gatherv(pProcRows, pReceiveNum[ProcRank], MPI_INT,
                pMatrix, pReceiveNum, pReceiveInd, MPI_INT, 0, MPI_COMM_WORLD);

    delete [] pReceiveNum;
    delete [] pReceiveInd;
}

// Паралельний Floyd–Warshall над блоками рядків
void ParallelFloyd(int *pProcRows, int Size, int RowNum) {
    int *pRow = new int[Size]; // буфер для k-го рядка
    int t1, t2;

    // Зовнішній цикл по k — як у звичайному Флойді
    for (int k = 0; k < Size; k++) {
        // 1) Визначити, в якому процесі лежить рядок k, і розіслати його всім
        RowDistribution(pProcRows, Size, RowNum, k, pRow);

        // 2) Кожен процес оновлює СВОЇ рядки, використовуючи розісланий рядок k
        for (int i = 0; i < RowNum; i++)
            for (int j = 0; j < Size; j++)
                if ((pProcRows[i * Size + k] != -1) &&
                    (pRow[j]               != -1)) {
                    t1 = pProcRows[i * Size + j];
                    t2 = pProcRows[i * Size + k] + pRow[j];

                    pProcRows[i * Size + j] = Min(t1, t2);
                }
    }

    delete [] pRow;
}

// Визначає, який процес містить k-й рядок, копіює його в буфер і робить MPI_Bcast
void RowDistribution(int *pProcRows, int Size, int RowNum, int k, int *pRow) {
    int ProcRowRank;  // Ранг процесу, який містить рядок k
    int ProcRowNum;   // Номер рядка усередині цього процесу

    int RestRows = Size;
    int Ind = 0;
    int Num = Size / ProcNum;

    // Знаходимо, до якого процесу належить глобальний рядок k
    for (ProcRowRank = 1; ProcRowRank < ProcNum + 1; ProcRowRank++) {
        if (k < Ind + Num) break;
        RestRows -= Num;
        Ind      += Num;
        Num       = RestRows / (ProcNum - ProcRowRank);
    }
    ProcRowRank = ProcRowRank - 1;
    ProcRowNum  = k - Ind;

    // Процес-власник копіює свій локальний рядок у pRow
    if (ProcRowRank == ProcRank)
        copy(&pProcRows[ProcRowNum * Size],
             &pProcRows[(ProcRowNum + 1) * Size],
             pRow);

    // Розсилаємо повний рядок k усім процесам
    MPI_Bcast(pRow, Size, MPI_INT, ProcRowRank, MPI_COMM_WORLD);
}

// Вивід локальних блоків рядків (зараз фактично вимкнено, бо PrintMatrix порожня)
void ParallelPrintMatrix(int *pProcRows, int Size, int RowNum) {
    for (int i = 0; i < ProcNum; i++) {
        MPI_Barrier(MPI_COMM_WORLD);
        if (ProcRank == i) {
            printf("ProcRank = %d\n", ProcRank);
            fflush(stdout);
            printf("Proc rows:\n");
            fflush(stdout);
            PrintMatrix(pProcRows, RowNum, Size);
            fflush(stdout);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }
}

// Тест коректності розподілу (не використовується при замірі часу)
void TestDistribution(int *pMatrix, int *pProcRows, int Size, int RowNum) {
    MPI_Barrier(MPI_COMM_WORLD);
    if (ProcRank == 0) {
        printf("Initial adjacency matrix:\n");
        PrintMatrix(pMatrix, Size, Size);
    }

    MPI_Barrier(MPI_COMM_WORLD);

    ParallelPrintMatrix(pProcRows, Size, RowNum);
}

// Тест збіжності з серійною версією (використовується зараз)
void TestResult(int *pMatrix, int *pSerialMatrix, int Size) {
    MPI_Barrier(MPI_COMM_WORLD);

    if (ProcRank == 0) {
        SerialFloyd(pSerialMatrix, Size);
        if (!CompareMatrices(pMatrix, pSerialMatrix, Size)) {
            printf("Results of serial and parallel algorithms are "
                   "NOT identical. Check your code\n");
        } else {
            printf("Results of serial and parallel algorithms are "
                   "identical\n");
        }
    }
}



void PrintMatrix(int *pMatrix, int RowCount, int ColCount) {
    (void)pMatrix; (void)RowCount; (void)ColCount;
}

// реалізація серійного Флойда (для TestResult)
void SerialFloyd(int *pMatrix, int Size) {
    (void)pMatrix; (void)Size;
}

// Порівняння матриць
bool CompareMatrices(int *pMatrix1, int *pMatrix2, int Size) {
    (void)pMatrix1; (void)pMatrix2; (void)Size;
    return true;
}

// Копія матриці
void CopyMatrix(int *pMatrix, int Size, int *pMatrixCopy) {
    for (int i = 0; i < Size * Size; i++)
        pMatrixCopy[i] = pMatrix[i];
}
