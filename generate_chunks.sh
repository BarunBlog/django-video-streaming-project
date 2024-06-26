#!/bin/bash

# Ensure the static directory exists
mkdir -p ./stream_video/static/stream_video/segments

# Check if the DASH manifest file already exists
if [ -f ./stream_video/static/stream_video/segments/nature_video.mpd ]; then
    echo "DASH manifest and chunks already exist. Skipping FFmpeg processing."
else
    echo "Generating DASH manifest and chunks with FFmpeg."
    # Run the FFmpeg command
    ffmpeg -i ./stream_video/static/stream_video/videos/nature_video.mp4 -map 0 -b:v 2400k -s:v 1920x1080 -c:v libx264 -an -f dash ./stream_video/static/stream_video/segments/nature_video.mpd
fi
