import math
from scipy.integrate import solve_ivp

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

"""
scipy.integrate.solve_ivp(fun, t_span, y0, method='RK45', 
    t_eval=None, dense_output=False, events=None, vectorized=False, **options)

fun :
    Right-hand side of the system. The calling signature is fun(t, y). 
    Here t is a scalar, and there are two options for the ndarray y: 
    It can either have shape (n,); then fun must return array_like with shape (n,). 
    Alternatively it can have shape (n, k); 
    then fun must return an array_like with shape (n, k), 
    i.e. each column corresponds to a single column in y. 
    The choice between the two options is determined by vectorized argument (see below).

"""

def rk45_integrate1D(dydt,tmin,tmax,y0):
    result = solve_ivp(dydt,[tmin,tmax],[y0])
    return result.y[0][-1]

def quadratic_roots(a,b,c):
    x_m = math.nan ; x_p = math.nan
    if ((b==0) and (c/a<0)):
        x_m = math.sqrt(-1*c/a)
        x_p = x_m
    else:
        radical = b**2-4*a*c
        if radical >=0:
            x_m = 0.5*1/a *( -b - math.sqrt(radical))
            x_p = 0.5*1/a *( -b + math.sqrt(radical))
    return (x_m,x_p)