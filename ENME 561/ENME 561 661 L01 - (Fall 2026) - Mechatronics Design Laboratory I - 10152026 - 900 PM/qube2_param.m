% qube2_param.m
% QUBE-Servo 2 parameters, (c) Quanser Inc. Supplied unchanged below.
% A short ENME 561/661 addition follows the original script.

% Resistance
Rm = 8.4;
% Inductance (H)
Lm = 1.16e-3;
% Current-torque (N-m/A)
kt = 0.042; %0.045;
% Back-emf constant (V-s/rad)
km = 0.042;
% Rotor inertia (kg-m^2)
Jr = 4e-6;
% Hub mass (kg)
mh = 0.0106; % 9 g
% Hub radius (m)
rh = 22.2/1000/2; % diameter 22.2 mm
% Hub inertia (kg-m^2)
Jh = 0.5*mh*rh^2;
% Disc mass (kg)
md = 0.053;
% Disc radius (m)
rd = 49.5/1000/2; % diameter = 49.5 mm
% Disc moment of inertia (kg-m^2)
Jd = 0.5*md*rd^2;
% Equivalent moment of inertia (kg-m^2)
Jeq = Jr + Jh + Jd;

% -----------------------------------------------------------------
% Added for ENME 561/661 - not part of the original Quanser script
% -----------------------------------------------------------------
% Encoder resolution (quadrature counts per revolution)
counts_per_rev = 2048;
% Counts to degrees
K_enc_deg = 360/counts_per_rev;
% Counts to radians
K_enc_rad = 2*pi/counts_per_rev;

% Friction parameters identified in this lab - add your own values here
% Vc   = ... ;   % equivalent Coulomb friction voltage       (V)
% mu   = ... ;   % total viscous coefficient from the fit    (V-s/rad)
% mu_f = ... ;   % viscous friction coefficient              (V-s/rad)
