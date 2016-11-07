FROM ubuntu

# metadata
MAINTAINER PhenoMeNal-H2020 Project ( phenomenal-h2020-users@googlegroups.com )

# set the term var
ENV TERM xterm-256color

# wft4galaxy path
ENV WFT4GALAXY_PATH /opt/wft4galaxy

# install base packages
RUN apt-get update && \
    apt-get install -y python python-dev python-pip git \
                       python-lxml libyaml-dev && \
    apt-get -y clean && apt-get -y autoremove && rm -rf /var/lib/{cache,log}/ /tmp/* /var/tmp/*

# install ipython
RUN pip install --upgrade pip

# setup bash custom prompt (PS1)
RUN echo "parse_git_branch() {" >> ${HOME}/.bashrc
RUN echo "git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ (\1)/'" >> ${HOME}/.bashrc
RUN echo "}" >> ${HOME}/.bashrc
RUN echo "export PS1=\"\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\[\e[1;31m\]\$(parse_git_branch)\[\e[0m\]\$ \"" >> ${HOME}/.bashrc
RUN echo "export CLICOLOR=1" >> ${HOME}/.bashrc
RUN echo "export LSCOLORS=ExFxBxDxCxegedabagacad" >> ${HOME}/.bashrc

# install wft4galaxy
RUN git clone https://github.com/phnmnl/wft4galaxy ${WFT4GALAXY_PATH} \
    && cd ${WFT4GALAXY_PATH} \
    && python setup.py install

# link the example folder to the user's home
RUN ln -s ${WFT4GALAXY_PATH}/examples ${HOME}/wft4galaxy-examples

# update the working dir
WORKDIR /root

# add container entrypoint
COPY entrypoint.sh /bin/entrypoint.sh
COPY set-bioblend-env.sh /usr/local/bin/set-bioblend-env.sh

# set the entrypoint
ENTRYPOINT ["entrypoint.sh"]
