import os
import re
from django.conf import settings
from rest_framework.views import APIView
from django.http import StreamingHttpResponse, HttpResponse, FileResponse, Http404


class StreamVideo(APIView):
    
    def get(self, request):
        video_path = 'stream_video/videos/nature_video.mp4'
        file_path = os.path.join(settings.STATIC_ROOT, video_path)

        if not os.path.exists(file_path):
            return HttpResponse('File not found', status=404)
        
        file_size = os.path.getsize(file_path)
        range_header = request.headers.get('Range')
        content_type = 'video/mp4'

        if range_header:
            start_byte, end_byte = 0, None

            # Check if the range_header is in the format
            # bytes=100-200
            has_match = re.match(r'bytes=(\d+)-(\d*)', range_header)

            if has_match:
                start_byte, end_byte = has_match.groups()
            
            start_byte = int(start_byte)

            if end_byte:
                end_byte = int(end_byte)
            else:
                end_byte = file_size - 1

            print(f"start_byte: {start_byte}, end_byte: {end_byte}", flush=True)

            # Get the inclusive length of the byte range
            length = end_byte - start_byte + 1

            # Open the file in binary read mode and return the stream
            with open(file_path, 'rb') as file_stream:
                file_stream.seek(start_byte)  # Move pointer to the start_byte position
                data = file_stream.read(length)  # Reads length bytes from start_byte
            
            response = HttpResponse(data, status=206, content_type=content_type)
            response['Content-Length'] = str(length)
            response['Content-Range'] = f'bytes {start_byte}-{end_byte}/{file_size}'
        else:
            response = StreamingHttpResponse(open(file_path, 'rb'), content_type=content_type)
            response['Content-Length'] = str(file_size)

        response['Accept-Ranges'] = 'bytes'
        return response


class ServeMPDFile(APIView):
    def get(self, request, *args, **kwargs):
        mpd_file_path = os.path.join(settings.STATIC_ROOT, 'stream_video', 'segments', 'nature_video.mpd')
        print(mpd_file_path, flush=True)
        if os.path.exists(mpd_file_path):
            return FileResponse(open(mpd_file_path, 'rb'), content_type='application/dash+xml')
        else:
            raise Http404('MPD file not found')


class ServeSegmentFile(APIView):
    def get(self, request, segment_name, *args, **kwargs):
        segment_file_path = os.path.join(settings.STATIC_ROOT, 'stream_video', 'segments', segment_name)
        if os.path.exists(segment_file_path):
            return FileResponse(open(segment_file_path, 'rb'), content_type='video/mp4')
        else:
            raise Http404('Segment file not found')

