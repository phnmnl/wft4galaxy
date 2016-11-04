FROM wft4galaxy

# metadata
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

# install base packages
RUN apk update && apk add \
    nano \
    vim \
    wget \
    && rm -rf /var/cache/apk/*

# install ipython
RUN pip install --upgrade pip && pip install ipython jupyter

# update entrypoint script
COPY entrypoint.sh /bin/entrypoint.sh
