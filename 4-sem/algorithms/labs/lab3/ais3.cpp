#include <iostream>
#include <vector>
#include <algorithm>
#include <numeric>   // для std::gcd
#include <cmath>     // для std::llabs
#include <iomanip>   // для std::setw
using namespace std;

using namespace std;

// Клас раціонального числа
struct Rational {
    long long num, den;

    static long long my_gcd(long long a, long long b) {
        return b == 0 ? a : my_gcd(b, a % b);
    }

    Rational(long long n = 0, long long d = 1) {
        if (d < 0) { n = -n; d = -d; }
        // long long g = gcd(llabs(n), llabs(d));
        long long g = my_gcd(llabs(n), llabs(d));
        num = n / g;
        den = d / g;
    }

    // Перехресне множення для порівняння
    bool operator<(const Rational& other) const {
        return num * other.den < other.num * den;
    }
    bool operator==(const Rational& other) const {
        return num == other.num && den == other.den;
    }

    friend ostream& operator<<(ostream& os, const Rational& r) {
        if (r.den == 1) os << r.num;
        else            os << r.num << '/' << r.den;
        return os;
    }
};

// Вузол BST
struct BSTNode {
    Rational key;
    int freq;
    BSTNode* left;
    BSTNode* right;

    BSTNode(const Rational& k, int f)
        : key(k), freq(f), left(nullptr), right(nullptr) {}
};

// Клас для побудови оптимального BST
class OptimalBST {
    int n;
    vector<Rational> keys;
    vector<int> freq;
    vector<vector<long long>> cost;
    vector<vector<int>>  rootIdx;
    BSTNode* root;

public:
    OptimalBST(const vector<Rational>& k, const vector<int>& f)
        : keys(k), freq(f), root(nullptr)
    {
        n = keys.size();
        // Сортування ключів з частотами
        vector<int> idx(n);
        iota(idx.begin(), idx.end(), 0);
        sort(idx.begin(), idx.end(),
            [&](int a, int b) { return keys[a] < keys[b]; });

        vector<Rational> ks; ks.reserve(n);
        vector<int>       fs; fs.reserve(n);
        for (int i : idx) {
            ks.push_back(keys[i]);
            fs.push_back(freq[i]);
        }
        keys = move(ks);
        freq = move(fs);

        cost.assign(n, vector<long long>(n, 0));
        rootIdx.assign(n, vector<int>(n, 0));
    }

    // Обчислення DP-таблиць і побудова дерева
    void compute() {
        // Ініціалізація одиночних вузлів
        for (int i = 0; i < n; ++i) {
            cost[i][i] = freq[i];
            rootIdx[i][i] = i;
        }

        // Основний цикл по довжині піддерев
        for (int L = 2; L <= n; ++L) {
            for (int i = 0; i + L - 1 < n; ++i) {
                int j = i + L - 1;
                long long sum = 0;
                for (int k = i; k <= j; ++k)
                    sum += freq[k];

                cost[i][j] = LLONG_MAX;
                // Спроба кожного ключа як кореня
                for (int r = i; r <= j; ++r) {
                    long long c = sum;
                    if (r > i) c += cost[i][r - 1];
                    if (r < j) c += cost[r + 1][j];
                    if (c < cost[i][j]) {
                        cost[i][j] = c;
                        rootIdx[i][j] = r;
                    }
                }
            }
        }

        root = buildTree(0, n - 1);
    }

    // Рекурсивне відновлення дерева за таблицею rootIdx
    BSTNode* buildTree(int i, int j) {
        if (i > j) return nullptr;
        int r = rootIdx[i][j];
        BSTNode* node = new BSTNode(keys[r], freq[r]);
        node->left = buildTree(i, r - 1);
        node->right = buildTree(r + 1, j);
        return node;
    }

    // Друк таблиці cost
    void printCostTable() const {
        cout << "Cost table:\n";
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (j < i) cout << "      ";
                else       cout << setw(6) << cost[i][j];
            }
            cout << "\n";
        }
    }

    // Друк таблиці rootIdx
    void printRootTable() const {
        cout << "Root table:\n";
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                if (j < i) cout << "   ";
                else       cout << setw(3) << rootIdx[i][j];
            }
            cout << "\n";
        }
    }

    // Друк in-order обходу
    void inorderTraversal(BSTNode* node) const {
        if (!node) return;
        inorderTraversal(node->left);
        cout << node->key << " ";
        inorderTraversal(node->right);
    }
    void printInorder() const {
        cout << "In-order traversal: ";
        inorderTraversal(root);
        cout << "\n";
    }

    // Вивід дерева боком
    void printTree(BSTNode* node, int depth = 0) const {
        if (!node) return;
        printTree(node->right, depth + 1);
        cout << string(depth * 4, ' ') << node->key << "\n";
        printTree(node->left, depth + 1);
    }
    void printTree() const {
        cout << "Optimal BST structure:\n";
        printTree(root);
    }

    long long getOptimalCost() const {
        return cost[0][n - 1];
    }
};

int main() {
    
    vector<Rational> keys = {
        Rational(3, 2),  // 3/2
        Rational(5, 4),  // 5/4
        Rational(7, 3),  // 7/3
        Rational(8, 5)   // 8/5
    };
    // Частоти для кожного ключа
    vector<int> freq = { 5, 2, 8, 3 };

    OptimalBST obst(keys, freq);
    obst.compute();

    cout << "Optimal BST cost: " << obst.getOptimalCost() << "\n\n";
    obst.printCostTable();
    cout << "\n";
    obst.printRootTable();
    cout << "\n";
    obst.printTree();
    cout << "\n";
    obst.printInorder();

    return 0;
}