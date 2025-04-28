function test_direct()

    
    a = 1.0;
    b = 0.5;
    tp = 1.0;

    t = linspace(0.0, 10.0, 2000)';
    xt = ftd(t);
    %plot(t, xt);
    
    
    df = 1.0/100;
    fmax = 10;
    [Xn,omega] = direct_trafo(df, fmax, t(2)-t(1), xt);
    
    s = omega * 1i;
    Xs = s.*fld(s);
    plot(omega, real(Xs), omega, imag(Xs), ...
         omega, real(Xn),'+', omega, imag(Xn), 'o');
    axis([0.0 10 -2 2]);
    
    function xt = ftd(t)
        
        % works:
        % xt = (exp(-b*t) - exp(-a*t)) ./ (a - b);
        % works:
        % xt = 1.0 - exp(-a*t);
        
        %xt = ones(size(t));
        %r = (t <= tp);
        %xt(r) = 0.0; % 0.5*(1 - cos(pi*t(r)/tp));
        
        xt = zeros(size(t));
        r = (t <= tp);
        xt(r) = 0.5*(-cos(pi*t(r)/tp) - 1);
    end

    function Xs = fld(s)
        % Xs = 1.0 ./ ((s + a).*(s + b));
        % Xs = 1.0 ./ s - 1.0 ./ (s + a);
        as = pi/tp;
        % Xs = (1.0 - exp(-s*tp)) .* 0.5.*(1.0 - (s.^2 ./ (s.^2 + as^2))) ...
        %     + exp(-s*tp);
        Xs = 0.5.*( -s./(s.^2 + as.^2) - (1.0 ./ s)) .* (1.0 - exp(-s*tp));
    end
    
   
end