function [Xs,omega] = direct_trafo(df, fmax, dt, xt)

    
    tmax = 1/df
    t = 0.0:dt:(tmax+dt);
    ncx = size(xt,2);
    nrx = size(xt,1);
    xx = zeros(length(t),ncx);
    
    % transform x - x(end)
    xx(1:nrx,:) = xt - repmat( xt(end,:), nrx, 1 );
    xf = fft(xx) * dt;
    np = min(fmax/df+1, size(xf,1) / 2);
    
    % contribution of x(end) -> x(end) / s
    f = 0.0 : df : ((np-1)*df);
    omega = 2*pi*f;
    Xs = zeros(np,ncx);
    for ki = 1:np
        Xs(ki,:) = 1i*omega(ki)*xf(ki, :) + xt(end,:);
    end
    
   
end