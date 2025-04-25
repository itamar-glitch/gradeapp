# Step 1: Specify the base image
FROM python:3.10

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the application code into the container
COPY . .

# Step 4: Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Expose the necessary port
EXPOSE 8888
#step 6 : run the http app 
CMD ["python", "app.py"]
