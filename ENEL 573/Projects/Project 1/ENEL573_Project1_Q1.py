"""
Project 1 - Part 1, Question 1
Generate exponential random variables with rate lambda from U(0,1)
using the inverse-transform method:  X = -(1/lambda) * ln(1 - U)
"""
import math
import random
import time

LAMBDA = 75          # rate parameter (lambda)
N_SAMPLES = 1000     # number of samples to generate


def uniform01():
    """Return a U(0,1) sample. random.random() returns a value in [0, 1)."""
    return random.random()


def exponential(lam):
    """Inverse method: F(x) = 1 - e^(-lam*x) = U  =>  x = -ln(1 - U) / lam"""
    u = uniform01()
    return -math.log(1.0 - u) / lam   # 1 - U is in (0, 1], so log never fails


def mean_and_variance(samples):
    """Sample mean and (unbiased) sample variance."""
    n = len(samples)
    mean = sum(samples) / n
    var = sum((x - mean) ** 2 for x in samples) / (n - 1)
    return mean, var


def main():
    random.seed(time.time())   # like srand((unsigned)time(0)): new sequence every run

    # Step 0: check the uniform generator itself (mean 0.5, variance 1/12)
    uni = [uniform01() for _ in range(N_SAMPLES)]
    u_mean, u_var = mean_and_variance(uni)
    print("Uniform U(0,1) check with %d samples" % N_SAMPLES)
    print("  sample mean     = %.6f   (theory 0.5)" % u_mean)
    print("  sample variance = %.6f   (theory 1/12 = %.6f)" % (u_var, 1 / 12))
    print()

    # Step 1: generate 1000 exponential samples with lambda = 75
    samples = [exponential(LAMBDA) for _ in range(N_SAMPLES)]
    mean, var = mean_and_variance(samples)

    # Step 2: compare with theory: E[X] = 1/lambda, Var[X] = 1/lambda^2
    th_mean = 1 / LAMBDA
    th_var = 1 / LAMBDA ** 2
    print("Exponential samples, lambda = %d, n = %d" % (LAMBDA, N_SAMPLES))
    print("  sample mean     = %.6f   theory 1/lambda   = %.6f   error = %.2f%%"
          % (mean, th_mean, 100 * abs(mean - th_mean) / th_mean))
    print("  sample variance = %.8f theory 1/lambda^2 = %.8f error = %.2f%%"
          % (var, th_var, 100 * abs(var - th_var) / th_var))


if __name__ == "__main__":
    main()




