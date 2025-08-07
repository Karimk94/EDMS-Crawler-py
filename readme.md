EDMS Image Processing Batch Job

This console application automates the process of retrieving images from an OpenText eDOCS (EDMS) system, analyzing them with a local AI service to generate captions and tags, and updating the results back into an Oracle database.
Overview
The system is designed to run as a scheduled batch job and orchestrates a workflow between three components:
Oracle Database: The source database containing document numbers that need processing.
OpenText eDOCS (EDMS) SOAP Service: The system of record from which the actual image files are retrieved.
Image Captioning API: A separate, locally-run Flask application that performs the AI analysis on the images.
Workflow
The application starts and connects to the Oracle database.
It fetches a batch of document numbers that have not yet been processed.
It securely logs into the EDMS SOAP service to obtain an authentication token.
For each document number, it performs the following steps:
Retrieves the image file from the EDMS.
Sends the image to the local Image Captioning API.
Receives a descriptive caption and a list of relevant tags.
Updates the corresponding row in the Oracle database with the new caption and tags.
The process repeats until all documents in the batch have been processed.
Project Structure
/edms-batch-processor/
|
|-- run_batch_processor.py    # The main Python script for the console application.
|-- requirements.txt          # A list of the necessary Python libraries.
|-- .env                      # A local file to store your secret credentials (ignored by Git).
|-- .gitignore                # Tells Git to ignore the .env file.
|-- README.md                 # This file.


Setup and Installation
Follow these steps precisely to get the application running.
Prerequisites
Python 3.7+
Oracle Instant Client: The Oracle client libraries must be installed on the machine running this script so that Python can connect to the database. Ensure the client version is compatible with your database version.
Access to the Image Captioning API: The separate AI service must be running and accessible over the network.
Step 1: Clone the Repository
Clone or download the project files to your local machine.
Step 2: Create a Virtual Environment (Recommended)
It's highly recommended to create a virtual environment to keep project dependencies isolated.
# Navigate to the project directory
cd /path/to/edms-batch-processor

# Create the environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate


Step 3: Install Dependencies
Install all the required Python libraries from the requirements.txt file.
pip install -r requirements.txt


Step 4: Configure Your Credentials
This is the most important setup step. You must create a .env file to store your credentials securely.
Create a file named .env in the root of the project directory.
Copy the template below into your .env file and fill in your actual credentials.
# .env file

# --- Oracle Database Connection Details ---
# Example DSN: "your_db_host:1521/your_service_name"
ORACLE_USER="your_db_username"
ORACLE_PASSWORD="your_db_password"
ORACLE_DSN="your_db_host:1521/your_service_name"

# --- SOAP DMS Service Details ---
WSDL_URL="your_wsdl_url"
DMS_USER="your_dms_username"
DMS_PASSWORD="your_dms_password"

# --- Image Captioning API URL ---
# This should be the address of your locally running Flask API
IMAGE_PROCESSING_URL="your_image_processing_url"


Note: The .gitignore file is already configured to prevent your .env file from ever being committed to the repository.
Step 5: Customize the SQL Queries
Before running the application, you must update the SQL queries inside run_batch_processor.py to match your database schema.
Open the run_batch_processor.py file and locate the main() function. Inside this function, you will find two SQL statements that need to be edited:
sql_fetch: This query selects the document numbers to be processed. You must change YOUR_TABLE_NAME to the name of your table. You may also need to adjust the WHERE clause.
sql_update: This query updates the table with the results. You must change YOUR_TABLE_NAME and ensure the column names (IMAGE_CAPTION, IMAGE_TAGS, PROCESSED_DATE, DOCUMENT_NUMBER) match your schema.
Running the Application
Start the Image Captioning API: Ensure your separate Flask-based AI service is running and accessible at the URL you specified in the .env file.
Run the Batch Processor: Execute the main script from your terminal.
python run_batch_processor.py


The application will start, log its progress to the console, and create a batch_processor.log file with detailed information about the run.
Troubleshooting
oracledb.exceptions.DatabaseError: DPI-1047: Cannot locate a 64-bit Oracle Client library: This means the Oracle Instant Client is not installed or not in your system's PATH. Please install it and ensure it's accessible.
zeep.exceptions.Fault: Unable to locate document...: This error comes directly from the EDMS server. It means the document number retrieved from your database does not exist in the EDMS. Check the data in your Oracle table to ensure the document numbers are correct and do not have extra spaces or characters.
requests.exceptions.ConnectionError: This error occurs when the script cannot connect to the Image Captioning API. Make sure the Flask service is running and that the IMAGE_PROCESSING_URL in your .env file is correct.
