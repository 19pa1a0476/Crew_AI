FROM python:3.12

WORKDIR /app

# Copy the application code
COPY . /app/

# Install UV package manager
RUN apt-get update && apt-get install -y wget \
    && wget -qO- https://astral.sh/uv/install.sh | sh \
    && . $HOME/.local/bin/env

# Set environment variables
ENV PATH="$HOME/.local/bin:$PATH"
ENV PORT=8000
ENV PYTHONPATH="/app"

# Create a virtual environment using UV
RUN ~/.local/bin/uv venv

# Install dependencies using UV within the virtual environment
RUN . /app/.venv/bin/activate && ~/.local/bin/uv pip install -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Set the default command to run the main.py with python
CMD . /app/.venv/bin/activate && python main.py