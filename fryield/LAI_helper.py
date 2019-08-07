import fryield.photosynthesis as ps
import pandas as pd

Amin = 0.05 ; Amax = 1
Npts_A = 50
day_min = 5 ; day_max = 365
params = {
        }
A = [Amin + x*(Amax-Amin)/(Npts_A-1) for x in range(Npts_A)]
days = [x for x in range(day_min,day_max)]
cases = [(a,d) for a in A for d in days]

ps.setup()
pct = [ps.LAI_pct_max(x[1],ps_max_molCO2_m2_d=x[0]) for x in cases]

df = pd.DataFrame({'pct':pct,'A':[x[0] for x in cases],'t':[x[1] for x in cases]})
failed = df[df.pct==0].copy()

