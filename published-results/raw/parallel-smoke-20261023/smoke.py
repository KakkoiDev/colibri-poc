import json,time,urllib.request,concurrent.futures,pathlib
URL='http://127.0.0.1:11549/api/'
def api(p,b):
 return urllib.request.urlopen(urllib.request.Request(URL+p,data=json.dumps(b).encode(),headers={'Content-Type':'application/json'}),timeout=180)
def one(i):
 r={'id':i,'events':[]}; t=time.monotonic()
 with api('chat',dict(model=model,messages=[dict(role='user',content=f'Write a long numbered list of animals, starting with item {i+1}. Keep going.')],think=False,stream=True,keep_alive='5m',options=dict(temperature=0,num_predict=128,num_ctx=2048))) as f:
  for line in f:
   e=json.loads(line)
   if e.get('error'): raise RuntimeError(e['error'])
   if e.get('message',{}).get('content') or e.get('message',{}).get('thinking'): r['events'].append(time.monotonic())
   if e.get('done'): r['tokens']=e.get('eval_count');r['reason']=e.get('done_reason')
 r['seconds']=time.monotonic()-t
 return r
out=[]
for model in ['gemma4:26b','gemma4:26b-mlx','qwen3.8:27b-mlx','gpt-oss:20b']:
 try:
  one(0)
  start=time.monotonic()
  with concurrent.futures.ThreadPoolExecutor(2) as ex: rows=list(ex.map(one,range(2)))
  a,b=rows; overlap=bool(a['events'] and b['events'] and max(a['events'][0],b['events'][0])<min(a['events'][-1],b['events'][-1]))
  result=dict(model=model,clients=2,overlap=overlap,wall_s=time.monotonic()-start,rows=rows)
 except Exception as e: result=dict(model=model,error=str(e))
 out.append(result); pathlib.Path('/tmp/parallel-smoke-results.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'}),flush=True)
 try: api('generate',dict(model=model,keep_alive=0)).close()
 except Exception: pass
