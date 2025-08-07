import oracledb
import requests
from zeep import Client, Settings
import logging
from logging.handlers import RotatingFileHandler
import io
import os
from zeep.exceptions import Fault
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

# Oracle Database Connection Details
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN")

# SOAP DMS Service Details
WSDL_URL = os.getenv("WSDL_URL")
DMS_USER = os.getenv("DMS_USER")
DMS_PASSWORD = os.getenv("DMS_PASSWORD")

# Image Captioning API URL
IMAGE_PROCESSING_URL = os.getenv("IMAGE_PROCESSING_URL")

# Batch Processing Settings
BATCH_SIZE = 100 # Number of rows to fetch from Oracle in each run

# --- END OF CONFIGURATION ---

def setup_logging():
    """Configures logging to both console and a rotating file."""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_file = 'batch_processor.log'
    
    # File Handler
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # logging.info("Logging configured.")

def dms_login(username, password):
    """Logs into the DMS SOAP service and returns a session token (DST)."""
    try:
        settings = Settings(strict=False, xml_huge_tree=True)
        client = Client(WSDL_URL, settings=settings)
        
        login_info_type = client.get_type('{http://schemas.datacontract.org/2004/07/OpenText.DMSvr.Serializable}DMSvrLoginInfo')
        login_info_instance = login_info_type(network=0, loginContext='RTA_MAIN', username=username, password=password)
        
        array_type = client.get_type('{http://schemas.datacontract.org/2004/07/OpenText.DMSvr.Serializable}ArrayOfDMSvrLoginInfo')
        login_info_array_instance = array_type(DMSvrLoginInfo=[login_info_instance])
        
        call_data = {'call': {'loginInfo': login_info_array_instance, 'authen': 1, 'dstIn': ''}}
        
        # logging.info(f"Attempting DMS login for user '{username}'...")
        response = client.service.LoginSvr5(**call_data)
        
        if response and response.resultCode == 0 and response.DSTOut:
            # logging.info("DMS login successful.")
            return response.DSTOut
        else:
            result_code = getattr(response, 'resultCode', 'N/A')
            logging.error(f"DMS login failed. Result code: {result_code}")
            return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during DMS login: {e}", exc_info=True)
        return None

def get_document_from_dms(dst, doc_number, version_id=None):
    """Retrieves a single document's image bytes from the DMS using the GetDocSvr3 method."""
    svc_client, obj_client, content_id, stream_id = None, None, None, None
    try:
        settings = Settings(strict=False, xml_huge_tree=True)
        svc_client = Client(WSDL_URL, port_name='BasicHttpBinding_IDMSvc', settings=settings)
        obj_client = Client(WSDL_URL, port_name='BasicHttpBinding_IDMObj', settings=settings)
        
        # logging.info(f"Step 1: Calling GetDocSvr3 for doc: '{doc_number}'")
        
        get_doc_call = {
            'call': {
                'dstIn': dst,
                'criteria': {
                    'criteriaCount': 3,
                    'criteriaNames': {
                        'string': ['%TARGET_LIBRARY', '%DOCUMENT_NUMBER', '%VERSION_ID']
                    },
                    'criteriaValues': {
                        'string': ['RTA_MAIN', doc_number, '%VERSION_TO_INDEX']
                    }
                }
            }
        }
        
        doc_reply = svc_client.service.GetDocSvr3(**get_doc_call)

        if not (doc_reply and doc_reply.resultCode == 0 and doc_reply.getDocID):
            logging.warning(f"Document not found in DMS for doc_number: {doc_number}. Result code: {getattr(doc_reply, 'resultCode', 'N/A')}")
            return None, None
        
        content_id = doc_reply.getDocID
        # logging.info(f"Step 1 SUCCESS. contentID: {content_id}")

        # logging.info("Step 2: Calling GetReadStream")
        stream_reply = obj_client.service.GetReadStream(call={'dstIn': dst, 'contentID': content_id})
        if not (stream_reply and stream_reply.resultCode == 0 and stream_reply.streamID):
            raise Exception(f"Failed to get read stream. Result code: {getattr(stream_reply, 'resultCode', 'N/A')}")
        stream_id = stream_reply.streamID
        # logging.info(f"Step 2 SUCCESS. streamID: {stream_id}")

        # logging.info("Step 3: Reading stream...")
        doc_buffer = bytearray()
        while True:
            read_reply = obj_client.service.ReadStream(call={'streamID': stream_id, 'requestedBytes': 65536})
            if not read_reply or read_reply.resultCode != 0:
                raise Exception(f"Stream read failed. Result code: {getattr(read_reply, 'resultCode', 'N/A')}")
            chunk_data = read_reply.streamData.streamBuffer if read_reply.streamData else None
            if not chunk_data: break
            doc_buffer.extend(chunk_data)
        # logging.info("Step 3 SUCCESS. Full document downloaded.")

        filename = f"{doc_number}.jpg" # Default filename
        if doc_reply.docProperties and doc_reply.docProperties.propertyValues:
            try:
                prop_names = doc_reply.docProperties.propertyNames.string
                if '%VERSION_FILE_NAME' in prop_names:
                    index = prop_names.index('%VERSION_FILE_NAME')
                    version_file_name = doc_reply.docProperties.propertyValues.anyType[index]
                    _, extension = os.path.splitext(str(version_file_name))
                    if extension:
                        filename = f"{doc_number}{extension}"
            except Exception as e:
                logging.warning(f"Could not determine original filename, will use default. Error: {e}")

        return doc_buffer, filename

    except Fault as e:
        logging.error(f"Error during document retrieval for doc: {doc_number}. The DMS server responded with a fault: {e}", exc_info=True)
        return None, None
    except Exception as e:
        logging.error(f"An unexpected error occurred during document retrieval for doc: {doc_number}. Error: {e}", exc_info=True)
        return None, None
    finally:
        if obj_client:
            if stream_id:
                try: obj_client.service.ReleaseObject(call={'objectID': stream_id})
                except Exception: pass
            if content_id:
                try: obj_client.service.ReleaseObject(call={'objectID': content_id})
                except Exception: pass

def get_caption_and_tags(image_bytes, filename):
    """Sends image bytes to the captioning API and returns the results."""
    if not image_bytes:
        logging.warning("Image bytes are empty, cannot process.")
        return None, None
    
    try:
        # logging.info(f"Sending '{filename}' to image processing service...")
        files = {'image_file': (filename, io.BytesIO(image_bytes), 'application/octet-stream')}
        
        response = requests.post(IMAGE_PROCESSING_URL, files=files, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            caption = data.get('caption')
            tags = data.get('tags', [])
            # logging.info("Successfully received caption and tags.")
            return caption, tags
        else:
            logging.error(f"Image processing service failed with status {response.status_code}: {response.text}")
            return None, None
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not connect to image processing service at {IMAGE_PROCESSING_URL}. Is it running? Error: {e}")
        return None, None
    except Exception as e:
        logging.error(f"An unexpected error occurred while calling the image processor: {e}", exc_info=True)
        return None, None

def main():
    """Main execution function to run the batch process."""
    setup_logging()
    
    # 1. Login to DMS
    dst = dms_login(DMS_USER, DMS_PASSWORD)
    if not dst:
        logging.critical("Could not log into DMS. Aborting process.")
        return

    # 2. Connect to Oracle Database
    try:
        # logging.info("Connecting to Oracle database...")
        with oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN) as connection:
            # logging.info("Database connection successful.")
            with connection.cursor() as cursor:
                
                sql_fetch = f"""
                    SELECT docnumber from profile
                    WHERE docnumber = 19660298
                    FETCH FIRST {BATCH_SIZE} ROWS ONLY
                """
                # logging.info(f"Fetching up to {BATCH_SIZE} documents to process...")
                cursor.execute(sql_fetch)
                rows = cursor.fetchall()
                
                if not rows:
                    # logging.info("No documents found to process. Exiting.")
                    return

                # logging.info(f"Found {len(rows)} documents to process.")
                
                # 4. Process each document
                for i, row in enumerate(rows):
                    # This removes any potential leading/trailing whitespace.
                    doc_number = str(row[0]).strip()
                    
                    # logging.info(f"--- Processing document {i+1}/{len(rows)}: '{doc_number}' ---")
                    
                    # Get image from DMS
                    image_bytes, filename = get_document_from_dms(dst, doc_number)
                    if not image_bytes:
                        logging.warning(f"Skipping doc '{doc_number}' due to DMS retrieval failure.")
                        continue
                        
                    # Get caption and tags from AI service
                    caption, tags = get_caption_and_tags(image_bytes, filename)
                    if not caption:
                        logging.warning(f"Skipping doc '{doc_number}' due to captioning failure.")
                        continue
                        
                    # Update database
                    try:
                        # Convert tags list to a comma-separated string for storage
                        tags_str = ", ".join(tags)
                        
                        sql_update = """
                            UPDATE profile
                            SET abstract = :caption
                            WHERE docnumber = :doc_num
                        """
                        cursor.execute(sql_update, 
                            caption=caption, 
                            doc_num=doc_number
                        )
                        # logging.info(f"Successfully updated database for doc '{doc_number}'.")
                    except Exception as e:
                        logging.error(f"Failed to update database for doc '{doc_number}': {e}", exc_info=True)
                
                # Commit all changes at the end of the batch
                connection.commit()
                # logging.info("Batch finished. Database changes have been committed.")

    except oracledb.Error as e:
        logging.critical(f"Oracle Database error: {e}", exc_info=True)
    except Exception as e:
        logging.critical(f"An unhandled error occurred in the main process: {e}", exc_info=True)

if __name__ == '__main__':
    main()