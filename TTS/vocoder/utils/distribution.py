import math

import numpy as np
import torch
import torch.nn.functional as F
from torch.distributions.normal import Normal

# Numerical stability constants for Gaussian distributions
LOG_STD_MIN_DEFAULT = -7.0  # Prevents numerical underflow in exp(-7) ≈ 9e-4

# Numerical stability constants for discretized logistic distributions
LOG_SCALE_MIN_DEFAULT = float(np.log(1e-14))  # Prevents numerical underflow
UNIFORM_EPSILON = 1e-5  # Small epsilon for uniform sampling boundaries
CDF_EPSILON = 1e-12  # Minimum value for cdf_delta to prevent log(0)

# Adaptive threshold computation for CDF delta based on num_classes
# Mathematical basis: As num_classes increases, the bin width (2/(num_classes-1))
# decreases, requiring smaller thresholds to maintain numerical precision.
# The threshold scales inversely with sqrt(num_classes) to balance precision and stability.
def compute_cdf_delta_threshold(num_classes):
    """
    Compute adaptive threshold for CDF delta based on number of classes.
    
    For small num_classes (e.g., 256), larger threshold (1e-5) is sufficient.
    For large num_classes (e.g., 65536), smaller threshold is needed for precision.
    
    The formula: threshold = base_threshold / sqrt(num_classes / base_classes)
    ensures smooth scaling between different quantization levels.
    
    Args:
        num_classes (int): Number of quantization levels
    
    Returns:
        float: Adaptive threshold for CDF delta comparison
    """
    base_threshold = 1e-5
    base_classes = 256
    
    # Scale threshold inversely with square root of num_classes ratio
    # This provides good balance between numerical stability and precision
    scale_factor = math.sqrt(num_classes / base_classes)
    adaptive_threshold = base_threshold / scale_factor
    
    # Clamp to reasonable bounds to prevent extreme values
    return max(1e-7, min(1e-4, adaptive_threshold))


def gaussian_loss(y_hat, y, log_std_min=None):
    """
    Compute Gaussian negative log-likelihood loss.
    
    Args:
        y_hat (Tensor): Predicted parameters [B, T, 2] where [:,:,0] is mean, [:,:,1] is log_std
        y (Tensor): Target values [B, T, 1]
        log_std_min (float): Minimum log standard deviation for numerical stability
    
    Returns:
        Tensor: Mean negative log-likelihood
    """
    if log_std_min is None:
        log_std_min = LOG_STD_MIN_DEFAULT
        
    assert y_hat.dim() == 3
    assert y_hat.size(2) == 2
    
    mean = y_hat[:, :, :1]
    log_std = torch.clamp(y_hat[:, :, 1:], min=log_std_min)
    
    # Using PyTorch distribution for better numerical stability
    dist = Normal(mean, torch.exp(log_std))
    log_probs = dist.log_prob(y)
    
    return -log_probs.squeeze().mean()


def sample_from_gaussian(y_hat, log_std_min=None, scale_factor=1.0):
    """
    Sample from Gaussian distribution with numerical stability.
    
    Args:
        y_hat (Tensor): Parameters [B, T, 2] where [:,:,0] is mean, [:,:,1] is log_std
        log_std_min (float): Minimum log standard deviation for stability
        scale_factor (float): Clipping range [-scale_factor, scale_factor]
    
    Returns:
        Tensor: Sampled values
    """
    if log_std_min is None:
        log_std_min = LOG_STD_MIN_DEFAULT
        
    assert y_hat.size(2) == 2
    mean = y_hat[:, :, :1]
    log_std = torch.clamp(y_hat[:, :, 1:], min=log_std_min)
    dist = Normal(
        mean,
        torch.exp(log_std),
    )
    sample = dist.sample()
    sample = torch.clamp(torch.clamp(sample, min=-scale_factor), max=scale_factor)
    del dist
    return sample


def log_sum_exp(x):
    """numerically stable log_sum_exp implementation that prevents overflow"""
    # TF ordering
    axis = len(x.size()) - 1
    m, _ = torch.max(x, dim=axis)
    m2, _ = torch.max(x, dim=axis, keepdim=True)
    return m + torch.log(torch.sum(torch.exp(x - m2), dim=axis))


# It is adapted from https://github.com/r9y9/wavenet_vocoder/blob/master/wavenet_vocoder/mixture.py
def discretized_mix_logistic_loss(y_hat, y, num_classes=65536, log_scale_min=None, reduce=True):
    """
    Compute discretized mixture of logistics loss.
    
    This loss is designed for modeling discrete outputs (e.g., audio samples)
    using a mixture of logistic distributions. The discretization handles
    the fact that continuous distributions are modeling discrete values.
    
    Args:
        y_hat (Tensor): Predicted mixture parameters [B, 3*nr_mix, T]
        y (Tensor): Target values in range [-1, 1] [B, 1, T]
        num_classes (int): Number of discrete levels (e.g., 256 for 8-bit, 65536 for 16-bit)
        log_scale_min (float): Minimum log scale for numerical stability
        reduce (bool): Whether to reduce to scalar loss
    
    Returns:
        Tensor: Negative log-likelihood loss
    """
    if log_scale_min is None:
        log_scale_min = LOG_SCALE_MIN_DEFAULT
    y_hat = y_hat.permute(0, 2, 1)
    assert y_hat.dim() == 3
    assert y_hat.size(1) % 3 == 0
    nr_mix = y_hat.size(1) // 3

    # (B x T x C)
    y_hat = y_hat.transpose(1, 2)

    # unpack parameters. (B, T, num_mixtures) x 3
    logit_probs = y_hat[:, :, :nr_mix]
    means = y_hat[:, :, nr_mix : 2 * nr_mix]
    log_scales = torch.clamp(y_hat[:, :, 2 * nr_mix : 3 * nr_mix], min=log_scale_min)

    # B x T x 1 -> B x T x num_mixtures
    y = y.expand_as(means)

    centered_y = y - means
    inv_stdv = torch.exp(-log_scales)
    plus_in = inv_stdv * (centered_y + 1.0 / (num_classes - 1))
    cdf_plus = torch.sigmoid(plus_in)
    min_in = inv_stdv * (centered_y - 1.0 / (num_classes - 1))
    cdf_min = torch.sigmoid(min_in)

    # log probability for edge case of 0 (before scaling)
    # equivalent: torch.log(F.sigmoid(plus_in))
    log_cdf_plus = plus_in - F.softplus(plus_in)

    # log probability for edge case of 255 (before scaling)
    # equivalent: (1 - F.sigmoid(min_in)).log()
    log_one_minus_cdf_min = -F.softplus(min_in)

    # probability for all other cases
    cdf_delta = cdf_plus - cdf_min

    mid_in = inv_stdv * centered_y
    # log probability in the center of the bin, to be used in extreme cases
    # (not actually used in our code)
    log_pdf_mid = mid_in - log_scales - 2.0 * F.softplus(mid_in)

    # tf equivalent

    # log_probs = tf.where(x < -0.999, log_cdf_plus,
    #                      tf.where(x > 0.999, log_one_minus_cdf_min,
    #                               tf.where(cdf_delta > 1e-5,
    #                                        tf.log(tf.maximum(cdf_delta, 1e-12)),
    #                                        log_pdf_mid - np.log(127.5))))

    # Adaptive threshold selection based on num_classes
    # The threshold needs to be smaller for higher bit depths to maintain precision
    # while avoiding numerical instability from very small CDF differences
    cdf_threshold = compute_cdf_delta_threshold(num_classes)
    
    # When CDF delta is very small, we use the log PDF at the bin center
    # as an approximation to avoid numerical issues with log(very_small_number)
    inner_inner_cond = (cdf_delta > cdf_threshold).float()

    inner_inner_out = inner_inner_cond * torch.log(torch.clamp(cdf_delta, min=CDF_EPSILON)) + (1.0 - inner_inner_cond) * (
        log_pdf_mid - np.log((num_classes - 1) / 2)
    )
    inner_cond = (y > 0.999).float()
    inner_out = inner_cond * log_one_minus_cdf_min + (1.0 - inner_cond) * inner_inner_out
    cond = (y < -0.999).float()
    log_probs = cond * log_cdf_plus + (1.0 - cond) * inner_out

    log_probs = log_probs + F.log_softmax(logit_probs, -1)

    if reduce:
        return -torch.mean(log_sum_exp(log_probs))
    return -log_sum_exp(log_probs).unsqueeze(-1)


def sample_from_discretized_mix_logistic(y, log_scale_min=None):
    """
    Sample from discretized mixture of logistic distributions.
    
    Uses the Gumbel-Max trick for sampling from categorical distributions
    and inverse CDF sampling for the logistic components.
    
    Args:
        y (Tensor): Mixture parameters [B, 3*nr_mix, T]
        log_scale_min (float): Minimum log scale for numerical stability
    
    Returns:
        Tensor: Samples in range [-1, 1]
    """
    if log_scale_min is None:
        log_scale_min = LOG_SCALE_MIN_DEFAULT
    assert y.size(1) % 3 == 0
    nr_mix = y.size(1) // 3

    # B x T x C
    y = y.transpose(1, 2)
    logit_probs = y[:, :, :nr_mix]

    # sample mixture indicator from softmax using Gumbel-Max trick
    temp = logit_probs.data.new(logit_probs.size()).uniform_(UNIFORM_EPSILON, 1.0 - UNIFORM_EPSILON)
    temp = logit_probs.data - torch.log(-torch.log(temp))
    _, argmax = temp.max(dim=-1)

    # (B, T) -> (B, T, nr_mix)
    one_hot = to_one_hot(argmax, nr_mix)
    # select logistic parameters
    means = torch.sum(y[:, :, nr_mix : 2 * nr_mix] * one_hot, dim=-1)
    log_scales = torch.clamp(torch.sum(y[:, :, 2 * nr_mix : 3 * nr_mix] * one_hot, dim=-1), min=log_scale_min)
    # sample from logistic using inverse CDF & clip to interval
    # Note: we don't round to discrete values during sampling for differentiability
    u = means.data.new(means.size()).uniform_(UNIFORM_EPSILON, 1.0 - UNIFORM_EPSILON)
    x = means + torch.exp(log_scales) * (torch.log(u) - torch.log(1.0 - u))

    x = torch.clamp(torch.clamp(x, min=-1.0), max=1.0)

    return x


def to_one_hot(tensor, n, fill_with=1.0):
    # we perform one hot encore with respect to the last axis
    one_hot = torch.FloatTensor(tensor.size() + (n,)).zero_().type_as(tensor)
    one_hot.scatter_(len(tensor.size()), tensor.unsqueeze(-1), fill_with)
    return one_hot
