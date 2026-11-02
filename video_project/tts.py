import asyncio, ssl, json, subprocess, edge_tts, edge_tts.communicate as c
c._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
from script import SEG, VOICE
async def one(i, sp, t):
    v = VOICE[sp]
    await edge_tts.Communicate(t, v["voice"], rate=v["rate"], pitch=v["pitch"]).save(f"vo/{i:02d}.mp3")
async def main():
    for i,(sp,t,_,_) in enumerate(SEG):
        for k in range(4):
            try: await one(i,sp,t); break
            except Exception as e: print("retry",i,e); await asyncio.sleep(2)
asyncio.run(main())
durs=[]
for i in range(len(SEG)):
    # trim leading/trailing silence, 48k mono wav
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"vo/{i:02d}.mp3","-af",
      "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse",
      "-ar","48000","-ac","1",f"vo/{i:02d}.wav"],check=True)
    d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"vo/{i:02d}.wav"]))
    durs.append(d)
json.dump(durs,open("vo/durs.json","w"))
print(len(durs), round(sum(durs),1))
