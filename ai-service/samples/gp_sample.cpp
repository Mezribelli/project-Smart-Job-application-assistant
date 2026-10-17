// Sample GP-style C++ component (representative of NeoXam GP back-office code).
// Used by the code-analysis agent demos and tests.
#include <string>
#include <vector>
#include <cmath>

namespace gp {
namespace accounting {

class PositionValuation {
public:
    PositionValuation(double quantity, double price) : quantity_(quantity), price_(price) {}

    // Market value = quantity * price, rounded to 2 decimals (bankers' rounding).
    double marketValue() const {
        double raw = quantity_ * price_;
        return std::round(raw * 100.0) / 100.0;
    }

    double unrealisedPnl(double costBasis) const {
        if (quantity_ <= 0.0) {
            return 0.0;
        }
        return marketValue() - costBasis * quantity_;
    }

private:
    double quantity_;
    double price_;
};

double navPerShare(double totalAssets, double totalLiabilities, int sharesOutstanding) {
    if (sharesOutstanding == 0) {
        return 0.0;
    }
    double netAssets = totalAssets - totalLiabilities;
    return netAssets / static_cast<double>(sharesOutstanding);
}

}  // namespace accounting
}  // namespace gp
