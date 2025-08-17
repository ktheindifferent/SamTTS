#!/usr/bin/env python3
"""
Standalone test script to verify distribution.py improvements.
This can be run without the full TTS test infrastructure.
"""

import sys
import math

# Mock the missing dependencies for testing
class MockTorch:
    """Mock torch module for testing without PyTorch"""
    @staticmethod
    def clamp(x, min=None, max=None):
        if min is not None and x < min:
            return min
        if max is not None and x > max:
            return max
        return x

sys.modules['torch'] = MockTorch()
sys.modules['torch.nn'] = MockTorch()
sys.modules['torch.nn.functional'] = MockTorch()
sys.modules['torch.distributions'] = MockTorch()
sys.modules['torch.distributions.normal'] = MockTorch()
sys.modules['numpy'] = type('MockNumpy', (), {'log': math.log})()

# Now import our module
from TTS.vocoder.utils.distribution import (
    compute_cdf_delta_threshold,
    LOG_STD_MIN_DEFAULT,
    LOG_SCALE_MIN_DEFAULT,
    UNIFORM_EPSILON,
    CDF_EPSILON
)

def test_constants():
    """Test that constants are properly defined."""
    print("Testing constants...")
    assert LOG_STD_MIN_DEFAULT == -7.0, f"Expected -7.0, got {LOG_STD_MIN_DEFAULT}"
    assert abs(LOG_SCALE_MIN_DEFAULT - math.log(1e-14)) < 1e-10, f"LOG_SCALE_MIN_DEFAULT incorrect"
    assert UNIFORM_EPSILON == 1e-5, f"Expected 1e-5, got {UNIFORM_EPSILON}"
    assert CDF_EPSILON == 1e-12, f"Expected 1e-12, got {CDF_EPSILON}"
    print("✓ Constants test passed")

def test_adaptive_threshold():
    """Test adaptive threshold computation."""
    print("\nTesting adaptive threshold computation...")
    
    # Test for 8-bit audio (256 classes)
    threshold_256 = compute_cdf_delta_threshold(256)
    print(f"  Threshold for 256 classes: {threshold_256:.2e}")
    assert 1e-5 <= threshold_256 <= 1e-4, f"256-class threshold out of range: {threshold_256}"
    
    # Test for 16-bit audio (65536 classes)
    threshold_65536 = compute_cdf_delta_threshold(65536)
    print(f"  Threshold for 65536 classes: {threshold_65536:.2e}")
    assert 1e-7 <= threshold_65536 <= 1e-5, f"65536-class threshold out of range: {threshold_65536}"
    
    # Test that threshold decreases with more classes
    assert threshold_256 > threshold_65536, "Threshold should decrease with more classes"
    
    # Test extreme cases
    threshold_small = compute_cdf_delta_threshold(2)
    print(f"  Threshold for 2 classes: {threshold_small:.2e}")
    assert threshold_small <= 1e-4, f"Small class threshold too large: {threshold_small}"
    
    threshold_large = compute_cdf_delta_threshold(1000000)
    print(f"  Threshold for 1000000 classes: {threshold_large:.2e}")
    assert threshold_large >= 1e-7, f"Large class threshold too small: {threshold_large}"
    
    print("✓ Adaptive threshold test passed")

def test_threshold_formula():
    """Test the mathematical formula for threshold computation."""
    print("\nTesting threshold formula...")
    
    # Test specific values
    base_threshold = 1e-5
    base_classes = 256
    
    # For 256 classes, should return base threshold
    threshold = compute_cdf_delta_threshold(256)
    expected = base_threshold / math.sqrt(256 / base_classes)
    assert abs(threshold - expected) < 1e-10, f"Formula mismatch for 256 classes"
    
    # For 1024 classes (4x more), threshold should be halved
    threshold_1024 = compute_cdf_delta_threshold(1024)
    expected_1024 = base_threshold / math.sqrt(1024 / base_classes)
    assert abs(threshold_1024 - expected_1024) < 1e-10, f"Formula mismatch for 1024 classes"
    
    # Verify it's approximately half
    ratio = threshold / threshold_1024
    assert 1.9 < ratio < 2.1, f"Unexpected ratio: {ratio}"
    
    print("✓ Threshold formula test passed")

def test_monotonicity():
    """Test that thresholds decrease monotonically with num_classes."""
    print("\nTesting threshold monotonicity...")
    
    classes = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
    thresholds = [compute_cdf_delta_threshold(n) for n in classes]
    
    print("  Class -> Threshold mapping:")
    for c, t in zip(classes, thresholds):
        print(f"    {c:6d} -> {t:.2e}")
    
    # Check monotonic decrease
    for i in range(len(thresholds) - 1):
        assert thresholds[i] >= thresholds[i + 1], \
            f"Non-monotonic at {classes[i]} -> {classes[i+1]}"
    
    print("✓ Monotonicity test passed")

def main():
    """Run all tests."""
    print("=" * 50)
    print("Testing distribution.py improvements")
    print("=" * 50)
    
    try:
        test_constants()
        test_adaptive_threshold()
        test_threshold_formula()
        test_monotonicity()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED ✓")
        print("=" * 50)
        
        print("\nSummary of improvements:")
        print("1. Replaced magic numbers with named constants")
        print("2. Added adaptive threshold based on num_classes")
        print("3. Documented mathematical reasoning")
        print("4. Improved numerical stability")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()