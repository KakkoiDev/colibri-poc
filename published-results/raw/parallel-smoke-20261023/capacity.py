exec(open('/tmp/parallel-smoke.py').read().split('out=[]')[0])
import subprocess,threading,sys
sys.path.insert(0,'~/Code/colibri-poc')
import olmoe_concurrency as h
model='gpt-oss:20b'
one(0)
results=[]
for n in [1,2,4,8,16]:
 before=subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip()
 peaks=[]; stop=threading.Event()
 def sample():
  while not stop.is_set():
   procs=subprocess.check_output(['ps','-axo','pid=,command='],text=True)
   ids=[int(l.split()[0]) for l in procs.splitlines() if '/Applications/Ollama.app/Contents/Resources/ollama runner' in l and '--parallel 16' in l]
   peaks.append(sum(h.footprint_kb(p) for p in ids)/1024**2)
   stop.wait(.3)
 thread=threading.Thread(target=sample);thread.start(); start=time.monotonic()
 try:
  with concurrent.futures.ThreadPoolExecutor(n) as ex: rows=list(ex.map(one,range(n)))
 finally: stop.set();thread.join()
 events=[(t,1) for r in rows if r['events'] for t in [r['events'][0]]]+[(r['events'][-1],-1) for r in rows if r['events']]
 active=maximum=0
 for t,d in sorted(events): active+=d;maximum=max(maximum,active)
 result=dict(clients=n,max_overlapping_streams=maximum,wall_s=time.monotonic()-start,tokens=sum(r['tokens'] for r in rows),runner_footprint_gib=max(peaks,default=0),swap_before=before,swap_after=subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip(),rows=rows)
 results.append(result);pathlib.Path('/tmp/parallel-capacity-results.json').write_text(json.dumps(results,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
api('generate',dict(model=model,keep_alive=0)).close()
