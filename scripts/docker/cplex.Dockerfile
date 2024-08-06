ARG DOCKER_VER

# Build runtime image
FROM cosim-build:$DOCKER_VER AS cosim-cplex

ARG COSIM_USER
ARG CPLEX_BIN=cplex_studio129.linux-x86-64.bin
ENV PSST_SOLVER=$INSTDIR/ibm/cplex/bin/x86-64_linux/cplexamp

COPY "./$CPLEX_BIN" /home/$COSIM_USER/repo/

USER root
RUN chown -hR worker:worker $REPO_DIR/$CPLEX_BIN

USER $COSIM_USER
RUN cd $REPO_DIR && \
    chmod a+x "$CPLEX_BIN" && \
    ./$CPLEX_BIN -i silent -DLICENSE_ACCEPTED=TRUE -DUSER_INSTALL_DIR=$INSTDIR/ibm && \
    rm -r "$REPO_DIR/$CPLEX_BIN"
