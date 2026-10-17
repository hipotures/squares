#pragma once

#include <cstdint>
#include <cstddef>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace sqtopology {

// 128-bit intermediates: limb_carry products and remainder*base sums can
// exceed 2^64 once class sizes or group orders grow past ~1.8e10 (n >= 7),
// so both mul_small and div_small need a wider accumulator.
__extension__ using BigWide = unsigned __int128;

// Minimal exact unsigned big integer, base 10^9 limbs, little-endian.
// Only the operations needed by exact Burnside counting are provided.
// Shared by the direct event oracle (orbit.cpp) and the wreath-product
// class-aggregated counter (wreath.cpp).
class BigUint {
  public:
    BigUint() = default;

    explicit BigUint(std::uint64_t value) {
        while (value > 0) {
            limbs_.push_back(static_cast<std::uint32_t>(value % kBase));
            value /= kBase;
        }
    }

    [[nodiscard]] bool is_zero() const noexcept { return limbs_.empty(); }

    [[nodiscard]] static BigUint power_of_two(unsigned exponent) {
        BigUint result(1);
        for (unsigned step = 0; step < exponent; ++step) {
            result.mul_small(2);
        }
        return result;
    }

    void add_into(const BigUint& other) {
        const std::size_t size = std::max(limbs_.size(), other.limbs_.size());
        limbs_.resize(size, 0);
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < size; ++i) {
            std::uint64_t sum = carry + limbs_[i];
            if (i < other.limbs_.size()) {
                sum += other.limbs_[i];
            }
            if (sum >= kBase) {
                limbs_[i] = static_cast<std::uint32_t>(sum - kBase);
                carry = 1;
            } else {
                limbs_[i] = static_cast<std::uint32_t>(sum);
                carry = 0;
            }
        }
        if (carry != 0) {
            limbs_.push_back(static_cast<std::uint32_t>(carry));
        }
    }

    void mul_small(std::uint64_t factor) {
        if (factor == 0) {
            limbs_.clear();
            return;
        }
        BigWide carry = 0;
        for (auto& limb : limbs_) {
            const BigWide product =
                static_cast<BigWide>(limb) * factor + carry;
            limb = static_cast<std::uint32_t>(product % kBase);
            carry = product / kBase;
        }
        while (carry > 0) {
            limbs_.push_back(static_cast<std::uint32_t>(carry % kBase));
            carry /= kBase;
        }
    }

    // In-place exact division by a small positive divisor; returns the
    // remainder. The caller checks that the remainder is zero where the
    // mathematical value is known to be divisible.
    [[nodiscard]] std::uint64_t div_small(std::uint64_t divisor) {
        if (divisor == 0) {
            throw std::invalid_argument("big integer division by zero");
        }
        std::uint64_t remainder = 0;
        for (std::size_t i = limbs_.size(); i-- > 0;) {
            const BigWide current =
                static_cast<BigWide>(remainder) * kBase + limbs_[i];
            limbs_[i] = static_cast<std::uint32_t>(current / divisor);
            remainder = static_cast<std::uint64_t>(current % divisor);
        }
        trim();
        return remainder;
    }

    [[nodiscard]] std::string to_decimal() const {
        if (limbs_.empty()) {
            return "0";
        }
        std::ostringstream out;
        out << limbs_.back();
        for (std::size_t i = limbs_.size() - 1; i-- > 0;) {
            out << std::setw(9) << std::setfill('0') << limbs_[i];
        }
        return out.str();
    }

    [[nodiscard]] std::uint64_t to_uint64() const {
        std::uint64_t value = 0;
        for (std::size_t i = limbs_.size(); i-- > 0;) {
            value = value * kBase + limbs_[i];
        }
        return value;
    }

  private:
    static constexpr std::uint64_t kBase = 1000000000ULL;

    void trim() {
        while (!limbs_.empty() && limbs_.back() == 0) {
            limbs_.pop_back();
        }
    }

    std::vector<std::uint32_t> limbs_;
};

}  // namespace sqtopology
