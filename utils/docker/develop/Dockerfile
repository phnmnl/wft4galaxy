FROM ubuntu:14.04

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
RUN \
       echo "Installing packages" \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
         git \
         inetutils-ping \
         libyaml-dev \
         nano \
         python3-dev \
         python3-lxml \
         python3-pip \
         vim \
    && echo "Installing ipython and jupyter" \
    && pip3 install --upgrade pip


RUN pip3 install ipython bash_kernel

RUN echo "Cloning and installing wft4galaxy" \
    && git clone -b ${WFT4GALAXY_BRANCH} ${WFT4GALAXY_REPOSITORY_URL} ${WFT4GALAXY_PATH} \
    && cd ${WFT4GALAXY_PATH} \
    && python3 setup.py install \
    && apt-get -y clean \
    && apt-get -y autoremove \
    && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/*

# setup bash custom prompt (PS1)
ADD bashrc /root/.bashrc

# update the working dir
WORKDIR /root

# add container entrypoint
COPY entrypoint.sh /bin/entrypoint.sh
COPY entrypoint-argparser.sh /usr/local/bin/entrypoint-argparser.sh

# set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
