# Step 1: Specify the base image
FROM ubuntu:22.04
FROM python:3.9
# Step 2: Set the working directory inside the container
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENV MONGO_URI=mongodb://mongo:27017/
EXPOSE 8888
CMD ["python", "app.py &"]


