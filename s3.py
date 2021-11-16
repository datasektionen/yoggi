from os import getenv
import boto3

from urllib.parse import quote

BUCKET = getenv("S3_BUCKET")

client = boto3.client('s3')
bucket = boto3.resource('s3').Bucket(BUCKET)

def exists(path):
    items = [path, path + '/'] #check both the path and a folder at that path
    return any(map(lambda x: x.key in items, bucket.objects.filter(Prefix=path)))

def owner(path):
    if exists(path): return bucket.Object(path).metadata['owner']

def list(prefix):
    response = client.list_objects_v2(
        Bucket=BUCKET,
        Delimiter='/',
        Prefix=prefix)

    files = [x['Key'] for x in response['Contents']] if 'Contents' in response else []
    folders = [x['Prefix'] for x in response['CommonPrefixes']] if 'CommonPrefixes' in response else []

    # Apparently you can't get tags from list_objects...
    tags = {}
    for f in files:
        file_tags = client.get_object_tagging(
            Bucket=BUCKET,
            Key=f
        )

        tags[f] = file_tags["TagSet"] or [{'Key': 'public', 'Value': 'False'}]

    return {'files': files, 'folders': folders, 'tags': tags}


def get(path):
    if exists(path): return bucket.Object(path).get()


def get_url(path):
    if exists(path):
        return client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET,
                'Key': path
            },
            ExpiresIn=60*60*24*365)


def put(path, file, owner, mimetype, public):
    if exists(path):
        return False

    file.seek(0)

    return bucket.put_object(
        Key=path,
        Body=file,
        ContentType=mimetype,
        Metadata={
            'owner': owner,
            'filename': quote(file.filename)
        },
        Tagging="public=" + str(public)
    )

def putPermissions(path, public):
    if not exists(path):
        return False
    
    return client.put_object_tagging(
        Bucket=BUCKET,
        Key=path,
        Tagging={
            'TagSet': [
                {
                    'Key': 'public',
                    'Value': str(public)
                }
            ]
        }
    )

def delete(path):
    if not exists(path):
        return False

    bucket.Object(path).delete()
    return True
