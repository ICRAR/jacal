import glob,os,sys
import numpy as np

def_par=[0.0,1500.0,100,'EOR+Foreground/sky_eor_model_f*.osm']
for n in range(1,len(sys.argv)):
    def_par[n-1]=sys.argv[n]

start_f=float(def_par[0]) ## Start overide is MHz
end_f=float(def_par[1]) ## Start overide is MHz
delta_f=int(def_par[2])   ## Number of instances to give Delta Freq in MHz
glob_list=def_par[3] ## model file list

model_list=glob.glob(glob_list)
model_list.sort()
print '#Working from %d models'%(len(model_list))

os.system('cp demo-root.ini demo.ini')

frq=np.zeros((len(model_list))) 
for n in range(len(model_list)): 
  noff=model_list[n].rindex('/')
  frq[n]=model_list[n][(noff+16):(noff+22)] 

if (start_f>end_f):
    n=start_f
    start_f=end_f
    end_f=n

if (frq[0]>start_f):
    start_f=frq[0]

if (frq[-1]<end_f):
    end_f=frq[-1]

delta_f=(end_f-start_f)/delta_f
 
print '#Freq Range (and step) %f %f %f MHz'%(start_f,end_f,delta_f)

start_freq=np.arange(start_f,end_f,step=delta_f)
start_freq=np.array(frq)
IdCount=0
for start_f in start_freq:
    cmd=[]
    use_model=model_list[np.where(frq>=start_f)[0][0]]
    cmd.append('oskar_sim_interferometer --set demo.ini observation/start_frequency_hz %d'%(start_f*1e6))
    cmd.append('oskar_sim_interferometer --set demo.ini observation/num_channels 1')
    cmd.append('oskar_sim_interferometer --set demo.ini observation/frequency_inc_hz %d'%(delta_f*1e6))
    cmd.append('oskar_sim_interferometer --set demo.ini sky/oskar_sky_model/file '+use_model)
    cmd.append('oskar_sim_interferometer --set demo.ini interferometer/ms_filename output/demo_f%08.4f.ms'%(start_f))
    cmd.append('oskar_sim_interferometer demo.ini')
    print '%d "'%(IdCount),
    for line in cmd:
      print '%s;'%(line),
    print '"'
    IdCount=IdCount+1



