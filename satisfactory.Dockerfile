FROM ubuntu:24.04

# https://askubuntu.com/a/1515958
RUN touch /var/mail/ubuntu && chown ubuntu /var/mail/ubuntu && userdel -r ubuntu

# Install required system packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y curl software-properties-common && rm -rf /var/lib/apt/lists/*

# Add support for the 32bit architecture
RUN add-apt-repository multiverse && dpkg --add-architecture i386

# Install required SteamCMD dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y lib32gcc-s1 && rm -rf /var/lib/apt/lists/*

# Add an unprivileged user
# Running things in Docker as root is a security risk and should be avoided
RUN useradd -ms /bin/bash steam

# Switch to the new user
USER steam

# Switch to the HOME directory of the new user
WORKDIR /home/steam

# Create the "Steam" subdirectory
RUN mkdir -p Steam

# Switch to the new directory
WORKDIR /home/steam/Steam

# Download SteamCMD and extract it
RUN curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -

# Install the Satisfactory dedicated server
ARG RELEASE_BRANCH=server-public
RUN if [ "$RELEASE_BRANCH" = "server-public" ]; then \
    /home/steam/Steam/steamcmd.sh +force_install_dir SatisfactoryDedicatedServer +login anonymous +app_update 1690800 +quit; \
    else \
    /home/steam/Steam/steamcmd.sh +force_install_dir SatisfactoryDedicatedServer +login anonymous +app_update 1690800 -beta $RELEASE_BRANCH +quit; \
    fi

# Set the entrypoint to the dedicated server start script
ENTRYPOINT [ "/home/steam/Steam/SatisfactoryDedicatedServer/FactoryServer.sh" ]

# for documentation purposes
EXPOSE 7777/udp
EXPOSE 7777/tcp
EXPOSE 8888/tcp
