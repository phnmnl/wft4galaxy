FROM alpine:3.6

# metadata
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

# allow user defined Git repository
ARG git_url
ARG git_branch

# set the term var
ENV TERM xterm-256color

# wft4galaxy path
ENV WFT4GALAXY_PATH /opt/wft4galaxy

# set Git repository url
ENV WFT4GALAXY_REPOSITORY_URL ${git_url:-"https://github.com/phnmnl/wft4galaxy"}

# wft4galaxy branch
ENV WFT4GALAXY_BRANCH ${git_branch:-develop}

# install base packages
RUN echo "Installing dependencies" >&2 \
    && apk update && apk add \
        bash \
        build-base \
        gcc \
        git \
        iputils \
        make \
        nano \
        py-lxml \
        py-pip \
        py-setuptools \
        python \
        python-dev \
        vim \
    && pip install --upgrade pip \
    && pip install ipython jupyter bash_kernel \
    && echo "Cloning wft4galaxy: branch=${WFT4GALAXY_BRANCH} url=${WFT4GALAXY_REPOSITORY_URL}" >&2 \
    && git clone -b ${WFT4GALAXY_BRANCH} ${WFT4GALAXY_REPOSITORY_URL} ${WFT4GALAXY_PATH} \
    && cd ${WFT4GALAXY_PATH} \
    && pip install -r requirements.txt \
    && python -m bash_kernel.install \
    && echo "Building and installing wft4galaxy" >&2 \
    && python setup.py install \
    && rm -rf /var/cache/apk/*

# setup bash custom prompt (PS1)
ADD bashrc /root/.bashrc

# build a tutorial folder within the user's home
RUN mkdir ${HOME}/tutorial && \
    ln -s ${WFT4GALAXY_PATH}/examples ${HOME}/tutorial/examples && \
    ln -s ${WFT4GALAXY_PATH}/docs/notebooks ${HOME}/tutorial/notebooks && \
    ln -s ${WFT4GALAXY_PATH}/docs/images ${HOME}/tutorial/images

# update the working dir
WORKDIR /root

# add container entrypoint
COPY entrypoint.sh /bin/entrypoint.sh
COPY entrypoint-argparser.sh /usr/local/bin/entrypoint-argparser.sh

# set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
