// Test bridge to the unchanged, separately pinned external verifier.
// Compile with -I pointing at its source directory and the upstream FP flags.
#define main tokoharu_original_main
#include "verify.cpp"
#undef main

int main() {
    std::string operation;
    std::cout << std::hexfloat;
    while (std::cin >> operation) {
        if (operation == "area") {
            R rectangle;
            rectangle.a = readI(std::cin);
            rectangle.b = readI(std::cin);
            rectangle.d = readI(std::cin);
            rectangle.e = readI(std::cin);
            rectangle.rho = I(1);
            I x = readI(std::cin), y = readI(std::cin);
            I c = readI(std::cin), s = readI(std::cin), side = readI(std::cin);
            std::cout << area_lower(rectangle, x, y, c, s, side) << '\n';
        } else if (operation == "slice") {
            I z = readI(std::cin), C = readI(std::cin), O = readI(std::cin);
            I lo = readI(std::cin), hi = readI(std::cin);
            I A1 = readI(std::cin), A2 = readI(std::cin);
            I k1 = readI(std::cin), k2 = readI(std::cin);
            I value = slice(z, C, O, lo, hi, A1, A2, k1, k2);
            std::cout << value.l << ' ' << value.h << '\n';
        } else {
            std::cerr << "unknown probe operation\n";
            return 2;
        }
        if (!std::cin) {
            std::cerr << "truncated probe input\n";
            return 2;
        }
    }
    return 0;
}
