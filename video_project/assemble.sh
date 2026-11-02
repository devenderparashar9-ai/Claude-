set -e
ls parts/*.mp4 | sort | sed "s/^/file '/;s/$/'/" > parts.txt
mkdir -p /home/user/Claude-/output
ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -i mix.wav \
  -vf "ass=captions.ass:fontsdir=fonts,format=yuv420p" -r 30 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.2 -maxrate 16M -bufsize 32M \
  -c:a aac -b:a 192k -ar 48000 -map 0:v -map 1:a -shortest -movflags +faststart \
  /home/user/Claude-/output/Lakshmi_Puja_Ki_Mithai_1080x1920.mp4
