FROM debian:10

# Add Dependencies for PySpark
RUN apt-get -y update && apt-get install -y curl vim net-tools wget zip make automake gcc g++ subversion python3 python3-venv && mkdir /project_files

# RUN wget https://www.python.org/ftp/python/3.9.13/Python-3.9.13.tgz && tar -xf Python-3.9.13.tgz && cd Python-3.9.13 && ./configure --enable-optimizations && make install 
WORKDIR /project_files
