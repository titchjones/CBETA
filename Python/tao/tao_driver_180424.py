import os
import numpy as np
import subprocess
import pexpect
import time
import math
import atexit
import multiprocessing
import time
import sys

from matplotlib import pyplot as plt

def parse_plot_data_str(data_str):

  s = []
  x = []

  if(isinstance(data_str,str)):
    lines = data_str.split(",")
  else:
    lines = data_str
  
  for line in lines:
    tokens = line.split(";")

    if(len(tokens)==3):
      s.append(tokens[1])
      x.append(tokens[2])

  return(s,x)
  
  
def parse_plot_data_str2(data_str):

  s = []
  x = []

  el_num = []
  el_name = []
  el_s = []
  beta_a = []
  beta_b = []
  b1_gradient = []
  ir = 0
  
  for ele in data_str[3:]:
     
     el_spl = ele.split()
     if el_spl[0] == 'Index':
     	break
     el_num.append(int(el_spl[0]))
     el_name.append(str(el_spl[1]))
     el_s.append(float(el_spl[3]))
     beta_a.append(float(el_spl[5]))
     beta_b.append(float(el_spl[6]))
     if el_spl[7] == '---':
         b1_gradient.append(None)
     else:
         b1_gradient.append(float(el_spl[7]))
     ir = ir + 1     

  return (el_num, el_name, el_s, beta_a, beta_b, b1_gradient)
  


def start_tao():

  tao = pexpect.spawn("tao -noplot -lat fat.bmad")   # Tao must be in your path, also you should add your lattice file to this too
  tao.expect('Tao>')                             # Trap initial prompt, REPLACE THIS WITH "Tao>" 

  # Do default setting up here, if not in tao.init
  send_command('set global plot_calc_always = T',tao) 

  return tao

def send_command(cmd_str,tao):

  tao.sendline(cmd_str) 
  #tao.expect('CBETA-V>')
  tao.expect('Tao>')

  # Gets data from tao and splits on new lines
  lines = tao.before.decode(encoding='UTF-8').split("\r\n")

  final_lines = []
  for line in lines:
    if(line.strip() != ''): 
      final_lines.append(line.strip())   

  return(final_lines[1:])  # return list of strings


# ---------------------------------------------------------------------------- #
# MAIN
# ---------------------------------------------------------------------------- #
if __name__ == '__main__':

  print("Starting Tao: ") 
  tao = start_tao()  # Start tao and trap it
  
  # Place the data you want on a plot/region/graph, we will be looking at beta functions  
  send_command('place r1 beta',tao) 
  send_command('set plot r1 visible = T',tao)


  #quad_strengths = np.linspace(-0.1,0.1,Npts)   # Just a dummy in this example
  
  
  qs = []
  beta_xf = []  # final beta at end of beamline, for simplicity sake
  beta_yf = []
  
  #retrieve values in nominal lattice
  data_str = send_command("show lat -at beta_a -at beta_b -at B1_gradient", tao)
  data = parse_plot_data_str2(data_str)
  el_name = data[1]
  bet_a = data[3]  # beta-x(s)
  bet_b = data[4]  # beta-x(s)
  b1_grad = data[5]
  
  ms1qua03_ind = el_name.index("S1.PIP04\\MS1QUA03")
  ms1qua04_ind = el_name.index("S1.PIP05\\MS1QUA04")
  ms1qua05_ind = el_name.index("S1.PIP08\\MS1QUA05")
  ms1qua06_ind = el_name.index("S1.PIP09\\MS1QUA06")
  iscr2_ind = el_name.index('IS1SCR02')
  
  #print "quad indices ",ms1qua03_ind, ms1qua04_ind, ms1qua05_ind, ms1qua06_ind
  print "screen index ",iscr2_ind
  
  ms1qua03_betx_nom = bet_a[ms1qua03_ind]
  ms1qua04_betx_nom = bet_a[ms1qua04_ind]
  ms1qua05_betx_nom = bet_a[ms1qua05_ind]
  ms1qua06_betx_nom = bet_a[ms1qua06_ind]
  ms1qua03_bety_nom = bet_b[ms1qua03_ind]
  ms1qua04_bety_nom = bet_b[ms1qua04_ind]
  ms1qua05_bety_nom = bet_b[ms1qua05_ind]
  ms1qua06_bety_nom = bet_b[ms1qua06_ind]
  
  iscr2_betx_nom = bet_a[iscr2_ind]
  iscr2_bety_nom = bet_b[iscr2_ind]
  
  ms1qua03_b1_nom = b1_grad[ms1qua03_ind]
  ms1qua04_b1_nom = b1_grad[ms1qua04_ind]
  ms1qua05_b1_nom = b1_grad[ms1qua05_ind]
  ms1qua06_b1_nom = b1_grad[ms1qua06_ind]
 
  print "nominal betx values at quads 3-6 ",ms1qua03_betx_nom, ms1qua04_betx_nom, ms1qua05_betx_nom, ms1qua06_betx_nom
  print "nominal bety values at quads 3-6 ",ms1qua03_bety_nom, ms1qua04_bety_nom, ms1qua05_bety_nom, ms1qua06_bety_nom
  print "nominal betx, bety values at screen ",iscr2_betx_nom, iscr2_bety_nom
  
  print "nominal b1 at quads 3-6 ",ms1qua03_b1_nom, ms1qua04_b1_nom, ms1qua05_b1_nom, ms1qua06_b1_nom
  
  iselq = 2 #select quad to vary
  
  quad_name_l = ["MS1QUA03","MS1QUA04","MS1QUA05","MS1QUA06"]
  quad_b1_l = [ms1qua03_b1_nom, ms1qua04_b1_nom, ms1qua05_b1_nom, ms1qua06_b1_nom]
  quad_name_sel = quad_name_l[iselq]
  quad_b1_sel = quad_b1_l[iselq]
  
  Npts = 11
  qfac = 0.1
  quad_strengths = np.linspace((1-qfac)*quad_b1_l[iselq],(1+qfac)*quad_b1_l[iselq],Npts)   # Just a dummy in this example
  
  print "select quad ",quad_name_sel, "nominal b1 ",quad_b1_sel

  plt.figure(1)
  
  for q in quad_strengths:
  
    #print("dummy quad scan: ",q)

    #Send a command to tao:
    #send_command("set ele FF.QUA01 B1_GRADIENT = "+str(q),tao)   # replace with whatever you want to tell Tao, like command for setting a quad strength
    send_command("set ele "+quad_name_sel+" B1_GRADIENT = "+str(q),tao)
    #send_command('show ele IS1SCR02',tao)
    # Retrieve your data
    #data_str = send_command('python plot_line r1.g.a',tao)      # <- here this graph component corresponds to the ones set above

    data_str = send_command("show lat -at beta_a -at beta_b -at B1_gradient", tao)
    

    # Parse it (assuming its 2 column data like s-position and beta, for example:
    data = parse_plot_data_str2(data_str)
    
    el_name = data[1]
    s = data[2]  # s-position
    
    bet_a = data[3]  # beta-x(s)
    bet_b = data[4]  # beta-x(s)
    
    

    qs.append(q)
    beta_xf.append(bet_a[iscr2_ind])
    beta_yf.append(bet_b[iscr2_ind])
    
  plt.plot(qs,beta_xf, 'ko-')
  plt.plot(qs,beta_yf, 'ro-')
  
  plt.axvline(x=quad_b1_sel,color='gray')
  plt.ylim(ymin=0)

  plt.show()
    
 





