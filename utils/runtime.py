import time

def get_execution_time(fun_handle,args,kwargs):
    start_time = time.time()
    result = fun_handle(*args,**kwargs)
    sec_elapsed = time.time()-start_time
    return (result,sec_elapsed)