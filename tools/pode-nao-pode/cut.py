import json,subprocess,sys
src,out,keep=sys.argv[1],sys.argv[2],json.loads(sys.argv[3])
fv=';'.join(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={b-a-0.04:.3f}:d=0.04[a{i}]" for i,(a,b) in enumerate(keep))
cc=''.join(f"[v{i}][a{i}]" for i in range(len(keep)))
fc=fv+f";{cc}concat=n={len(keep)}:v=1:a=1[v][a]"
subprocess.run(['ffmpeg','-v','error','-y','-i',src,'-filter_complex',fc,'-map','[v]','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','16','-c:a','aac','-b:a','160k',out],check=True)
