FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \ 
&& rm -rf /var/lib/apt/lists/*
RUN pip3 install setuptools
RUN git clone https://github.com/starksimilarity/msf_prompt.git /usr/src/msf_prompt
WORKDIR /usr/src/msf_prompt
RUN python3 setup.py install

