#include <iostream>
#include <cstdint>
#include <limits>
#include <functional>

// Функція для обчислення НСД (алгоритм Евкліда) для int64_t
static int64_t gcd_int64(int64_t a, int64_t b) {
    return b == 0 ? (a < 0 ? -a : a) : gcd_int64(b, a % b);
}

// Структура для представлення раціонального числа у вигляді нескоротної дробі
struct Rational {
    int64_t num, den;  // чисельник та знаменник

    // Конструктор: автоматично стискає дріб
    Rational(int64_t n = 0, int64_t d = 1) : num(n), den(d) {
        if (den < 0) { num = -num; den = -den; }
        int64_t g = gcd_int64(num, den);
        num /= g;
        den /= g;
    }

    // Порівняння двох дробів: a/b < c/d <=> a*d < c*b
    bool operator<(const Rational& o) const {
        return num * o.den < o.num * den;
    }
    bool operator==(const Rational& o) const {
        return num == o.num && den == o.den;
    }

    // Вивід у потік: "чисельник/знаменник"
    friend std::ostream& operator<<(std::ostream& os, const Rational& r) {
        return os << r.num << "/" << r.den;
    }
};

// Вузол біноміального дерева
struct Node {
    Rational key;      // ключ вузла
    int degree;        // степінь (кількість дітей)
    Node* parent;      // вказівник на батька
    Node* child;       // вказівник на найлівішого сина
    Node* sibling;     // вказівник на наступного брата

    // Конструктор вузла
    Node(const Rational& k)
        : key(k), degree(0), parent(nullptr), child(nullptr), sibling(nullptr) {}
};

// Клас біноміальної купи (пір?міди)
class BinomialHeap {
    Node* head;  // початок списку коренів

    // Злиття двох впорядкованих списків коренів за степенем
    static Node* mergeLists(Node* a, Node* b) {
        if (!a) return b;
        if (!b) return a;
        Node* head = nullptr;
        Node* tail = nullptr;
        while (a && b) {
            Node* pick = (a->degree < b->degree ? a : b);
            if (pick == a) a = a->sibling;
            else b = b->sibling;
            if (!head) head = tail = pick;
            else { tail->sibling = pick; tail = pick; }
        }
        tail->sibling = a ? a : b;
        return head;
    }

    // Зв'язування двох біноміальних дерев одного порядку: y стає сином z
    static void link(Node* y, Node* z) {
        y->parent = z;
        y->sibling = z->child;
        z->child = y;
        z->degree++;
    }

public:
    // MAKE_HEAP: створення порожньої піраміди
    BinomialHeap() : head(nullptr) {}

    // UNION / merge: злиття двох пірамід
    void merge(BinomialHeap& other) {
        head = mergeLists(head, other.head);
        other.head = nullptr;  // звільнимо іншу купу
        if (!head) return;
        Node* prev = nullptr;
        Node* curr = head;
        Node* next = curr->sibling;
        while (next) {
            if (curr->degree != next->degree ||
                (next->sibling && next->sibling->degree == curr->degree)) {
                // випадок 1 або 2: просто просуваємось
                prev = curr;
                curr = next;
            }
            else if (curr->key < next->key) {
                // випадок 3: curr залишається коренем, next під'єднуємо до curr
                curr->sibling = next->sibling;
                link(next, curr);
            }
            else {
                // випадок 4: next стає новим коренем
                if (!prev) head = next;
                else prev->sibling = next;
                link(curr, next);
                curr = next;
            }
            next = curr->sibling;
        }
    }

    // INSERT: вставка нового ключа в купу
    void insert(const Rational& k) {
        BinomialHeap temp;          // створюємо тимчасову купу
        temp.head = new Node(k);    // дерево B0 з одним вузлом
        merge(temp);                // зливаємо з основною купою
    }

    // FIND_MIN: пошук мінімального ключа
    Rational getMin() const {
        if (!head) throw std::runtime_error("Heap is empty");
        Rational mn = head->key;
        for (Node* x = head->sibling; x; x = x->sibling)
            if (x->key < mn) mn = x->key;
        return mn;
    }

    // EXTRACT_MIN: вилучення мінімального елемента
    Rational extractMin() {
        if (!head) throw std::runtime_error("Heap is empty");
        Node* prevMin = nullptr;
        Node* minNode = head;
        Node* prev = nullptr;
        Rational mn = head->key;
        // знаходимо мінімальний корінь
        for (Node* x = head; x; x = x->sibling) {
            if (x->key < mn) {
                mn = x->key;
                prevMin = prev;
                minNode = x;
            }
            prev = x;
        }
        // видаляємо minNode зі списку коренів
        if (prevMin) prevMin->sibling = minNode->sibling;
        else head = minNode->sibling;
        // створюємо купу з дітей minNode (реверс списку)
        BinomialHeap childHeap;
        for (Node* c = minNode->child; c; ) {
            Node* nxt = c->sibling;
            c->sibling = childHeap.head;
            c->parent = nullptr;
            childHeap.head = c;
            c = nxt;
        }
        delete minNode;
        merge(childHeap);  // зливаємо з основною купою
        return mn;
    }

    // DECREASE_KEY: зменшення ключа в заданому вузлі
    void decreaseKey(Node* x, const Rational& newKey) {
        if (!(newKey < x->key))
            throw std::invalid_argument("New key must be less than current");
        x->key = newKey;
        // піднімаємо вузол вгору, поки інваріант не відновиться
        for (Node* y = x, *z = y->parent; z && y->key < z->key; y = z, z = z->parent)
            std::swap(y->key, z->key);
    }

    // DELETE: видалення довільного вузла через decreaseKey + extractMin
    void deleteNode(Node* x) {
        decreaseKey(x, Rational(std::numeric_limits<int64_t>::min(), 1));
        extractMin();
    }

    // FIND (DFS): пошук вузла за ключем
    Node* find(const Rational& k) {
        std::function<Node* (Node*)> dfs = [&](Node* r) -> Node* {
            if (!r) return nullptr;
            if (r->key == k) return r;
            if (Node* s = dfs(r->child)) return s;
            return dfs(r->sibling);
            };
        return dfs(head);
    }
};


int main() {
    BinomialHeap heap;
    heap.insert(Rational(7, 4));
    heap.insert(Rational(3, 5));
    heap.insert(Rational(1, 3));
    heap.insert(Rational(2, 7));
    heap.insert(Rational(9, 2));
    heap.insert(Rational(4, 9));

    std::cout << "Min: " << heap.getMin() << std::endl;
    Rational ex = heap.extractMin();
    std::cout << "Extracted min: " << ex << std::endl;
    std::cout << "New min: " << heap.getMin() << std::endl;

    Node* n = heap.find(Rational(9, 2));
    if (n) {
        heap.decreaseKey(n, Rational(1, 2));
        std::cout << "After decreaseKey, min: " << heap.getMin() << std::endl;
    }

    // UNION
    BinomialHeap A, B;

    A.insert(Rational(1, 2));  // 1/2
    A.insert(Rational(3, 4));  // 3/4
    A.insert(Rational(2, 5));  // 2/5
    A.insert(Rational(5, 6));  // 5/6

    B.insert(Rational(1, 3));  // 1/3
    B.insert(Rational(4, 7));  // 4/7
    B.insert(Rational(3, 8));  // 3/8
    B.insert(Rational(6, 5));  // 6/5

    std::cout << "Min A: " << A.getMin() << std::endl; // Min A: 1/2
    std::cout << "Min B: " << B.getMin() << std::endl; // Min B: 1/3

    A.merge(B);

    std::cout << "After UNION, min of merged heap: "
        << A.getMin() << std::endl;

    return 0;
}