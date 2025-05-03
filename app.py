from flask import Flask, render_template, request, redirect, url_for
import boto3
import os

app = Flask(__name__)

S3_BUCKET = "finance-crawler-17032"
S3_FOLDER = "sbp_reports"
REGION = "us-east-1"
ITEMS_PER_PAGE = 20

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=REGION
)

def get_all_keys_paginated(bucket, prefix, start_after=None, max_keys=ITEMS_PER_PAGE):
    kwargs = {
        'Bucket': bucket,
        'Prefix': prefix,
        'MaxKeys': max_keys,
    }
    if start_after:
        kwargs['StartAfter'] = start_after

    response = s3_client.list_objects_v2(**kwargs)
    pdfs = [
        obj['Key'] for obj in response.get('Contents', [])
        if obj['Key'].endswith(".pdf") and obj['Key'] != prefix
    ]

    is_truncated = response.get('IsTruncated', False)
    next_start_after = pdfs[-1] if is_truncated and pdfs else None
    return pdfs, next_start_after

@app.route('/')
def list_pdfs():
    start_after = request.args.get('start_after')
    pdfs, next_start_after = get_all_keys_paginated(S3_BUCKET, S3_FOLDER + '/', start_after)

    return render_template(
        'index.html',
        pdfs=pdfs,
        bucket=S3_BUCKET,
        next_start_after=next_start_after,
        prev_start_after=start_after
    )

@app.route('/view/<path:key>')
def view_pdf(key):
    url = s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': key},
        ExpiresIn=3600
    )
    return redirect(url)

if __name__ == "__main__":
    app.run(debug=True)
