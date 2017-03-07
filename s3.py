import boto3

BUCKET = 'dsekt-assets'

client = boto3.client('s3')
bucket = boto3.resource('s3').Bucket(BUCKET)

def exists(path):
    items = [path, path + '/'] #check both the path and a folder at that path
    return any(map(lambda x: x.key in items, bucket.objects.filter(Prefix=path)))

def owner(path):
    if exists(path): return bucket.Object(path).metadata['owner']

def list(prefix):
    response = client.list_objects_v2(
        Bucket='dsekt-assets',
        Delimiter='/',
        Prefix=prefix)

    files = [x['Key'] for x in response['Contents']] if 'Contents' in response else []
    folders = [x['Prefix'] for x in response['CommonPrefixes']] if 'CommonPrefixes' in response else []

    return {'files': files, 'folders': folders}

def get(path):
    if exists(path): return bucket.Object(path).get()

def get_url(path):
    if exists(path):
        return client.generate_presigned_url(
            'get_object',
            Params = {
                'Bucket': BUCKET,
                'Key': path
            },
            ExpiresIn = 1800)

def put(path, file, owner, mimetype):
    if exists(path):
        return False

    file.seek(0)

    return bucket.put_object(
        Key=path,
        Body=file,
        ContentType=mimetype,
        Metadata={
            'owner': owner,
            'filename': file.filename
        }
    )

def delete(path):
    if not exists(path): 
        return False

    bucket.Object(path).delete()
    return True
