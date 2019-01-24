import glob,os
import numpy as np
import matplotlib.pylab as pl
pl.ion()
show_plots=False

N1=16;N2=128;N3=N2


fl=glob.glob('delta_T*Mpc.new')
fl.sort()

ball=[];sall=[]
First=True
z=[];fq=[];fall=[];
for f in fl:
    print 'Working on '+f
    a=np.fromfile(f,dtype='float32')
    if (len(a)==(N1*N2*N3)):
      n=f.index('z')+1;
      z.append(float(f[n:(n+6)]))
      fq.append(1420.4/(1+z[-1]))
      a=np.reshape(a,(N1,N2,N3))  # freq in first axis
      if (First):
       si=a*0
       First=False
      else:
       df=(fq[-2]-fq[-1])/N1
       si=-np.log(a/b)/np.log(fq[-1]/(df+fq[-1]))
      b=a.copy()      
      for n in range(N1):
        ball.append(a[n])
        sall.append(si[n])

z=np.array(z)
fq=[]
for n1 in range(len(z)-1):
    fq.append(np.arange(z[n1],z[n1+1],np.diff(z[n1:(n1+2)])/N1))

fq.append(np.arange(z[-1],z[-1]+np.diff(z[-2:]),+np.diff(z[-2:])/N1))
fq=np.array(fq);
fq=fq.reshape(-1,1)
fq=np.array(fq)
fq=1420.4/(1+fq)

ball=np.array(ball)
sall=np.array(sall)
fall=np.array(fall)

a=[]
f='NGC1566_from_ASKAP12.bin'
if (os.path.isfile(f)):
    a=np.fromfile(f,dtype='float32')
    a=a.reshape(101,128,128)
    ball[0:101]=ball[0:101]+a*1000

for n1 in range(len(fq)):
   pl.figure(1);pl.clf();
   pl.imshow(ball[n1]);pl.title(str(n1)+': '+str(fq[n1]));
   pl.colorbar()
   if (show_plots):
       pl.pause(0.3)
   else:
       pl.savefig('sky_eor_model_f%06.2f.png'%(fq[n1]))

for n1 in range(1,len(sall)): # recalculate SI.
    #   As there is a bug in previous calc which I can not both searching for :)
    #   si=-np.log(a/b)/np.log(fq[-1]/(df+fq[-1]))
    sall[n1]=-np.log(ball[n1]/ball[n1-1])/np.log(fq[n1-1]/fq[n1])
    for n2 in range(N2):
        sall[n1][n2][np.where(np.isnan(sall[n1][n2])==True)]=0

#sall[np.where(np.isnan(sall)==True)]=0
#ball[np.where(np.isnan(ball)==True)]=0

crval=[201,-44];crdel=[6.0/N2,6.0/N3] # reference values in deg
corn_markers=[]
print '##'
print '##  RA,    Dec,   I,    Q,    U,    V,   freq0, spix,  RM,      maj,      min,      pa'
print '## (deg), (deg), (Jy), (Jy), (Jy), (Jy), (Hz), (-), (rad/m^2), (arcsec), (arcsec), (deg)'
print '##'
#201 -44 1.000 0.000000 0.000000 0.000000 1.000000e+08 0.000000 0.000000 54.347520 54.347520 0.000000
corn_markers.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(N2*-0.45)*crdel[0],crval[1]+(N3*-0.45)*crdel[1],1e-3,fq[0]*1e6,0,0,0))
corn_markers.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(N2*-0.45)*crdel[0],crval[1]+(N3*0.45)*crdel[1],1e-3,fq[0]*1e6,0,0,0))
corn_markers.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(N2*0.45)*crdel[0],crval[1]+(N3*-0.45)*crdel[1],1e-3,fq[0]*1e6,0,0,0))
corn_markers.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(N2*0.45)*crdel[0],crval[1]+(N3*0.45)*crdel[1],1e-3,fq[0]*1e6,0,0,0))

#std_dev=np.std(ball,axis=(1,2))*0
n=ball.shape
if (show_plots==False):
  for n1 in range(n[0]):
    print 'Freq Chan: '+str(fq[n1])
    std_dev=np.std(ball[n1])*0
    l=[]
    for n2 in range(n[1]):
        for n3 in range(n[2]):
            if (np.abs(ball[n1][n2][n3])>std_dev):
                l.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(n2-N2/2)*crdel[0],crval[1]+(n3-N3/2)*crdel[1],ball[n1][n2][n3]/1e3,fq[n1]*1e6,sall[n1][n2][n3],crdel[0]/3600,crdel[1]/3600))
            #if (n1<len(a)): ## Now a is added to ball
            #    l.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(n2-N2/2)*crdel[0],crval[1]+(n3-N3/2)*crdel[1],a[n1][n2][n3],1e9,0,crdel[0]/3600,crdel[1]/3600))
    fp=open('sky_eor_model_f%06.2f.osm'%(fq[n1]),'w')
    fp.writelines(corn_markers)
    if (len(l)):
        fp.writelines(l)
    fp.close()
