FROM python:3.11-slim
WORKDIR /workspace

# Install crewai
RUN pip install --no-cache-dir crewai crewai-tools

# Default: interactive bash
CMD ["/bin/bash"]
