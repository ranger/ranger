# Usage instructions:
# 1. "docker build -t ranger/ranger:latest ranger ."
# 2. "docker run -it ranger/ranger ranger"

FROM debian

RUN apt-get update
RUN apt-get install -y ranger
