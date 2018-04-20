from epics import caget, caput, cainfo, PV
import re

rmPV = PV('vm0@erp122:r_matrix')
rmvarsPV = PV('vm0@erp122:r_matrix_vars')


rm = rmPV.get()
n, m = rm[0:2]
rm = rm[2:]
print (list(zip(*[iter(rm)]*int(m))))
corrnames = [chr(i) for i in rmvarsPV.get()]
print (re.split("[, \-!?:]+", str.join('', corrnames).rstrip('\x00')))
