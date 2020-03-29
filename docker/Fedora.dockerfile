# RPM build script for Fedora (latest)
#
# Usage:
#   (From the rivescript-python git root)
#   sudo docker build -t rivescript_fedora -f ./docker/Fedora.dockerfile .
#   sudo docker run rivescript_fedora -v ./docker/dist:/mnt/export
#
# Bind mount: /mnt/export in the image is where the final rpm files are copied
# to, so mount it on the host to get at these files.

FROM fedora:latest
MAINTAINER Noah Petherbridge <root@kirsle.net>
ENV RIVESCRIPT_DOCKER_BUILD 42

# Updates and requirements
RUN dnf -y update && dnf -y install rpm-build sudo make \
    perl python3-devel python2-devel && \
    dnf clean all

# Create a user to build the packages.
RUN useradd builder -u 1000 -m -G users,wheel && \
    echo "builder ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    echo "# macros"                      >  /home/builder/.rpmmacros && \
    echo "%_topdir    /home/builder/rpm" >> /home/builder/.rpmmacros && \
    echo "%_sourcedir %{_topdir}"        >> /home/builder/.rpmmacros && \
    echo "%_builddir  %{_topdir}"        >> /home/builder/.rpmmacros && \
    echo "%_specdir   %{_topdir}"        >> /home/builder/.rpmmacros && \
    echo "%_rpmdir    %{_topdir}"        >> /home/builder/.rpmmacros && \
    echo "%_srcrpmdir %{_topdir}"        >> /home/builder/.rpmmacros && \
    mkdir /home/builder/rpm && \
    chown -R builder /home/builder

# Add the Python tree to /build in the container.
WORKDIR /home/builder/src
ADD . /home/builder/src
RUN chown -R builder /home/builder

USER builder
RUN pip install --user --trusted-host pypi.python.org -r requirements.txt
CMD ["make", "docker.rpm"]
