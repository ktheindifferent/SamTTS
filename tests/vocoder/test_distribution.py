"""
Unit tests for TTS.vocoder.utils.distribution module.

Tests numerical stability, edge cases, and adaptive threshold behavior
for discretized logistic and Gaussian distributions.
"""

import math
import unittest
import torch
import numpy as np
from TTS.vocoder.utils.distribution import (
    gaussian_loss,
    sample_from_gaussian,
    discretized_mix_logistic_loss,
    sample_from_discretized_mix_logistic,
    compute_cdf_delta_threshold,
    log_sum_exp,
    to_one_hot,
    LOG_STD_MIN_DEFAULT,
    LOG_SCALE_MIN_DEFAULT,
    UNIFORM_EPSILON,
    CDF_EPSILON
)


class TestNumericalConstants(unittest.TestCase):
    """Test numerical stability constants."""
    
    def test_default_constants(self):
        """Verify default constants are in expected ranges."""
        assert LOG_STD_MIN_DEFAULT == -7.0
        assert abs(LOG_SCALE_MIN_DEFAULT - np.log(1e-14)) < 1e-10
        assert UNIFORM_EPSILON == 1e-5
        assert CDF_EPSILON == 1e-12
        
    def test_exp_stability(self):
        """Test that exp of minimum values doesn't underflow."""
        assert np.exp(LOG_STD_MIN_DEFAULT) > 0
        assert np.exp(LOG_SCALE_MIN_DEFAULT) > 0


class TestAdaptiveThreshold(unittest.TestCase):
    """Test adaptive CDF delta threshold computation."""
    
    def test_threshold_scaling(self):
        """Test that threshold scales appropriately with num_classes."""
        # For 8-bit audio (256 classes)
        threshold_256 = compute_cdf_delta_threshold(256)
        assert 1e-5 <= threshold_256 <= 1e-4
        
        # For 16-bit audio (65536 classes)
        threshold_65536 = compute_cdf_delta_threshold(65536)
        assert 1e-7 <= threshold_65536 <= 1e-5
        
        # Threshold should decrease as num_classes increases
        assert threshold_256 > threshold_65536
        
    def test_threshold_bounds(self):
        """Test that thresholds are clamped to reasonable bounds."""
        # Very small num_classes
        threshold_small = compute_cdf_delta_threshold(2)
        assert threshold_small <= 1e-4
        
        # Very large num_classes
        threshold_large = compute_cdf_delta_threshold(1000000)
        assert threshold_large >= 1e-7
        
    def test_threshold_continuity(self):
        """Test smooth scaling of thresholds."""
        classes = [128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536]
        thresholds = [compute_cdf_delta_threshold(n) for n in classes]
        
        # Check monotonic decrease
        for i in range(len(thresholds) - 1):
            assert thresholds[i] >= thresholds[i + 1]


class TestGaussianDistribution(unittest.TestCase):
    """Test Gaussian distribution functions."""
    
    def setUp(self):
        """Generate sample data for testing."""
        batch_size, time_steps = 2, 10
        self.y_hat = torch.randn(batch_size, time_steps, 2)
        self.y = torch.randn(batch_size, time_steps, 1)
    
    def test_gaussian_loss_shape(self):
        """Test that Gaussian loss returns correct shape."""
        y_hat, y = self.y_hat, self.y
        loss = gaussian_loss(y_hat, y)
        assert loss.shape == ()  # Scalar
        
    def test_gaussian_loss_numerical_stability(self):
        """Test Gaussian loss with extreme values."""
        y_hat, y = self.y_hat.clone(), self.y
        
        # Test with very small log_std
        y_hat[:, :, 1] = -10.0
        loss = gaussian_loss(y_hat, y)
        assert torch.isfinite(loss)
        
        # Test with very large log_std
        y_hat[:, :, 1] = 10.0
        loss = gaussian_loss(y_hat, y)
        assert torch.isfinite(loss)
        
    def test_gaussian_sampling(self):
        """Test Gaussian sampling."""
        y_hat = self.y_hat
        
        # Test sampling
        samples = sample_from_gaussian(y_hat)
        assert samples.shape == (y_hat.shape[0], y_hat.shape[1], 1)
        
        # Test with scale factor
        samples_scaled = sample_from_gaussian(y_hat, scale_factor=0.5)
        assert torch.all(torch.abs(samples_scaled) <= 0.5)
        
    def test_gaussian_loss_with_custom_min(self):
        """Test Gaussian loss with custom log_std_min."""
        y_hat, y = self.y_hat.clone(), self.y
        y_hat[:, :, 1] = -20.0  # Very small log_std
        
        # Should clamp to custom minimum
        loss = gaussian_loss(y_hat, y, log_std_min=-10.0)
        assert torch.isfinite(loss)


class TestDiscretizedLogistic(unittest.TestCase):
    """Test discretized logistic distribution functions."""
    
    def setUp(self):
        """Generate sample data for testing."""
        batch_size, time_steps, nr_mix = 2, 10, 5
        # 3 parameters per mixture: logit_probs, means, log_scales
        self.y_hat = torch.randn(batch_size, 3 * nr_mix, time_steps)
        self.y = torch.rand(batch_size, 1, time_steps) * 2 - 1  # Range [-1, 1]
    
    def test_discretized_loss_shape(self):
        """Test that discretized loss returns correct shape."""
        y_hat, y = self.y_hat, self.y
        
        # Test with reduction
        loss = discretized_mix_logistic_loss(y_hat, y, reduce=True)
        assert loss.shape == ()  # Scalar
        
        # Test without reduction
        loss = discretized_mix_logistic_loss(y_hat, y, reduce=False)
        assert loss.shape == (y.shape[0], y.shape[2], 1)
        
    def test_discretized_loss_num_classes(self):
        """Test loss with different num_classes."""
        y_hat, y = self.y_hat, self.y
        
        # Test with 8-bit quantization
        loss_8bit = discretized_mix_logistic_loss(y_hat, y, num_classes=256)
        assert torch.isfinite(loss_8bit)
        
        # Test with 16-bit quantization
        loss_16bit = discretized_mix_logistic_loss(y_hat, y, num_classes=65536)
        assert torch.isfinite(loss_16bit)
        
        # Test with very large num_classes
        loss_large = discretized_mix_logistic_loss(y_hat, y, num_classes=1000000)
        assert torch.isfinite(loss_large)
        
    def test_discretized_loss_edge_cases(self):
        """Test loss with edge case inputs."""
        y_hat, y = self.y_hat, self.y.clone()
        
        # Test with y at boundaries
        y[:] = -1.0
        loss_min = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss_min)
        
        y[:] = 1.0
        loss_max = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss_max)
        
        # Test with y near boundaries
        y[:] = -0.999
        loss_near_min = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss_near_min)
        
        y[:] = 0.999
        loss_near_max = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss_near_max)
        
    def test_discretized_sampling(self):
        """Test discretized logistic sampling."""
        y_hat = self.y_hat
        
        # Test sampling
        samples = sample_from_discretized_mix_logistic(y_hat)
        assert samples.shape == (y_hat.shape[0], y_hat.shape[2])
        assert torch.all(samples >= -1.0)
        assert torch.all(samples <= 1.0)
        
    def test_numerical_stability_extreme_scales(self):
        """Test numerical stability with extreme log scales."""
        y_hat, y = self.y_hat.clone(), self.y
        
        # Very small log scales
        y_hat[:, 10:15, :] = -20.0
        loss = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss)
        
        # Very large log scales
        y_hat[:, 10:15, :] = 5.0
        loss = discretized_mix_logistic_loss(y_hat, y)
        assert torch.isfinite(loss)


class TestPrecisionComparison(unittest.TestCase):
    """Test behavior with different floating point precisions."""
    
    def setUp(self):
        """Generate sample data in different precisions."""
        batch_size, time_steps, nr_mix = 2, 10, 5
        
        # Float32 data
        self.y_hat_32 = torch.randn(batch_size, 3 * nr_mix, time_steps, dtype=torch.float32)
        self.y_32 = torch.rand(batch_size, 1, time_steps, dtype=torch.float32) * 2 - 1
        
        # Float64 data
        self.y_hat_64 = self.y_hat_32.double()
        self.y_64 = self.y_32.double()
    
    def test_precision_consistency(self):
        """Test that results are consistent across precisions."""
        y_hat_32, y_32 = self.y_hat_32, self.y_32
        y_hat_64, y_64 = self.y_hat_64, self.y_64
        
        # Test with different num_classes
        for num_classes in [256, 65536]:
            loss_32 = discretized_mix_logistic_loss(y_hat_32, y_32, num_classes=num_classes)
            loss_64 = discretized_mix_logistic_loss(y_hat_64, y_64, num_classes=num_classes)
            
            # Both should be finite
            assert torch.isfinite(loss_32)
            assert torch.isfinite(loss_64)
            
            # Results should be reasonably close
            rel_diff = abs(loss_32.item() - loss_64.item()) / abs(loss_64.item())
            assert rel_diff < 1e-3  # Allow for some precision difference


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions."""
    
    def test_log_sum_exp(self):
        """Test numerically stable log_sum_exp."""
        # Test with values that would overflow naive implementation
        x = torch.tensor([[1000.0, 1001.0, 999.0]])
        result = log_sum_exp(x)
        assert torch.isfinite(result)
        
        # Test with normal values
        x = torch.randn(2, 3, 4)
        result = log_sum_exp(x)
        assert result.shape == (2, 3)
        assert torch.all(torch.isfinite(result))
        
    def test_to_one_hot(self):
        """Test one-hot encoding."""
        tensor = torch.tensor([0, 1, 2, 1])
        n = 3
        
        one_hot = to_one_hot(tensor, n)
        assert one_hot.shape == (4, 3)
        
        # Check correct encoding
        expected = torch.tensor([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0]
        ])
        assert torch.allclose(one_hot, expected)


class TestRegressionCases(unittest.TestCase):
    """Test specific regression cases for known problematic inputs."""
    
    def test_cdf_delta_edge_case(self):
        """Test the specific case mentioned in the TODO comment."""
        # Create data that produces very small CDF delta
        batch_size, time_steps, nr_mix = 1, 1, 1
        y_hat = torch.zeros(batch_size, 3 * nr_mix, time_steps)
        
        # Set parameters to create small CDF delta
        y_hat[0, 0, 0] = 0.0  # logit_prob
        y_hat[0, 1, 0] = 0.0  # mean
        y_hat[0, 2, 0] = -10.0  # very small log_scale
        
        y = torch.zeros(batch_size, 1, time_steps)
        
        # Test with 16-bit audio
        loss = discretized_mix_logistic_loss(y_hat, y, num_classes=65536)
        assert torch.isfinite(loss)
        assert not torch.isnan(loss)
        
    def test_gradient_flow(self):
        """Test that gradients flow properly through the loss."""
        batch_size, time_steps, nr_mix = 2, 10, 5
        y_hat = torch.randn(batch_size, 3 * nr_mix, time_steps, requires_grad=True)
        y = torch.rand(batch_size, 1, time_steps) * 2 - 1
        
        # Test with different num_classes
        for num_classes in [256, 65536]:
            if y_hat.grad is not None:
                y_hat.grad.zero_()
                
            loss = discretized_mix_logistic_loss(y_hat, y, num_classes=num_classes)
            loss.backward()
            
            # Check gradients are finite and non-zero
            assert torch.all(torch.isfinite(y_hat.grad))
            assert torch.any(y_hat.grad != 0)


if __name__ == "__main__":
    unittest.main()