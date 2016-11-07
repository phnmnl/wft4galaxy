FROM crs4/wft4galaxy:ubuntu

# metadata
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

# install dev packages
RUN apt-get update && \
    apt-get install -y inetutils-ping nano vim && \
    apt-get -y clean && apt-get -y autoremove && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/*

# install ipython
RUN pip install --upgrade pip && pip install ipython jupyter bash_kernel

# install jupyter bash kernel
RUN python -m bash_kernel.install

# add container entrypoint
COPY entrypoint.sh /bin/entrypoint.sh

# expose jupyter port
EXPOSE 8888

# set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
