FROM python:3
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt \
    && apt update && apt install -y python3-numpy python3-cffi python3-aiohttp \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev \
    libswscale-dev libswresample-dev libavfilter-dev libopus-dev \
    libvpx-dev pkg-config libsrtp2-dev python3-opencv pulseaudio
CMD python app.py