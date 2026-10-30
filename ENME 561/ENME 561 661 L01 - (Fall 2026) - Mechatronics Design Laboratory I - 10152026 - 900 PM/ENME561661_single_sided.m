% ENME 561/661 - F2026 - Dr. Bisheban
% single_sided_demo.m
% Single-sided amplitude spectrum of DC + 50 Hz + 120 Hz (MathWorks fft example).
% https://www.mathworks.com/help/matlab/ref/openexample.html?websocket=on
clear; clc; close all;

%% 1. Signal
Fs = 1000;                 % sampling frequency (Hz)
L  = 1500;                 % number of samples
t  = (0:L-1)/Fs;           % time vector (s)

S = 0.8 + 0.7*sin(2*pi*50*t) + sin(2*pi*120*t);   % clean signal
X = S + 2*randn(size(t));                          % noisy signal

%% 2. Time domain
figure;
plot(1000*t(1:200), X(1:200)); hold on;
plot(1000*t(1:200), S(1:200), 'LineWidth', 2);
legend('Noisy X(t)', 'Clean S(t)');
xlabel('t (ms)'); ylabel('Amplitude'); title('Time domain'); grid on;

%% 3. Frequency domain, using the function below
figure;
subplot(2,1,1); plot_single_sided(S, Fs, 'Single-sided spectrum of S(t)');
subplot(2,1,2); plot_single_sided(X, Fs, 'Single-sided spectrum of noisy X(t)');

%% ---- Function: compute and plot the single-sided amplitude spectrum ----
function [f, P1] = plot_single_sided(x, Fs, ttl)
    % x   : real signal (vector)
    % Fs  : sampling frequency (Hz)
    % ttl : optional plot title
    if nargin < 3, ttl = 'Single-sided amplitude spectrum'; end

    x  = x(:).';                       % force row vector
    L  = numel(x);

    Y  = fft(x);                       % two-sided DFT
    P2 = abs(Y/L);                     % scale by L, take magnitude
    P1 = P2(1:floor(L/2)+1);           % keep 0 ... Fs/2

    if mod(L,2) == 0
        P1(2:end-1) = 2*P1(2:end-1);   % even L: skip DC and Nyquist
    else
        P1(2:end)   = 2*P1(2:end);     % odd L: no Nyquist bin
    end

    f = Fs*(0:floor(L/2))/L;           % frequency axis (Hz)

    plot(f, P1, 'LineWidth', 2);
    xlabel('f (Hz)'); ylabel('|P1(f)|');
    title(ttl); grid on;
end
