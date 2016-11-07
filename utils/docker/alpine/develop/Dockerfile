FROM wft4galaxy:alpine

# metadata
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

# install base packages
RUN apk update && apk add \
    nano \
    vim \
    wget \
    && rm -rf /var/cache/apk/*

# install ipython
RUN pip install --upgrade pip && pip install ipython jupyter bash_kernel

# install jupyter bash kernel
RUN python -m bash_kernel.install

# expose jupyter port
EXPOSE 8888

# update entrypoint script
COPY entrypoint.sh /bin/entrypoint.sh
