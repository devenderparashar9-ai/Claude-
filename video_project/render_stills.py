import sys, time
from scenes import SH, Canvas
from PIL import Image
names = sys.argv[1:] or list(SH)
for n in names:
    t=time.time(); cv=Canvas(); SH[n][0](cv); cv.finish().save(f"stills/{n}.png"); print(n, round(time.time()-t,1), flush=True)
