import math

def newton(fun_handle,y,x0,params={},hfull=1,dh=0.001,tolerance=0.001,maxiter=100,ymax=None):
    def y_at_x(x,dh):
        ym = fun_handle(x - 0.5 * dh, params)
        yp = fun_handle(x + 0.5 * dh, params)
        y0 = 0.5 * (yp + ym)
        e0 = 0.5 * (yp + ym-2*y)
        e = math.fabs(e0)
        dydx = (yp - ym) / dh
        return (y0,ym,yp,e0,e,dydx)
    e = 100 ; i = 0
    x = x0 ; dydx = 1
    h = hfull
    while (e>tolerance) and (i<maxiter):
        (y0,ym,yp,e0,e,dydx) = y_at_x(x,dh)
        if dydx==0:
            dh = 10*dh
        else:
            h = hfull
            step = h *e0 / dydx
            xt = x - step
            (y0, ym, yp, e0, e, dydx) = y_at_x(xt, dh)
            if not ymax is None:
                a = 0
                while (((ym > ymax) or (yp > ymax)) and (a<maxiter)):
                    h = 0.5*h
                    step = h * e0 / dydx
                    xt = x - step
                    (y0, ym, yp, e0, e, dydx) = y_at_x(xt, dh)
                    a = a + 1
            x = xt
        i = i+1
    return (x,e,i)
