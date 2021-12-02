from qcloud_cos import CosConfig, CosServiceError
from qcloud_cos import CosS3Client
from django.conf import settings
from sts.sts import Sts


def create_bucket(bucket, region='ap-chengdu'):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.create_bucket(Bucket=bucket, ACL="public-read")
    cors_config = {
        'CORSRule': [
            {
                'AllowedOrigin': '*',
                'AllowedMethod': ['GET', 'POST', 'HEAD', 'PUT', 'DELETE'],
                'AllowedHeader': '*',
                'ExposeHeader': '*',
                'MaxAgeSeconds': 500,
            }
        ]
    }
    client.put_bucket_cors(Bucket=bucket, CORSConfiguration=cors_config)


def upload_file(bucket, region, file_object, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.upload_file_from_buffer(Bucket=bucket, Body=file_object, Key=key)
    return f'https://{bucket}.cos.{region}.myqcloud.com/{key}'


def credential(bucket, region):
    config = {
        'duration_seconds': 1800,
        'secret_id': settings.TENCENT_COS_ID,
        'secret_key': settings.TENCENT_COS_KEY,
        'bucket': bucket,
        'region': region,
        'allow_prefix': '*',
        'allow_actions': [
            'name/cos:PutObject',
            '*',
        ],
    }

    sts = Sts(config)
    result_dict = sts.get_credential()
    return result_dict


def delete_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    client.delete_object(Bucket=bucket, Key=key)


def delete_file_list(bucket, region, key_list):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    objects = {
        "Quiet": "true",
        "Object": key_list
    }
    client.delete_objects(Bucket=bucket, Delete=objects)


def check_file(bucket, region, key):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    result_dict = client.head_object(Bucket=bucket, Key=key)
    return result_dict


def delete_bucket(bucket, region):
    config = CosConfig(Region=region, SecretId=settings.TENCENT_COS_ID, SecretKey=settings.TENCENT_COS_KEY)
    client = CosS3Client(config)
    try:
        while True:
            part_objects = client.list_objects(bucket)
            contents = part_objects.get('Contents')
            if not contents:
                break
            objects = {
                "Quiet": "true",
                'Object': [{"Key": i['Key']} for i in contents]
            }
            client.delete_objects(Bucket=bucket, Delete=objects)
            if part_objects.get('IsTruncated') == 'false':
                break

        while True:
            part_uploads = client.list_multipart_uploads(bucket)
            uploads = part_uploads.get('Upload')
            if not uploads:
                break
            for i in uploads:
                client.abort_multipart_upload(Bucket=bucket, Key=i['Key'], UploadId=i['UploadId'])
            if part_uploads.get('IsTruncated') == 'false':
                break
        client.delete_bucket(bucket)
    except CosServiceError:
        pass
