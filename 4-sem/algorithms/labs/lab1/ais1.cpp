#include <vector>
#include <algorithm>
#include <ctime>
#include <cmath>
#include <iostream>

// ---------------------------
// Константи для universal hash
// ---------------------------
struct Constants {
    int a = 0, b = 0, c = 0, k = 0;
    void randomize(int p) {
        a = rand() % p;
        b = rand() % p;
        c = rand() % p;
        k = rand() % 6;
    }
};

// ---------------------------
// Комплексний тип з цілими
// ---------------------------
struct ComplexInt {
    int re = 0, im = 0;
    ComplexInt() = default;
    ComplexInt(int r, int i) : re(r), im(i) {}
    bool operator==(const ComplexInt& o) const {
        return re == o.re && im == o.im;
    }
};

// квадрат модуля
inline long long sqmod(const ComplexInt& z) {
    return 1LL * z.re * z.re + 1LL * z.im * z.im;
}

// порядок: спочатку за модулем, потім за re
bool operator<(const ComplexInt& L, const ComplexInt& R) {
    long long m1 = sqmod(L), m2 = sqmod(R);
    if (m1 != m2) return m1 < m2;
    return L.re < R.re;
}

// перевірка простоти і наступне просте
bool is_prime(int x) {
    if (x < 2) return false;
    for (int i = 2; i * i <= x; ++i)
        if (x % i == 0) return false;
    return true;
}
int next_prime(int n) {
    if (n <= 2) return 2;
    n = (n % 2 == 0 ? n + 1 : n + 2);
    while (!is_prime(n)) n += 2;
    return n;
}

// ---------------------------
// FKS‑таблиця
// ---------------------------
struct PerfectHashTable {
    int p;                          // просте для поля
    size_t N;                       // кількість унікальних ключів
    Constants mainC;                // константи головної хеш‑ф-ї
    Constants* subC;                // константи для кожного вторинного масиву

    // primary collects raw lists; buckets — actual secondary arrays
    std::vector<ComplexInt>* primary;
    std::vector<std::vector<ComplexInt>>* buckets;

    PerfectHashTable(const std::vector<ComplexInt>& keys) {
        // 1) сортуємо й unique
        std::vector<ComplexInt> ks = keys;
        std::sort(ks.begin(), ks.end());
        ks.erase(std::unique(ks.begin(), ks.end()), ks.end());
        N = ks.size();

        primary = new std::vector<ComplexInt>[N];
        buckets = new std::vector<std::vector<ComplexInt>>[N];
        subC = new Constants[N];

        // 2) обираємо p і головні константи
        p = next_prime(int(N * N));
        srand(unsigned(time(nullptr)));
        mainC.randomize(p);

        // 3) розподіл по первинних кошиках
        for (auto& z : ks) {
            // простий лінійний hash на пару (re,im)
            int h = ((mainC.a * z.re + mainC.b * z.im + mainC.c * (z.re < 0 || z.im < 0)) % p + p)
                % p % int(N);
            primary[h].push_back(z);
        }

        // 4) будуємо вторинні масиви
        build_secondary();
    }

    void build_secondary() {
        for (size_t i = 0; i < N; ++i) {
            size_t n = primary[i].size();
            if (n == 0) {
                // лишаємо buckets[i] порожнім
            }
            else if (n == 1) {
                // один елемент — розмір 1, просто помістимо його
                buckets[i].assign(1, std::vector<ComplexInt>());
                buckets[i][0].push_back(primary[i][0]);
            }
            else {
                size_t slots = n * n;
                std::vector<std::vector<ComplexInt>> tmp(slots);
                int tries = 0;
                while (tries++ < 30) {
                    tmp.assign(slots, {});            // очищаємо
                    subC[i].randomize(p);
                    bool ok = true;
                    for (auto& z : primary[i]) {
                        int h2 = ((subC[i].a * z.re + subC[i].b * z.im + subC[i].c * (z.re < 0 || z.im < 0))
                            % p + p) % p % int(slots);
                        if (!tmp[h2].empty()) { ok = false; break; }
                        tmp[h2].push_back(z);
                    }
                    if (ok) { buckets[i] = tmp; break; }
                }
            }
        }
    }

    bool find(const ComplexInt& z) const {
        if (N == 0) return false;
        int h1 = ((mainC.a * z.re + mainC.b * z.im + mainC.c * (z.re < 0 || z.im < 0))
            % p + p) % p % int(N);
        auto& sec = buckets[h1];
        if (sec.empty()) return false;
        if (sec.size() == 1) return sec[0][0] == z;

        int slots = int(sec.size());
        int h2 = ((subC[h1].a * z.re + subC[h1].b * z.im + subC[h1].c * (z.re < 0 || z.im < 0))
            % p + p) % p % slots;
        return !sec[h2].empty() && sec[h2][0] == z;
    }

    void print() const {
        for (size_t i = 0; i < N; ++i) {
            std::cout << "Bucket " << i << ":";
            for (auto& cell : buckets[i]) {
                if (cell.empty()) std::cout << " _";
                else {
                    auto& z = cell[0];
                    std::cout << " {" << z.re << "," << z.im << "}";
                }
            }
            std::cout << "\n";
        }
    }

    ~PerfectHashTable() {
        delete[] primary;
        delete[] buckets;
        delete[] subC;
    }
};

int main() {
    // Задали відразу два вхідні набори ключів:
    std::vector<std::vector<ComplexInt>> dataSets = {
        // перший набір
        { {0,0}, {1,1}, {-1,-1} },
        //другий набір
        { {3,4}, {4,3}, {3,-4}, {4,-3} }
    };

    // Для кожного набору збудуємо й виведемо свою таблицю
    for (size_t idx = 0; idx < dataSets.size(); ++idx) {
        std::cout << "=== Dataset " << idx << " ===\n";
        PerfectHashTable ht(dataSets[idx]);
        ht.print();
        std::cout << "\n";
    }

    return 0;
}
