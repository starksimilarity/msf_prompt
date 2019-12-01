FROM ubuntu:18.04

RUN apt-get update
RUN apt-get update && apt-get -y install python3
RUN apt-get update && apt-get -y install python3-pip
RUN pip3 install setuptools
RUN apt-get update && apt-get -y install git
RUN git clone https://github.com/starksimilarity/msf_prompt.git /usr/src/msf_prompt
WORKDIR /usr/src/msf_prompt
RUN python3 setup.py install

