#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace sqtopology {

using SquareId = std::uint32_t;

enum class FeatureKind : std::uint8_t {
    Corner = 0,
    Side = 1,
};

enum class ContactKind : std::uint8_t {
    CornerCorner = 0,
    CornerSide = 1,
    SideSide = 2,
    Wall = 3,
};

struct FeatureRef {
    SquareId square{};
    FeatureKind kind{FeatureKind::Corner};
    std::uint8_t index{};

    bool operator==(const FeatureRef&) const = default;
};

struct Contact {
    ContactKind kind{ContactKind::CornerCorner};
    FeatureRef a{};
    std::optional<FeatureRef> b{};
    std::optional<std::uint8_t> wall{};

    bool operator==(const Contact&) const = default;
};

struct ValidationResult {
    std::vector<std::string> errors;

    [[nodiscard]] bool ok() const noexcept { return errors.empty(); }
};

struct D4Transform {
    std::uint8_t rotation{};
    bool reflected{};

    bool operator==(const D4Transform&) const = default;
};

class Topology {
  public:
    explicit Topology(std::uint32_t square_count = 0);

    [[nodiscard]] std::uint32_t square_count() const noexcept;
    [[nodiscard]] const std::vector<Contact>& contacts() const noexcept;
    [[nodiscard]] std::vector<Contact>& contacts() noexcept;

    void add_contact(Contact contact);
    [[nodiscard]] ValidationResult validate() const;
    [[nodiscard]] Topology normalized() const;

  private:
    std::uint32_t square_count_{};
    std::vector<Contact> contacts_;
};

[[nodiscard]] Contact make_square_contact(FeatureRef a, FeatureRef b);
[[nodiscard]] Contact make_wall_contact(FeatureRef feature, std::uint8_t wall);

[[nodiscard]] std::string to_string(FeatureKind kind);
[[nodiscard]] std::string to_string(ContactKind kind);
[[nodiscard]] std::string contact_key(const Contact& contact);

[[nodiscard]] std::vector<D4Transform> all_d4_transforms();
[[nodiscard]] FeatureRef transform_feature(FeatureRef feature, D4Transform transform);
[[nodiscard]] std::uint8_t transform_wall(std::uint8_t wall, D4Transform transform);

[[nodiscard]] Topology relabel_square(
    const Topology& topology,
    SquareId square,
    D4Transform transform
);
[[nodiscard]] Topology relabel_container(
    const Topology& topology,
    D4Transform transform
);
[[nodiscard]] Topology permute_squares(
    const Topology& topology,
    const std::vector<SquareId>& old_to_new
);

[[nodiscard]] std::uint8_t feature_ring_index(FeatureRef feature);
[[nodiscard]] FeatureRef feature_from_ring_index(SquareId square, std::uint8_t ring_index);

}  // namespace sqtopology
