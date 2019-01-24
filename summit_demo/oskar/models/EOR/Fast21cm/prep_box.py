import glob
import numpy as np
import matplotlib.pylab as pl
import os.path

fl=glob.glob('delta_T*Mpc')
fl.sort()
pl.ion()

print 'Find %d files'%(len(fl))
N1=16;N2=128;N3=N2

#b=np.zeros((N1,N2,N3))
for f in fl:
    print 'Working on '+f
    a=np.fromfile(f,dtype='float32')
    if (len(a)==(1024*1024*1024)):
      a=np.reshape(a,(1024,1024,1024))  # freq in first axis
      #a=a.T ## Check this
      aa=a.reshape(N1,1024/N1,N2,1024/N2,N3,1024/N3)
      b=aa.mean(5).mean(3).mean(1)
      n=0
      pl.figure(1)
      pl.clf()
      pl.imshow(a[n])
      pl.title('Original plane %d'%(n))
      pl.figure(2)
      pl.clf()
      n=int(n*N1)/1024
      pl.imshow(b[n])
      pl.title('Sum plane %d: %s'%(n,f))
      pl.pause(0.1)
      fo=f+'.new'
      print 'Writing '+fo
      fo=open(fo,'wb')
      fo.write(b)
      fo.close()

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
       si=np.log(a/b)/np.log(fq[-1]/fq[-2])
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

for n1 in range(len(fq)):
   pl.figure(1);pl.clf();
   pl.imshow(ball[n1]);pl.title(str(n1)+': '+str(fq[n1]));
   pl.savefig('sky_eor_model_f%06.2f.png'%(fq[n1]))

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

a=[]
f='NGC1566_from_ASKAP12.bin'
if (os.path.isfile(f)):
    a=np.fromfile(f,dtype='float32')
    a=a.reshape(128,128,101)
    a=a.T

std_dev=np.std(ball,axis=(1,2))
n=ball.shape
crval=[201,-44];crdel=[6.0/N2,6.0/N3] # reference values in deg
for n1 in range(n[0]):
    l=[]
    for n2 in range(n[1]):
        for n3 in range(n[2]):
            if (ball[n1][n2][n3]>std_dev[n1]):
                l.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(n2-N2/2)*crdel[0],crval[1]+(n3-N3/2)*crdel[1],ball[n1][n2][n3]/1e3,fq[n1]*1e6,sall[n1][n2][n3],crdel[0]/3600,crdel[1]/3600))
                if (n1<len(a)):
                    l.append('%10.8f %10.8f %10.8e 0.0 0.0 0.0 %e %6.3f 0.0 %6.4f %6.4f 0.0\n'%(crval[0]+(n2-N2/2)*crdel[0],crval[1]+(n3-N3/2)*crdel[1],a[n1][n2][n3],1e9,0,crdel[0]/3600,crdel[1]/3600))
    fp=open('sky_eor_model_f%06.2f.osm'%(fq[n1]),'w')
    fp.writelines(corn_markers)
    if (len(l)):
        fp.writelines(l)
    fp.close()
