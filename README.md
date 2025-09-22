# Yoggi
Static files server

## How it works
Yoggi uses AWS S3 to store the files. The frontend is written in React.

# How to run
1. Install Python
1. Run `npm install` and `npm run build` (builds the frontend)
1. Configure your environment variables in an `.env`-file, see [Environment variables](#environment-variables)
1. Change `'REACT_APP_BUCKET_NAME': JSON.stringify('dsekt-assets')` to `'REACT_APP_BUCKET_NAME': JSON.stringify('dsekt-assets-dev')` in [webpack-production.config.js](/webpack-production.config.js), if you are running `npm run build` to test locally
1. Run `pipenv install`
1. Run `pipenv shell` which loads environment variables and some other magic
1. Run python yoggi.py

At this time, I don't know how to make the hot-reloading of React work. You simply have to run `npm run build` to make it work with the backend.

# Environment variables

When running locally, you can run [nyckeln under dörrmattan](https://github.com/datasektionen/nyckeln-under-dorrmattan) instead of the production login system. If you need access to the `dsekt-assets-dev` bucket, you can ask Systemansvarig: [d-sys@datasektionen.se](mailto:d-sys@datasektionen.se), but setting up an own bucket may be a better choice.

| Name                           | Description                                                      | Default                                   |
| ------------------------------ | ---------------------------------------------------------------- | ----------------------------------------- |
| LOGIN_FRONTEND_URL             | URL to login from frontend                                       | https://sso.datasektionen.se/legacyapi    |
| LOGIN_API_URL                  | URL to login from backend                                        | https://sso.datasektionen.se/legacyapi    |
| LOGIN_API_KEY                  | API key for KTH authentication                                   | ---                                       |
| HIVE_URL                       | URL to hive server                                               | https://hive.datasektionen.se/api/v1      |
| HIVE_API_KEY                   | API key for getting permissions                                  | ---                                       |
| PORT                           | Port to serve backend on                                         | 5000                                      |
| S3_BUCKET                      | Name of S3 bucket. When running locally, use `dsekt-assets-dev`  | ---                                       |
| AWS_ACCESS_KEY_ID              | AWS IAM access key id                                            | ---                                       |
| AWS_SECRET_ACCESS_KEY          | AWS IAM secret access key                                        | ---                                       |

# Configuring the S3 bucket

Objects can be set as publicly accessible by adding the tag key-value-pair "public": "True" to the object. For this to work, the bucket needs to be configured with the following JSON (Bucket policy):
```JSON
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::dsekt-assets/*",
            "Condition": {
                "StringEquals": {
                    "s3:ExistingObjectTag/public": "True"
                }
            }
        }
    ]
}
```

# Protip
To allow larger file uploads, set the max size of file uploads to for example 100 MB.

```bash
echo "client_max_body_size 100M;" > /home/dokku/yoggi/nginx.conf.d/max_size.conf
```

Alernatively edit the file to edit the max size if the file already exists:

```bash
sudo nano /home/dokku/yoggi/nginx.conf.d/max_size.conf
```
