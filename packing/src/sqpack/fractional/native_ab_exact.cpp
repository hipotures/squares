/* Header-only Boost.Multiprecision; no fixed-width approximation or FP math.
 * Contexts are immutable after creation. All functions are single-threaded.
 * Exceptions never cross the C ABI. Strings are decimal integers, not code.
 */
#include <boost/multiprecision/cpp_int.hpp>
#include <cstdlib>
#include <cstring>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using boost::multiprecision::cpp_int;
namespace {
thread_local std::string error_text;
cpp_int gcd(cpp_int a, cpp_int b) {
    if (a < 0) a = -a;
    if (b < 0) b = -b;
    while (b != 0) { cpp_int r = a % b; a = b; b = r; }
    return a;
}
struct Slab { cpp_int a, b, lo, hi; };
struct Entry { Slab first, second; cpp_int num, den, weight; };
struct Point { cpp_int x, y, den; };
struct Depth {
    std::vector<Entry> entries;
    cpp_int scale = 1;
};
bool covers(const Slab &s, const Point &p) {
    const cpp_int projection = s.a * p.x + s.b * p.y;
    return projection >= s.lo * p.den && projection <= s.hi * p.den;
}
cpp_int at(const Depth &d, const Point &p) {
    cpp_int value = 0;
    for (const auto &e : d.entries)
        if (covers(e.first, p) && covers(e.second, p)) value += e.weight;
    return value;
}
char *encode(cpp_int num, cpp_int den) {
    const cpp_int divisor = gcd(num, den);
    num /= divisor; den /= divisor;
    const std::string value = num.str() + "/" + den.str();
    char *out = static_cast<char *>(std::malloc(value.size() + 1));
    if (!out) throw std::bad_alloc();
    std::memcpy(out, value.c_str(), value.size() + 1);
    return out;
}
}
extern "C" {
int ab_exact_version() { return 1; }
const char *ab_exact_error() { return error_text.c_str(); }
void ab_exact_free_string(void *p) { std::free(p); }
void ab_exact_destroy(void *p) { delete static_cast<Depth *>(p); }
void *ab_exact_create(const char *text) {
    try {
        error_text.clear();
        if (!text) throw std::invalid_argument("missing depth input");
        std::istringstream input(text);
        size_t count = 0;
        if (!(input >> count) || count > 1000000)
            throw std::invalid_argument("invalid depth count");
        Depth value;
        value.entries.reserve(count);
        for (size_t i = 0; i < count; ++i) {
            Entry e;
            if (!(input >> e.first.a >> e.first.b >> e.first.lo >> e.first.hi
                        >> e.second.a >> e.second.b >> e.second.lo >> e.second.hi
                        >> e.num >> e.den) || e.den <= 0)
                throw std::invalid_argument("invalid slab or weight denominator");
            value.scale = (value.scale / gcd(value.scale, e.den)) * e.den;
            value.entries.push_back(std::move(e));
        }
        std::string trailing;
        if (input >> trailing) throw std::invalid_argument("trailing depth data");
        for (auto &e : value.entries) e.weight = e.num * (value.scale / e.den);
        return new Depth(std::move(value));
    } catch (const std::exception &e) { error_text = e.what(); return nullptr; }
      catch (...) { error_text = "unknown native depth error"; return nullptr; }
}
/* mode=0 sums point depths (also handles a single at query); mode=1 returns
 * the maximum. Empty queries return zero, matching the Python reference.
 */
void *ab_exact_query(const void *context, const char *text, int mode) {
    try {
        error_text.clear();
        if (!context || !text || (mode != 0 && mode != 1))
            throw std::invalid_argument("invalid depth query");
        const Depth &d = *static_cast<const Depth *>(context);
        std::istringstream input(text);
        size_t count = 0;
        if (!(input >> count) || count > 1000000)
            throw std::invalid_argument("invalid point count");
        cpp_int result = 0;
        for (size_t i = 0; i < count; ++i) {
            Point p;
            if (!(input >> p.x >> p.y >> p.den) || p.den <= 0)
                throw std::invalid_argument("invalid point denominator");
            cpp_int value = at(d, p);
            if (mode == 0) result += value;
            else if (i == 0 || value > result) result = value;
        }
        std::string trailing;
        if (input >> trailing) throw std::invalid_argument("trailing query data");
        return encode(result, d.scale);
    } catch (const std::exception &e) { error_text = e.what(); return nullptr; }
      catch (...) { error_text = "unknown native query error"; return nullptr; }
}
}
