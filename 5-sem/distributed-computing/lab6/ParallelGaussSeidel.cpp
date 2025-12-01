#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <mpi.h>
#include <algorithm>

using namespace std;

static int ProcNum = 0;
static int ProcRank = -1;

// Function for distribution of the grid rows among the processes
void DataDistribution(double* pMatrix, double* pProcRows, int RowNum, int Size) {
    int *pSendNum;
    int *pSendInd;
    int RestRows = Size - 2;
    pSendInd = new int [ProcNum];
    pSendNum = new int [ProcNum];

    int InnerRows = RestRows / ProcNum;
    pSendNum[0] = (InnerRows + 2) * Size;
    pSendInd[0] = 0;
    RestRows -= InnerRows;

    for (int i = 1; i < ProcNum; i++) {
        InnerRows = RestRows / (ProcNum - i);
        pSendNum[i] = (InnerRows + 2) * Size;
        pSendInd[i] = pSendInd[i - 1] + pSendNum[i - 1] - 2 * Size;
        RestRows -= InnerRows;
    }

    MPI_Scatterv(
        pMatrix,
        pSendNum,
        pSendInd,
        MPI_DOUBLE,
        pProcRows,
        pSendNum[ProcRank],
        MPI_DOUBLE,
        0,
        MPI_COMM_WORLD
    );

    delete [] pSendInd;
    delete [] pSendNum;
}

// Function for computational process termination
void ProcessTermination (double* pMatrix, double* pProcRows) {
    if (ProcRank == 0)
        delete [] pMatrix;
    delete [] pProcRows;
}

// Function for formatted matrix output
void PrintMatrix(double *pMatrix, int RowCount, int ColCount){
    int i, j;
    for (i = 0; i < RowCount; i++) {
        for (j = 0; j < ColCount; j++)
            printf("%7.4f ", pMatrix[i * ColCount + j]);
        printf("\n");
    }
}

// Function for the execution of the Gauss-Seidel method iteration
double IterationCalculation(double* pProcRows, int Size, int RowNum) {
    int i, j;
    double dm, dmax, temp;
    dmax = 0;

    for (i = 1; i < RowNum - 1; i++) {
        for (j = 1; j < Size - 1; j++) {
            temp = pProcRows[Size * i + j];
            pProcRows[Size * i + j] = 0.25 * (
                pProcRows[(i - 1) * Size + j] +
                pProcRows[(i + 1) * Size + j] +
                pProcRows[i * Size + j - 1] +
                pProcRows[i * Size + j + 1]
            );
            dm = fabs(pProcRows[Size * i + j] - temp);
            if (dmax < dm) dmax = dm;
        }
    }
    return dmax;
}

// Function for simple setting the grid node values
void DummyDataInitialization (double* pMatrix, int Size) {
    int i, j;
    for (i = 0; i < Size; i++) {
        for (j = 0; j < Size; j++) {
            if (i == 0 || i == Size - 1 || j == 0 || j == Size - 1)
                pMatrix[i * Size + j] = 100;
            else
                pMatrix[i * Size + j] = 0;
        }
    }
}

// Function for setting the grid node values by a random generator
void RandomDataInitialization (double* pMatrix, int Size) {
    int i, j;
    srand(unsigned(clock()));
    for (i = 0; i < Size; i++) {
        for (j = 0; j < Size; j++) {
            if (i == 0 || i == Size - 1 || j == 0 || j == Size - 1)
                pMatrix[i * Size + j] = 100;
            else
                pMatrix[i * Size + j] = rand() / double(1000);
        }
    }
}

// Function for memory allocation and initialization of grid nodes
// (interactive: ask user for size and eps on rank 0)
void ProcessInitialization (double* &pMatrix,
                            double* &pProcRows,
                            int &Size,
                            int &RowNum,
                            double &Eps) {
    int RestRows;
    int i;

    if (ProcRank == 0) {
        // --- ask for grid size ---
        do {
            printf("Enter the grid size: ");
            fflush(stdout);
            scanf("%d", &Size);

            if (Size <= 2) {
                printf("Size of grid must be greater than 2!\n");
            }
            if (Size <= ProcNum) {
                printf("Size of grid (%d) must be greater than number of processes (%d)!\n",
                       Size, ProcNum);
            }
        } while (Size <= 2 || Size <= ProcNum);

        // --- ask for required accuracy (eps) ---
        do {
            printf("Enter the required accuracy: ");
            fflush(stdout);
            scanf("%lf", &Eps);
            if (Eps <= 0)
                printf("Accuracy must be greater than 0!\n");
        } while (Eps <= 0);
    }

    // broadcast Size and Eps to all processes
    MPI_Bcast(&Size, 1, MPI_INT,    0, MPI_COMM_WORLD);
    MPI_Bcast(&Eps,  1, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    // compute RowNum for this rank (inner rows + 2 halo rows)
    RestRows = Size - 2;
    for (i = 0; i < ProcRank; i++)
        RestRows = RestRows - RestRows / (ProcNum - i);

    RowNum = RestRows / (ProcNum - ProcRank) + 2;

    // allocate local stripe
    pProcRows = new double[RowNum * Size];

    // allocate and initialize global matrix only on root
    if (ProcRank == 0) {
        pMatrix = new double[Size * Size];
        DummyDataInitialization(pMatrix, Size);
        // або RandomDataInitialization(pMatrix, Size);
    }
}

// Function for exchanging the boundary rows
void ExchangeData(double* pProcRows, int Size, int RowNum) {
    MPI_Status status;
    int NextProcNum = (ProcRank == ProcNum - 1) ? MPI_PROC_NULL : ProcRank + 1;
    int PrevProcNum = (ProcRank == 0)          ? MPI_PROC_NULL : ProcRank - 1;

    MPI_Sendrecv(
        pProcRows + Size * (RowNum - 2), Size, MPI_DOUBLE,
        NextProcNum, 4,
        pProcRows, Size, MPI_DOUBLE,
        PrevProcNum, 4,
        MPI_COMM_WORLD, &status
    );

    MPI_Sendrecv(
        pProcRows + Size, Size, MPI_DOUBLE,
        PrevProcNum, 5,
        pProcRows + (RowNum - 1) * Size, Size, MPI_DOUBLE,
        NextProcNum, 5,
        MPI_COMM_WORLD, &status
    );
}

// Function for the parallel Gauss - Seidel method
void ParallelResultCalculation (double *pProcRows,
                                int Size,
                                int RowNum,
                                double Eps,
                                int &Iterations) {
    double ProcDelta, Delta;
    Iterations = 0;

    do {
        Iterations++;
        ExchangeData(pProcRows, Size, RowNum);
        ProcDelta = IterationCalculation(pProcRows, Size, RowNum);
        MPI_Allreduce(&ProcDelta, &Delta, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);
    } while (Delta > Eps);
}

// Function for gathering the result vector
void ResultCollection(double *pMatrix, double* pProcRows, int Size, int RowNum) {
    int *pReceiveNum = new int[ProcNum];
    int *pReceiveInd = new int[ProcNum];
    int RestRows = Size - 2;

    for (int i = 0; i < ProcNum; i++) {
        int InnerRows = RestRows / (ProcNum - i);
        pReceiveNum[i] = InnerRows * Size;

        if (i == 0)
            pReceiveInd[0] = Size;         // пропускаємо перший граничний рядок
        else
            pReceiveInd[i] = pReceiveInd[i - 1] + pReceiveNum[i - 1];

        RestRows -= InnerRows;
    }

    MPI_Gatherv(
        pProcRows + Size,                 // пропускаємо верхній halo-рядок
        (RowNum - 2) * Size, MPI_DOUBLE,  // надсилаємо лише «реальні» внутрішні рядки
        pMatrix,
        pReceiveNum,
        pReceiveInd,
        MPI_DOUBLE,
        0,
        MPI_COMM_WORLD
    );

    delete [] pReceiveNum;
    delete [] pReceiveInd;
}

// Function for the serial Gauss – Seidel method
void SerialResultCalculation(double *pMatrixCopy, int Size, double Eps, int &Iter){
    int i, j;
    double dm, dmax, temp;
    Iter = 0;
    do {
        dmax = 0;
        for (i = 1; i < Size - 1; i++) {
            for (j = 1; j < Size - 1; j++) {
                temp = pMatrixCopy[Size * i + j];
                pMatrixCopy[Size * i + j] = 0.25 * (
                    pMatrixCopy[Size * i + j + 1] +
                    pMatrixCopy[Size * i + j - 1] +
                    pMatrixCopy[Size * (i + 1) + j] +
                    pMatrixCopy[Size * (i - 1) + j]
                );
                dm = fabs(pMatrixCopy[Size * i + j] - temp);
                if (dmax < dm) dmax = dm;
            }
        }
        Iter++;
    } while (dmax > Eps);
}

// Function to copy the initial data
void CopyData(double *pMatrix, int Size, double *pSerialMatrix) {
    copy(pMatrix, pMatrix + Size * Size, pSerialMatrix);
}

// Function for testing the computation result
void TestResult(double* pMatrix, double* pSerialMatrix, int Size, double Eps) {
    int equal = 0;
    int Iter;
    if (ProcRank == 0) {
        SerialResultCalculation(pSerialMatrix, Size, Eps, Iter);
        for (int i = 0; i < Size * Size; i++) {
            if (fabs(pSerialMatrix[i] - pMatrix[i]) >= Eps * 5.0) {
                equal = 1;
                break;
            }
        }
        if (equal == 1)
            printf("\nThe results of serial and parallel algorithms are NOT identical. Check your code.\n");
        else
            printf("\nThe results of serial and parallel algorithms are identical.\n");
    }
}

int main(int argc, char* argv[]) {
    double* pMatrix       = NULL;
    double* pProcRows     = NULL;
    double* pSerialMatrix = NULL;
    int Size;
    int RowNum;
    double Eps;
    int Iterations;
    double Start, Finish, Duration;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &ProcNum);
    MPI_Comm_rank(MPI_COMM_WORLD, &ProcRank);

    if (ProcRank == 0) {
        printf("Parallel Gauss - Seidel algorithm\n");
        fflush(stdout);
    }

    // interactive init
    ProcessInitialization(pMatrix, pProcRows, Size, RowNum, Eps);

    if (ProcRank == 0) {
        pSerialMatrix = new double[Size * Size];
        CopyData(pMatrix, Size, pSerialMatrix);
    }

    Start = MPI_Wtime();

    DataDistribution(pMatrix, pProcRows, RowNum, Size);

    ParallelResultCalculation(pProcRows, Size, RowNum, Eps, Iterations);

    ResultCollection(pMatrix, pProcRows, Size, RowNum);

    Finish   = MPI_Wtime();
    Duration = Finish - Start;

    if (ProcRank == 0) {
        printf("\nTime of execution: %f seconds\n", Duration);
        TestResult(pMatrix, pSerialMatrix, Size, Eps);

        if (Size <= 20) {
            // printf("\nResult matrix:\n");
            // PrintMatrix(pMatrix, Size, Size);
        }
        delete [] pSerialMatrix;
    }

    ProcessTermination(pMatrix, pProcRows);
    MPI_Finalize();
    return 0;
}
