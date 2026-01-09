"""
S3 client utilities for Isekai ComfyUI Custom Nodes

Provides HTTP-based S3 upload functionality with AWS Signature Version 4 authentication.
Works with AWS S3 and all S3-compatible services (Cloudflare R2, DigitalOcean Spaces, etc.)
"""

import os
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlparse, quote
from typing import Tuple

import requests


class S3UploadError(Exception):
    """Exception raised for S3 upload errors"""
    pass


def get_s3_credentials(access_key_input: str, secret_key_input: str) -> Tuple[str, str]:
    """
    Get S3 credentials with priority: environment variables > node input.

    Prints warnings to guide users toward secure practices.

    Args:
        access_key_input: Access key ID from node input (optional)
        secret_key_input: Secret access key from node input (optional)

    Returns:
        Tuple of (access_key_id, secret_access_key)

    Raises:
        S3UploadError: If no credentials found

    Priority:
        1. Environment variables (RECOMMENDED) ✅
        2. Node input (FALLBACK) ⚠️
    """
    # Check environment variables first (more secure)
    env_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    env_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()

    if env_access_key and env_secret_key:
        print("[Isekai] S3: Using credentials from AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        return (env_access_key, env_secret_key)

    # Fall back to node input with security warning
    if access_key_input and access_key_input.strip() and secret_key_input and secret_key_input.strip():
        print("[Isekai] S3: ⚠️  WARNING: Credentials provided via node input.")
        print("[Isekai] S3: For security, set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables instead.")
        print("[Isekai] S3: Credentials in node inputs may be saved in workflow JSON files.")
        return (access_key_input.strip(), secret_key_input.strip())

    # No credentials found
    raise S3UploadError(
        "No S3 credentials provided. Either:\n"
        "1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables (recommended), or\n"
        "2. Enter credentials in the node's input fields\n\n"
        "Get credentials from:\n"
        "  AWS S3: https://console.aws.amazon.com/iam/\n"
        "  Cloudflare R2: https://dash.cloudflare.com/\n"
        "  DigitalOcean: https://cloud.digitalocean.com/account/api/tokens\n"
        "  MinIO: Your MinIO admin console"
    )


def sign(key: bytes, msg: str) -> bytes:
    """Helper function for HMAC-SHA256 signing"""
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()


def get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    """
    Generate AWS Signature Version 4 signing key.

    Args:
        secret_key: AWS secret access key
        date_stamp: Date in YYYYMMDD format
        region: AWS region (e.g., 'us-east-1')
        service: AWS service name (e.g., 's3')

    Returns:
        Signing key as bytes
    """
    k_date = sign(('AWS4' + secret_key).encode('utf-8'), date_stamp)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, 'aws4_request')
    return k_signing


def generate_aws_signature_v4(
    method: str,
    url: str,
    headers: dict,
    payload_hash: str,
    access_key: str,
    secret_key: str,
    region: str,
    service: str = 's3'
) -> str:
    """
    Generate AWS Signature Version 4 authorization header.

    Implements AWS Signature Version 4 signing process:
    https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html

    Args:
        method: HTTP method (e.g., 'PUT')
        url: Full URL including scheme and path
        headers: Request headers dictionary
        payload_hash: SHA256 hash of request payload (hex string)
        access_key: AWS access key ID
        secret_key: AWS secret access key
        region: AWS region
        service: AWS service name (default: 's3')

    Returns:
        Authorization header value

    Example:
        >>> auth = generate_aws_signature_v4(
        ...     'PUT', 'https://bucket.s3.amazonaws.com/key',
        ...     headers, payload_hash, access_key, secret_key, 'us-east-1'
        ... )
    """
    # Parse URL
    parsed_url = urlparse(url)
    canonical_uri = quote(parsed_url.path, safe='/~')
    canonical_querystring = parsed_url.query or ''

    # Get timestamp from x-amz-date header
    amz_date = headers.get('x-amz-date', '')
    date_stamp = amz_date[:8]  # YYYYMMDD

    # Create canonical headers
    canonical_headers_list = []
    signed_headers_list = []

    for key in sorted(headers.keys()):
        canonical_headers_list.append(f"{key.lower()}:{headers[key].strip()}")
        signed_headers_list.append(key.lower())

    canonical_headers = '\n'.join(canonical_headers_list) + '\n'
    signed_headers = ';'.join(signed_headers_list)

    # Create canonical request
    canonical_request = f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"

    # Create string to sign
    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    canonical_request_hash = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{canonical_request_hash}"

    # Calculate signature
    signing_key = get_signature_key(secret_key, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # Create authorization header
    authorization_header = (
        f"{algorithm} "
        f"Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return authorization_header


def upload_to_s3_http(
    bucket: str,
    key: str,
    file_bytes: bytes,
    content_type: str,
    acl: str,
    access_key: str,
    secret_key: str,
    region: str,
    endpoint_url: str = ""
) -> None:
    """
    Upload file to S3 using HTTP PUT request with AWS Signature V4.

    Args:
        bucket: S3 bucket name
        key: Object key (path) in bucket
        file_bytes: File content as bytes
        content_type: MIME type (e.g., 'image/jpeg')
        acl: Access control list (e.g., 'private', 'public-read')
        access_key: AWS access key ID
        secret_key: AWS secret access key
        region: AWS region or S3-compatible region
        endpoint_url: Custom endpoint URL for S3-compatible services (empty for AWS S3)

    Raises:
        S3UploadError: If upload fails

    Example:
        >>> upload_to_s3_http(
        ...     'my-bucket', 'images/photo.jpg', image_bytes,
        ...     'image/jpeg', 'public-read', access_key, secret_key, 'us-east-1'
        ... )
    """
    # Build URL
    if endpoint_url:
        # Custom endpoint (R2, Spaces, MinIO, etc.)
        endpoint_url = endpoint_url.rstrip('/')
        url = f"{endpoint_url}/{bucket}/{key}"
    else:
        # AWS S3
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{key}"

    # Calculate payload hash
    payload_hash = hashlib.sha256(file_bytes).hexdigest()

    # Get current timestamp
    t = datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')

    # Prepare headers
    headers = {
        'host': urlparse(url).netloc,
        'x-amz-date': amz_date,
        'x-amz-content-sha256': payload_hash,
        'content-type': content_type,
        'x-amz-acl': acl
    }

    # Generate authorization header
    authorization = generate_aws_signature_v4(
        'PUT', url, headers, payload_hash,
        access_key, secret_key, region
    )

    # Add authorization to headers
    headers['Authorization'] = authorization

    # Make PUT request
    try:
        response = requests.put(
            url,
            data=file_bytes,
            headers=headers,
            timeout=60
        )

        # Check response
        if response.status_code == 200:
            print(f"[Isekai] S3: Upload successful ({len(file_bytes)} bytes)")
            return

        # Handle errors
        if response.status_code == 403:
            if 'SignatureDoesNotMatch' in response.text:
                raise S3UploadError(
                    "SignatureDoesNotMatch: Invalid credentials or signature.\n"
                    "Possible causes:\n"
                    "1. Incorrect access key or secret key\n"
                    "2. System clock is off (check time synchronization)\n"
                    "3. Wrong region specified"
                )
            raise S3UploadError(f"Access denied (403): {response.text[:200]}")

        if response.status_code == 404:
            raise S3UploadError(
                f"Bucket '{bucket}' not found (404).\n"
                f"Ensure bucket exists and region/endpoint are correct."
            )

        if response.status_code >= 400:
            raise S3UploadError(
                f"Upload failed (HTTP {response.status_code}): {response.text[:200]}"
            )

    except requests.exceptions.Timeout:
        raise S3UploadError("Upload request timed out after 60 seconds.")
    except requests.exceptions.ConnectionError as e:
        raise S3UploadError(f"Connection failed: {str(e)}")
    except S3UploadError:
        raise
    except Exception as e:
        raise S3UploadError(f"Unexpected error: {str(e)}")


def generate_s3_url(bucket: str, key: str, region: str, endpoint_url: str = "") -> str:
    """
    Generate public URL for S3 object.

    Args:
        bucket: S3 bucket name
        key: Object key (path) in bucket
        region: AWS region
        endpoint_url: Custom endpoint URL (empty for AWS S3)

    Returns:
        Public URL to the uploaded object

    Example:
        >>> url = generate_s3_url('my-bucket', 'image.jpg', 'us-east-1')
        >>> url
        'https://my-bucket.s3.us-east-1.amazonaws.com/image.jpg'
    """
    if endpoint_url:
        # Custom endpoint
        endpoint_url = endpoint_url.rstrip('/')
        return f"{endpoint_url}/{bucket}/{key}"
    else:
        # AWS S3
        return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"
