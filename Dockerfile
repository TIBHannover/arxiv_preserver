FROM ubuntu:21.04

RUN DEBIAN_FRONTEND=noninteractive apt update --fix-missing -y
RUN DEBIAN_FRONTEND=noninteractive apt upgrade -y 
RUN DEBIAN_FRONTEND=noninteractive apt install python3-pip git cmake libboost-python-dev libpoppler-glib-dev build-essential python3-numpy libboost-numpy-dev libboost-program-options-dev libboost-filesystem-dev python3-skimage -y
RUN DEBIAN_FRONTEND=noninteractive apt install libmariadbclient-dev-compat imagemagick -y

COPY /arxiv_makeover /arxiv/arxiv_makeover
COPY /sanity /arxiv/sanity
COPY /manage.py /arxiv/manage.py
COPY /requirements.txt /arxiv/requirements.txt


RUN cd /arxiv/sanity/pdf_renderer/; mkdir build; cd build; cmake ..; make
RUN cd /arxiv; pip install -r requirements.txt
