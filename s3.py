import boto3

s3 = boto3.resource('s3')
bucket = s3.Bucket('dsekt-assets')

def exists(path):
    items = [path, path + '/'] #check both the path and a folder at that path
    return any(map(lambda x: x.key in items, bucket.objects.filter(Prefix=path)))

def owner(path):
    if exists(path): return bucket.Object(path).metadata['owner']

def list(prefix, type='files'):
    if type == 'files':
        return [x.key for x in bucket.objects.filter(Prefix=prefix, Delimiter='/')]
    else:
        return [x.key for x in bucket.objects.filter(Prefix=prefix) if x.key.endswith('/')]

def get(path):
    if exists(path): return bucket.Object(path).get()

def put(path, file, owner, mimetype):
    if exists(path):
        return False

    file.seek(0)

    return bucket.put_object(
        Key=path,
        Body=file,
        ContentType=mimetype,
        Metadata={
            'owner': owner
        }
    )

def delete(path):
    if not exists(path): 
        return False

    bucket.Object(path).delete()
    return True
