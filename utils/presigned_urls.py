import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from django.conf import settings


def generate_presigned_url(s3_key, expiration=settings.PRESIGNED_URL_EXPIRY_TIME) -> str:
    s3_client = boto3.client(
        's3',
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=f'https://s3-{settings.AWS_S3_REGION_NAME}.amazonaws.com'
    )

    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=expiration
        )
        return response
    except NoCredentialsError:
        raise Exception("AWS credentials not available")
    except ClientError as e:
        raise Exception(f"Error generating pre-signed URL: {str(e)}")
