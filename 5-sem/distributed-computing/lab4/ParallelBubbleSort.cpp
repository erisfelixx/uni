#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <ctime>
#include <cmath>
#include <algorithm>
#include <mpi.h>

using namespace std;

const double RandomDataMultiplier = 1000.0;
int ProcNum = 0; // Number of available processes
int ProcRank = -1; // Rank of current process

// Визначення enum для режиму поділу
enum split_mode {
    KeepFirstHalf, // Зберігати першу половину даних
    KeepSecondHalf // Зберігати другу половину даних
};

void ProcessInitialization(double *&pData, int &DataSize, double *&pProcData, int &BlockSize);
void ProcessTermination(double *pData, double *pProcData);
void DummyDataInitialization(double *&pData, int &DataSize);
void RandomDataInitialization(double *&pData, int &DataSize);
void DataDistribution(double *pData, int DataSize, double *pProcData, int BlockSize);
void DataCollection(double *pData, int DataSize, double *pProcData, int BlockSize);
void ParallelBubble(double *pProcData, int BlockSize);
void ExchangeData(double *pProcData, int BlockSize, int DualRank, double *pDualData, int DualBlockSize);
void TestDistribution(double *pData, int DataSize, double *pProcData, int BlockSize);
void ParallelPrintData(double *pProcData, int BlockSize);
void TestResult(double *pData, double *pSerialData, int DataSize);
void CopyData(double *pData, int DataSize, double *pDataCopy);
bool CompareData(double *pData1, double *pData2, int DataSize);
void SerialBubbleSort(double *pData, int DataSize);
void SerialStdSort(double *pData, int DataSize);
void PrintData(double *pData, int DataSize);

int main(int argc, char *argv[]) {
    double *pData = 0;
    double *pProcData = 0;
    int DataSize = 0;
    int BlockSize = 0;
    double *pSerialData = 0;
    double start, finish;
    double duration = 0.0;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &ProcNum);
    MPI_Comm_rank(MPI_COMM_WORLD, &ProcRank);

    if (ProcRank == 0)
        printf("Parallel bubble sort program\n");

    ProcessInitialization(pData, DataSize, pProcData, BlockSize);

    if (ProcRank == 0) {
        pSerialData = new double[DataSize];
        CopyData(pData, DataSize, pSerialData);
    }

    start = MPI_Wtime();

    DataDistribution(pData, DataSize, pProcData, BlockSize);

    ParallelBubble(pProcData, BlockSize);

    DataCollection(pData, DataSize, pProcData, BlockSize);

    finish = MPI_Wtime();

    duration = finish - start;

    if (ProcRank == 0)
        printf("Time of execution: %f\n", duration);

    if (ProcRank == 0)
        delete[] pSerialData;

    ProcessTermination(pData, pProcData);
    MPI_Finalize();

    return 0;
}

void ProcessInitialization(double *&pData, int &DataSize, double *&pProcData, int &BlockSize) {
    setvbuf(stdout, 0, _IONBF, 0);

    if (ProcRank == 0) {
        do {
            printf("Enter the size of data to be sorted: ");
            scanf("%d", &DataSize);

            if (DataSize < ProcNum)
                printf("Data size should be greater than number of processes\n");
        } while (DataSize < ProcNum);

        printf("Sorting %d data items\n", DataSize);
    }

    MPI_Bcast(&DataSize, 1, MPI_INT, 0, MPI_COMM_WORLD);
    int RestData = DataSize;

    for (int i = 0; i < ProcRank; i++)
        RestData -= RestData / (ProcNum - i);
    BlockSize = RestData / (ProcNum - ProcRank);
    pProcData = new double[BlockSize];

    if (ProcRank == 0) {
        pData = new double[DataSize];
        DummyDataInitialization(pData, DataSize);
    }
}

void ProcessTermination(double *pData, double *pProcData) {
    if (ProcRank == 0)
        delete[] pData;
    delete[] pProcData;
}

void DummyDataInitialization(double *&pData, int &DataSize) {
    for (int i = 0; i < DataSize; i++)
        pData[i] = DataSize - i;
}

void DataDistribution(double *pData, int DataSize, double *pProcData, int BlockSize) {
    int *pSendInd = new int[ProcNum];
    int *pSendNum = new int[ProcNum];
    int RestData = DataSize;
    int CurrentSize = DataSize / ProcNum;

    pSendNum[0] = CurrentSize;
    pSendInd[0] = 0;

    for (int i = 1; i < ProcNum; i++) {
        RestData -= CurrentSize;
        CurrentSize = RestData / (ProcNum - i);
        pSendNum[i] = CurrentSize;
        pSendInd[i] = pSendInd[i - 1] + pSendNum[i - 1];
    }

    MPI_Scatterv(pData, pSendNum, pSendInd, MPI_DOUBLE, pProcData, pSendNum[ProcRank], MPI_DOUBLE, 0, MPI_COMM_WORLD);

    delete[] pSendNum;
    delete[] pSendInd;
}

void DataCollection(double *pData, int DataSize, double *pProcData, int BlockSize) {
    int *pReceiveNum = new int[ProcNum];
    int *pReceiveInd = new int[ProcNum];
    int RestData = DataSize;

    pReceiveInd[0] = 0;
    pReceiveNum[0] = DataSize / ProcNum;

    for (int i = 1; i < ProcNum; i++) {
        RestData -= pReceiveNum[i - 1];
        pReceiveNum[i] = RestData / (ProcNum - i);
        pReceiveInd[i] = pReceiveInd[i - 1] + pReceiveNum[i - 1];
    }

    MPI_Gatherv(pProcData, BlockSize, MPI_DOUBLE, pData, pReceiveNum, pReceiveInd, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    delete[] pReceiveNum;
    delete[] pReceiveInd;
}

void ParallelBubble(double *pProcData, int BlockSize) {
    SerialBubbleSort(pProcData, BlockSize);

    int Offset;
    split_mode SplitMode;

    for (int i = 0; i < ProcNum; i++) {
        if ((i % 2) == 1) {
            Offset = (ProcRank % 2 == 1) ? 1 : -1;
            SplitMode = (ProcRank % 2 == 1) ? KeepFirstHalf : KeepSecondHalf;
        } else {
            Offset = (ProcRank % 2 == 1) ? -1 : 1;
            SplitMode = (ProcRank % 2 == 1) ? KeepSecondHalf : KeepFirstHalf;
        }

        if ((ProcRank == ProcNum - 1 && Offset == 1) || (ProcRank == 0 && Offset == -1))
            continue;

        MPI_Status status;
        int DualBlockSize;

        MPI_Sendrecv(&BlockSize, 1, MPI_INT, ProcRank + Offset, 0, &DualBlockSize, 1, MPI_INT, ProcRank + Offset, 0, MPI_COMM_WORLD, &status);

        double *pDualData = new double[DualBlockSize];
        double *pMergedData = new double[BlockSize + DualBlockSize];

        ExchangeData(pProcData, BlockSize, ProcRank + Offset, pDualData, DualBlockSize);

        merge(pProcData, pProcData + BlockSize, pDualData, pDualData + DualBlockSize, pMergedData);

        if (SplitMode == KeepFirstHalf)
            copy(pMergedData, pMergedData + BlockSize, pProcData);
        else
            copy(pMergedData + BlockSize, pMergedData + BlockSize + DualBlockSize, pProcData);

        delete[] pDualData;
        delete[] pMergedData;
    }
}

void ExchangeData(double *pProcData, int BlockSize, int DualRank, double *pDualData, int DualBlockSize) {
    MPI_Status status;
    MPI_Sendrecv(pProcData, BlockSize, MPI_DOUBLE, DualRank, 0, pDualData, DualBlockSize, MPI_DOUBLE, DualRank, 0, MPI_COMM_WORLD, &status);
}

void CopyData(double *pData, int DataSize, double *pDataCopy) {
    for (int i = 0; i < DataSize; i++)
        pDataCopy[i] = pData[i];
}

bool CompareData(double *pData1, double *pData2, int DataSize) {
    for (int i = 0; i < DataSize; i++)
        if (pData1[i] != pData2[i])
            return false;
    return true;
}

void SerialBubbleSort(double *pData, int DataSize) {
    for (int i = 0; i < DataSize - 1; i++)
        for (int j = 0; j < DataSize - i - 1; j++)
            if (pData[j] > pData[j + 1])
                swap(pData[j], pData[j + 1]);
}

void SerialStdSort(double *pData, int DataSize) {
    sort(pData, pData + DataSize);
}

void PrintData(double *pData, int DataSize) {
    for (int i = 0; i < DataSize; i++)
        printf("%f ", pData[i]);
    printf("\n");
}

