Image Processing Batch Job
This document provides instructions on how to set up and run the Python console application for batch processing images.
Overview
The system is composed of three main parts:
Image Captioning API: The local Flask service that analyzes an image and returns a caption and tags. You have already provided this.
Oracle Database: Your source database containing the document numbers to be processed.
Batch Processor Console App: The new script (run_batch_processor.py) that connects the database and the APIs to perform the work.
The workflow is as follows:
The Batch Processor connects to the Oracle database and fetches a list of document numbers that need processing.
It logs into the SOAP DMS service to get an authentication token.
For each document number, it retrieves the image file from the SOAP service.
The image is sent to the running Image Captioning API.
The returned caption and tags are used to update the corresponding row in the Oracle database.
Setup & Execution
Follow these steps precisely to run the application.
Step 1: Set Up the Image Captioning API
First, ensure the local AI service is ready.
Navigate to the API Directory: Open a terminal or command prompt and go to the directory of your image-captioning-py project.
Install Dependencies: If you haven't already, install its dependencies.
pip install -r requirements.txt


Download AI Models: This is a crucial one-time step that requires an internet connection.
python download_model.py


Run the API Service: Start the Flask server. It will run on http://127.0.0.1:5001.
python app.py

Leave this terminal open and running.
Step 2: Set Up the Batch Processor
Now, in a new terminal, set up the main console application.
Place Files: Save the run_batch_processor.py and requirements.txt files into a new, separate folder for your project.
Install Dependencies: Install the dependencies for the batch processor.
pip install -r requirements.txt

Note: This requirements.txt is different from the one for the captioning API.
Configure Credentials: Open the run_batch_processor.py script and fill in your credentials in the --- CONFIGURATION --- section at the top of the file. This includes:
Oracle Database connection details (ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN).
SOAP DMS login credentials (DMS_USER, DMS_PASSWORD).
Step 3: Run the Batch Processor
Once both services are set up and the Image Captioning API is running, you can start the main process.
Execute the Script: Run the script from your terminal.
python run_batch_processor.py


Monitor the Output: The application will log its progress to the console, showing which document is being processed and whether the operations were successful. A detailed log file (batch_processor.log) will also be created in the same directory.
