"""Tests for quantum_routing.utils.fidelity module."""

import math
import pytest
from quantum_routing.utils.fidelity import (
    transmissivity,
    swap_fidelity,
    path_fidelity,
    fidelity_weight,
)


class TestTransmissivity:
    """Tests for transmissivity = exp(-L / L_att)."""

    def test_zero_length(self):
        """Zero distance should give transmissivity = 1."""
        assert transmissivity(0.0) == pytest.approx(1.0)

    def test_one_attenuation_length(self):
        """At L = L_att, transmissivity = exp(-1) ~ 0.3679."""
        assert transmissivity(22.0, L_att=22.0) == pytest.approx(math.exp(-1))

    def test_custom_attenuation(self):
        """Verify with a custom attenuation length."""
        L, L_att = 50.0, 25.0
        assert transmissivity(L, L_att) == pytest.approx(math.exp(-2.0))

    def test_long_distance_decays(self):
        """Longer distances should give lower transmissivity."""
        t_short = transmissivity(10.0)
        t_long = transmissivity(100.0)
        assert t_short > t_long

    def test_always_positive(self):
        """Transmissivity is always > 0 for finite distances."""
        assert transmissivity(10000.0) > 0


class TestSwapFidelity:
    """Tests for the depolarizing swap model: F_out = f1*f2 + (1-f1)(1-f2)/3."""

    def test_perfect_inputs(self):
        """Swapping two perfect links gives perfect output."""
        assert swap_fidelity(1.0, 1.0) == pytest.approx(1.0)

    def test_symmetric(self):
        """Swap fidelity should be symmetric in f1, f2."""
        assert swap_fidelity(0.9, 0.8) == pytest.approx(swap_fidelity(0.8, 0.9))

    def test_known_value(self):
        """Manual calculation: f1=0.9, f2=0.8 -> 0.9*0.8 + 0.1*0.2/3 = 0.72 + 0.00667."""
        expected = 0.9 * 0.8 + (0.1 * 0.2) / 3
        assert swap_fidelity(0.9, 0.8) == pytest.approx(expected)

    def test_maximally_mixed(self):
        """f1 = f2 = 0.25 (maximally mixed) -> 0.25*0.25 + 0.75*0.75/3 = 0.25."""
        result = swap_fidelity(0.25, 0.25)
        assert result == pytest.approx(0.25)

    def test_one_perfect_one_noisy(self):
        """If one input is perfect, output equals the other."""
        # F_out = 1.0 * f2 + 0 * (1 - f2) / 3 = f2
        assert swap_fidelity(1.0, 0.85) == pytest.approx(0.85)

    def test_output_between_half_and_one(self):
        """For reasonable inputs (> 0.5), output should be > 0.5."""
        result = swap_fidelity(0.9, 0.9)
        assert 0.5 < result <= 1.0


class TestPathFidelity:
    """Tests for end-to-end fidelity along a chain of links."""

    def test_empty_list(self):
        """No links means zero fidelity."""
        assert path_fidelity([]) == 0.0

    def test_single_link(self):
        """Single link: path fidelity = link fidelity."""
        assert path_fidelity([0.95]) == pytest.approx(0.95)

    def test_two_links(self):
        """Two links: should equal one swap."""
        f1, f2 = 0.95, 0.90
        expected = swap_fidelity(f1, f2)
        assert path_fidelity([f1, f2]) == pytest.approx(expected)

    def test_three_links_associativity(self):
        """Three links: sequential swapping (left to right)."""
        f1, f2, f3 = 0.95, 0.90, 0.85
        intermediate = swap_fidelity(f1, f2)
        expected = swap_fidelity(intermediate, f3)
        assert path_fidelity([f1, f2, f3]) == pytest.approx(expected)

    def test_all_perfect(self):
        """All perfect links gives perfect end-to-end."""
        assert path_fidelity([1.0, 1.0, 1.0, 1.0]) == pytest.approx(1.0)

    def test_fidelity_degrades_with_length(self):
        """Longer paths should have lower fidelity (for non-perfect links)."""
        f_short = path_fidelity([0.95, 0.95])
        f_long = path_fidelity([0.95, 0.95, 0.95, 0.95])
        assert f_short > f_long


class TestFidelityWeight:
    """Tests for edge weight = -log(f)."""

    def test_perfect_fidelity(self):
        """Perfect fidelity -> weight = 0."""
        assert fidelity_weight(1.0) == pytest.approx(0.0)

    def test_known_value(self):
        assert fidelity_weight(0.5) == pytest.approx(-math.log(0.5))

    def test_zero_fidelity_gives_inf(self):
        assert fidelity_weight(0.0) == float("inf")

    def test_negative_fidelity_gives_inf(self):
        assert fidelity_weight(-0.1) == float("inf")

    def test_lower_fidelity_higher_weight(self):
        assert fidelity_weight(0.7) > fidelity_weight(0.9)
