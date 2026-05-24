# priv/backend/utils/aws_client.py
import os
import logging
from typing import Dict, Any, Optional
import asyncio
import json

# AWS SDK for Python
try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Boto3 (AWS SDK) not installed. AWS integration functionality will be disabled.")
    boto3 = None
    ClientError = None
    AWS_AVAILABLE = False

class AWSClient:
    """
    Client to interact with various AWS services.
    Credentials are expected to be available as environment variables.
    """
    def __init__(self):
        logger.info("AWSClient: Initializing.")
        self.lambda_client = None
        self.s3_client = None # Example for S3, if needed later
        self._initialize_aws_clients()

    def _initialize_aws_clients(self):
        """
        Initializes AWS service clients using credentials from environment variables.
        These environment variables will be populated from Kubernetes Secrets in GKE.
        """
        if boto3 is None:
            logger.warning("Boto3 (AWS SDK) not available. Skipping AWS client initialization.")
            return

        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        aws_region = os.getenv("AWS_REGION", "us-east-1") # Default to us-east-1 if not set

        if not all([aws_access_key_id, aws_secret_access_key]):
            logger.warning("Missing AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY environment variables. AWS clients will not be initialized.")
            return

        try:
            # Initialize Lambda client
            self.lambda_client = boto3.client(
                'lambda',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=aws_region
            )
            logger.info(f"AWS Lambda client initialized for region: {aws_region}")

            # Initialize S3 client (example, uncomment if needed)
            # self.s3_client = boto3.client(
            #     's3',
            #     aws_access_key_id=aws_access_key_id,
            #     aws_secret_access_key=aws_secret_access_key,
            #     region_name=aws_region
            # )
            # logger.info(f"AWS S3 client initialized for region: {aws_region}")

        except ClientError as e:
            logger.error(f"Failed to initialize AWS client due to ClientError: {e}", exc_info=True)
            self.lambda_client = None
            self.s3_client = None
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}", exc_info=True)
            self.lambda_client = None
            self.s3_client = None

    async def invoke_lambda_function(self, function_name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Invokes an AWS Lambda function asynchronously.

        Args:
            function_name (str): The name of the Lambda function to invoke.
            payload (Dict[str, Any]): The payload to send to the Lambda function.

        Returns:
            Optional[Dict[str, Any]]: The response from the Lambda function, or None on error.
        """
        if not self.lambda_client:
            logger.error("AWS Lambda client is not initialized. Cannot invoke Lambda function.")
            return None

        try:
            logger.info(f"Invoking AWS Lambda function '{function_name}' with payload: {payload}")
            response = await asyncio.to_thread(
                self.lambda_client.invoke,
                FunctionName=function_name,
                InvocationType='RequestResponse', # Use 'Event' for async, 'RequestResponse' for sync
                Payload=json.dumps(payload)
            )

            # Parse the response payload
            response_payload = json.loads(response['Payload'].read().decode('utf-8'))
            logger.info(f"Received response from AWS Lambda: {response_payload}")
            return response_payload
        except ClientError as e:
            logger.error(f"AWS ClientError invoking Lambda function '{function_name}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error invoking Lambda function '{function_name}': {e}", exc_info=True)
            return None

    # Add other AWS interaction methods here (e.g., for S3, EC2, etc.)
    # async def upload_to_s3(self, bucket_name: str, key: str, data: bytes):
    #     if not self.s3_client: return
    #     await asyncio.to_thread(self.s3_client.put_object, Bucket=bucket_name, Key=key, Body=data)
    #     logger.info(f"Uploaded {key} to s3://{bucket_name}")

