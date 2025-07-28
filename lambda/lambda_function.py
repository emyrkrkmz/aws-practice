import boto3
from PIL import Image, ImageOps
import io
import os
import urllib.parse

s3 = boto3.client('s3')

def lambda_handler(event, context):
    print("Received event:", event)
    
    # Get source bucket and key
    src_bucket = event['Records'][0]['s3']['bucket']['name']
    src_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    dst_bucket = src_bucket + "-resized"
    dst_key = "resized-" + src_key

    try:
        # Download the image from S3
        response = s3.get_object(Bucket=src_bucket, Key=src_key)
        image_content = response['Body'].read()

        # Open image
        img = Image.open(io.BytesIO(image_content))

        # Resize image
        width = 100
        w_percent = (width / float(img.size[0]))
        height = int((float(img.size[1]) * float(w_percent)))
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)

        # Save to buffer
        buffer = io.BytesIO()
        img_format = img.format if img.format else 'JPEG'
        img_resized.save(buffer, format=img_format)
        buffer.seek(0)

        # Upload to destination bucket
        s3.put_object(
            Bucket=dst_bucket,
            Key=dst_key,
            Body=buffer,
            ContentType=response['ContentType']
        )

        print(f"Successfully resized {src_key} and uploaded to {dst_bucket}/{dst_key}")
    except Exception as e:
        print(f"Error processing object {src_key} from bucket {src_bucket}. Error: {str(e)}")
        raise e
