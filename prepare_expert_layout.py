"""Losslessly repack original expert tensors into contiguous expert records."""
import hashlib
import json
import os
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent

def main():
    folder=ROOT/'models/olmoe-1b-7b-4bit'
    source=folder/'model.safetensors'
    target=folder/'experts-contiguous.bin'
    index=folder/'experts-contiguous.json'
    fd=os.open(source,os.O_RDONLY)
    try:
        size=struct.unpack('<Q',os.pread(fd,8,0))[0]
        header=json.loads(os.pread(fd,size,8))
        source_hash=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
        if target.exists() and index.exists():
            old=json.loads(index.read_text())
            if old['source_sha256']==source_hash and old['packed_sha256']==hashlib.file_digest(target.open('rb'),'sha256').hexdigest():
                print('Verified existing lossless expert layout');return
        output={};verified=0
        temporary=target.with_suffix('.tmp')
        with temporary.open('wb') as f:
            for layer in range(16):
                for expert in range(64):
                    prefix=f'model.layers.{layer}.mlp.experts.{expert}.'
                    for projection in ('up_proj','gate_proj','down_proj'):
                        for suffix in ('weight','scales','biases'):
                            key=prefix+projection+'.'+suffix
                            meta=header[key];a,b=meta['data_offsets']
                            raw=os.pread(fd,b-a,8+size+a)
                            if len(raw)!=b-a:raise IOError('Short source read')
                            start=f.tell();f.write(raw)
                            output[key]=dict(meta,data_offsets=[start,f.tell()])
            f.flush();os.fsync(f.fileno())
        # Verify every copied tensor against the original bytes, not just file length.
        with temporary.open('rb') as f:
            for key,meta in output.items():
                a,b=meta['data_offsets'];f.seek(a);raw=f.read(b-a)
                c,d=header[key]['data_offsets']
                if raw!=os.pread(fd,d-c,8+size+c):raise ValueError(f'Changed tensor {key}')
                verified+=1
        temporary.replace(target)
        data=dict(source_sha256=source_hash,packed_sha256=hashlib.file_digest(target.open('rb'),'sha256').hexdigest(),
                  verified_tensors=verified,bytes=target.stat().st_size,tensors=output)
        index.write_text(json.dumps(data,indent=2)+'\n')
        print(f'Verified {verified} original tensors; {data["bytes"]} bytes')
    finally:os.close(fd)

if __name__=='__main__':main()
