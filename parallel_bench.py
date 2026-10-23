"""Capability gate, then bounded shared-model parallel/context stress on an isolated Ollama."""
import argparse, concurrent.futures, fcntl, json, os, re, shutil, signal, socket, subprocess, threading, time, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def api(url, path, body=None, timeout=180):
    req = urllib.request.Request(url+'/api/'+path, data=None if body is None else json.dumps(body).encode(), headers={'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=timeout))

def overlap_count(rows):
    # Require repeated interleaving of content chunks, not overlapping HTTP lifetimes.
    events = sorted((t, i) for i,r in enumerate(rows) for t in r['events'])
    active = set()
    for i,a in enumerate(rows):
        for j,b in enumerate(rows[:i]):
            if not a['events'] or not b['events']: continue
            lo,hi=max(a['events'][0],b['events'][0]),min(a['events'][-1],b['events'][-1])
            seq=[owner for t,owner in events if lo <= t <= hi and owner in (i,j)]
            if sum(x!=y for x,y in zip(seq,seq[1:])) >= 3: active.update((i,j))
    return len(active)

def swap_mib():
    text=subprocess.check_output(['sysctl','vm.swapusage'],text=True)
    m=re.search(r'used = ([0-9.]+)M',text)
    return float(m[1]) if m else None

def request(url,model,client,ctx,tokens,style):
    # Distinct prefixes avoid measuring only shared-prefix reuse. Actual prompt tokens recorded.
    filler=' '.join(f'word{(j+client*13)%997}' for j in range(ctx//3)) if ctx>2048 else ''
    prompt=f'Conversation {client}. Reference notes: {filler}\nWrite a long numbered list of animals. Keep going.'
    if style=='terse': prompt+=' Use short entries.'
    body=dict(model=model,messages=[dict(role='user',content=prompt)],think=False,stream=True,keep_alive='5m',options=dict(temperature=0,num_ctx=ctx,num_predict=tokens))
    req=urllib.request.Request(url+'/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    start=time.monotonic(); events=[]; parts=[]; final={}
    with urllib.request.urlopen(req,timeout=180) as response:
        for line in response:
            ev=json.loads(line)
            if ev.get('error'): raise RuntimeError(ev['error'])
            msg=ev.get('message',{})
            if msg.get('content') or msg.get('thinking'): events.append(time.monotonic())
            parts.append(msg.get('content',''))
            if ev.get('done'): final=ev
    if not final or not events: raise RuntimeError('Missing streamed output or final telemetry')
    return dict(events=events,text=''.join(parts),tokens=final.get('eval_count',0),prompt_tokens=final.get('prompt_eval_count'),latency_s=time.monotonic()-start,ttft_s=events[0]-start,finish=final.get('done_reason'))

def measure(url,model,n,ctx,tokens,style):
    start=time.monotonic(); before=swap_mib(); peaks=[]; done=threading.Event()
    def sample():
        while not done.is_set():
            try: peaks.append(api(url,'ps',timeout=5))
            except Exception: pass
            done.wait(.5)
    sampler=threading.Thread(target=sample,daemon=True);sampler.start()
    try:
        with concurrent.futures.ThreadPoolExecutor(n) as pool:
            rows=list(pool.map(lambda i:request(url,model,i,ctx,tokens,style),range(n)))
    finally: done.set();sampler.join(timeout=6)
    wall=time.monotonic()-start; after=swap_mib()
    return dict(clients=n,context_limit=ctx,wall_s=wall,total_tok_s=sum(r['tokens'] for r in rows)/wall,
                overlapping_streams=overlap_count(rows),swap_before_mib=before,swap_after_mib=after,
                server_reported_bytes=max((m.get('size',0) for p in peaks for m in p.get('models',[])),default=None),
                memory_note='Ollama reported allocation, not physical peak RAM. Context limit is per request; actual prompt tokens are recorded.',requests=rows)

def run(args):
    if api('http://127.0.0.1:11434','ps')['models']: raise RuntimeError('Owner model is loaded; wait until unloaded. Nothing changed.')
    models=api('http://127.0.0.1:11434','tags')['models']; model=next(m for m in models if m['name']==args.model)
    binary=shutil.which('ollama') or '/Applications/Ollama.app/Contents/Resources/ollama'
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close();url=f'http://127.0.0.1:{port}'
    out=ROOT/'results'/('parallel-bench-'+time.strftime('%Y%m%dT%H%M%S')+'-'+str(os.getpid()));out.mkdir(parents=True)
    env=dict(os.environ,OLLAMA_HOST=f'127.0.0.1:{port}',OLLAMA_NUM_PARALLEL=str(args.max_clients),OLLAMA_MAX_LOADED_MODELS='1',OLLAMA_NOPRUNE='1')
    # Honor the owner's model storage (no downloads); allow explicit environment override.
    if 'OLLAMA_MODELS' not in env and (Path.home()/'models/ollama').exists(): env['OLLAMA_MODELS']=str(Path.home()/'models/ollama')
    summary=dict(model=args.model,digest=model['digest'],status='running',phase='preparing',style=args.style,thinking=False,parallel_slots=args.max_clients,stress=[],busy_machine=True)
    def save(): (out/'summary.json').write_text(json.dumps(summary,indent=2))
    save();server=None
    try:
        with (out/'server.log').open('w') as log:
            server=subprocess.Popen([binary,'serve'],env=env,stdout=log,stderr=log,start_new_session=True)
            for _ in range(100):
                if server.poll() is not None: raise RuntimeError('Isolated server failed; see server.log')
                try: summary['engine']=api(url,'version');break
                except OSError: time.sleep(.1)
            else: raise RuntimeError('Server startup timed out')
            request(url,args.model,0,2048,32,args.style)
            summary['phase']='capability';save()
            gate=measure(url,args.model,2,2048,128,args.style);summary['capability']=gate
            summary['status']='supported' if gate['overlapping_streams']==2 else 'not_supported'
            summary['scope']='Exact model digest, engine version, parallel slots and direct/no-thinking profile on this run. Not a model-intrinsic claim.'
            save();print(f"Capability: {summary['status']}",flush=True)
            if summary['status']=='not_supported' or args.smoke_only: return
            summary['phase']='stress';save()
            for ctx in [2048,8192]:
                for n in [x for x in [2,4,8,16] if x<=args.max_clients]:
                    row=measure(url,args.model,n,ctx,128,args.style);summary['stress'].append(row);save()
                    print(f"{n} clients, context {ctx}: {row['overlapping_streams']} overlapping, {row['total_tok_s']:.1f} tok/s",flush=True)
                    if row['swap_before_mib'] is not None and row['swap_after_mib']-row['swap_before_mib']>128:
                        summary['stress_stop']='Swap increased by more than 128 MiB';return
                    if row['overlapping_streams']<n:
                        summary['stress_stop']='Not all clients showed interleaved output; larger levels skipped';return
    except (Exception,KeyboardInterrupt) as e:
        summary['status']='error';summary['error']=str(e);raise
    finally:
        summary['phase']='failed' if summary['status']=='error' else 'finished'
        save()
        if server is not None:
            try: api(url,'generate',dict(model=args.model,keep_alive=0),timeout=10)
            except Exception: pass
            try: os.killpg(server.pid,signal.SIGTERM);server.wait(timeout=10)
            except (ProcessLookupError,subprocess.TimeoutExpired):
                if server.poll() is None: os.killpg(server.pid,signal.SIGKILL)
        print(out,flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--model',required=True);p.add_argument('--style',choices=['normal','terse'],default='terse');p.add_argument('--max-clients',type=int,choices=[2,4,8,16],default=16);p.add_argument('--smoke-only',action='store_true');args=p.parse_args()
    with (ROOT/'.bench.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        signal.signal(signal.SIGTERM,lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
        run(args)
if __name__=='__main__': main()
