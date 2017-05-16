FROM ubuntu

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
RUN apt-get update && \
    apt-get install -y python python-dev python-pip git \
                       python-lxml libyaml-dev && \
    apt-get -y clean && apt-get -y autoremove && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/*

# install ipython
RUN pip install --upgrade pip

# setup bash custom prompt (PS1)
ADD bashrc ${HOME}/.bashrc

# install wft4galaxy
RUN git clone --single-branch --depth 1 -b ${WFT4GALAXY_BRANCH} ${WFT4GALAXY_REPOSITORY_URL} ${WFT4GALAXY_PATH} \
    && cd ${WFT4GALAXY_PATH} \
    && python setup.py install \
    && rm -rf ${WFT4GALAXY_PATH}

# update the working dir
WORKDIR /root

# add container entrypoint
COPY entrypoint.sh /bin/entrypoint.sh
COPY entrypoint-argparser.sh /usr/local/bin/entrypoint-argparser.sh

# set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
