# Use an official Python runtime as a base image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the source code into the container
COPY src/ ./src
COPY .env ./
COPY main.py ./
COPY requirements.txt ./

# Install dependencies if needed
RUN pip install -r requirements.txt

# Set the entrypoint
CMD ["python", "main.py"]