import math as m
def newton(fun_handle,y,x0,params = {},h=0.001,tolerance=0.001,maxiter=100,xmin=None):
    i=0
    e=100
    x=x0
    while (e>tolerance) and (i<maxiter):
        em = (fun_handle(x-0.5*h,params))-y
        ep = (fun_handle(x+0.5*h,params))-y
        e0 = .5*(ep+em)
        e = m.fabs(e0)
        dydx = (ep-em) / h
        if dydx==0:
            h = 10*h
        else:
            x = x-e0/dydx
        i = i+1
    return x,e,i


