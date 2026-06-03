import boto3

class S3Uploader:

    def __init__(self, bucket, region=None):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)

    def upload(self, file_path, s3_key):
        self.s3.upload_file(file_path, self.bucket, s3_key)
        return f"s3://{self.bucket}/{s3_key}"