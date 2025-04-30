function [tv, xt, yti, fv, ys] = generate_validation()
% [tv, yti, fv, ys] = generate_validation()
% 
%
% generate validation input and reference output for steptransform
%

% constants for simpler 2-dof damped oscillator
%
wtarget = 2*pi/30e-3;
m1 = 0.5;
m2 = 5.0;

ktarget = wtarget^2 * sqrt(m1*m2);
k1 = 0.01*ktarget;
k2 = ktarget;
c1 = 0.1*wtarget;
c2 = 1.0*wtarget;

% input pulse and time discretization
% 
tpulse = 17e-3;
tfinal = 20*tpulse;
dt = tpulse / 192;
tv = 0.0:dt:tfinal;

xt = ones(length(tv),1);
prange = (tv <= tpulse);
xt(prange) = 0.5*(1 - cos( tv(prange)*pi/tpulse ) ); 
xsp = csapi(tv, xt);
xch = 2;

% assemble mechanical system
%
M = zeros(3,3);
K = zeros(3,3);
C = zeros(3,3);

M(1,1) = m1;
M(2,2) = m1 + m2;
M(3,3) = m2;

K(1:2, 1:2) = [k1 -k1; -k1 k1];
K(2:3, 2:3) = K(2:3, 2:3) + [k2 -k2; -k2 k2];

C(1:2, 1:2) = [c1 -c1; -c1 c1];
C(2:3, 2:3) = C(2:3, 2:3) + [c2 -c2; -c2 c2];

M = M(1:2, 1:2)
K = K(1:2, 1:2)
C = C(1:2, 1:2)

% first-order representation f = A*dot(z) + B*z
%
A = [ M zeros(2); zeros(2) eye(2) ]
B = [ C K ; -eye(2) zeros(2) ]

eig(-A \ B)

[tout, yt] = ode45(@zdot, tv, zeros(4,1));
plot(tout, yt(:,3), tout, yt(:,4));

    function zd = zdot(t, z)
        f = zeros(4,1);
        f(xch) = fnval(xsp, t);
        zd = A \ (f - B*z);
    end

% export transfer function
%
s = 1i*linspace(0.0, 2*pi/tpulse, 100)';
a = pi/tpulse
ns = length(s);
xs = zeros(2,1);
xs(xch) = 1;
ys = zeros(ns,2);
for ki = 1:ns
    si = s(ki);
    ys(ki,:) = (M*si^2 + C*si + K) \ xs;
end

    function fs = fhat(si)
        et1 = (1 - exp(-tpulse*si));
        et2 = 1 / (si.^2 + a^2);
        fs = 0.5*et1.*(1.0 ./ si - si.*et2) + exp(-tpulse*si)./si;
    end

% write files
% 
tv = tv';
yti = interp1(tout, yt(:,3:4), tv, 'spline');
tref = [tv xt yti];
save 'treference.txt' -ascii tref

fv = imag(s);
sref = [fv real(ys) imag(ys)];
save 'sreference.txt' -ascii sref

% write parameters
% 
fid = fopen('validation.cfg', 'w');
fprintf(fid, 'ValidationInput = treference.txt\n');
fprintf(fid, 'PulseLength = %f\n', tpulse);
fprintf(fid, 'MaxOutFrequency = %f\n', max(imag(s))/(2*pi));
fprintf(fid, 'SampleCount = %d\n', length(tv));
fprintf(fid, 'ChannelCount = %d\n', size(yti, 2));

end


