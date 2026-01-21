# Deploy backend to AWS (Docker)

This guide shows a simple path to containerize the FastAPI backend and deploy it to AWS using either App Runner (simplest) or ECS Fargate (more control).

## 1) Prereqs
- AWS account and CLI configured: `aws configure`
- ECR permissions to create repos and push images
- Backend environment values (replace with your actual values):
  - `APP_S3_BUCKET_NAME`
  - `APP_AWS_REGION` (must match the bucket region)
  - `APP_ALLOWED_ORIGINS` (e.g., `["http://localhost:5174","https://your-frontend.example.com"]`)
  - `APP_PRESIGN_EXPIRATION_SECONDS` (e.g., `3600`)
  - `APP_RECOMMENDED_PART_SIZE_MB` (e.g., `10`)
  - Optional: `APP_AWS_ACCESS_KEY_ID`, `APP_AWS_SECRET_ACCESS_KEY`, `APP_AWS_SESSION_TOKEN` (prefer using an IAM role at runtime when possible)

## 2) Build and test locally
From the repo root:

```bash
# Build the backend image (uses backend/Dockerfile)
docker build -t youtube-backend:latest -f backend/Dockerfile .

# Run locally on port 8001 -> container 8000 (optional)
docker run --rm -p 8001:8000 \
  -e APP_S3_BUCKET_NAME=your-bucket \
  -e APP_AWS_REGION=us-east-1 \
  -e APP_ALLOWED_ORIGINS='["http://localhost:5174"]' \
  -e APP_PRESIGN_EXPIRATION_SECONDS=3600 \
  -e APP_RECOMMENDED_PART_SIZE_MB=10 \
  youtube-backend:latest

# Health check
curl http://127.0.0.1:8001/health
```

## 3) Push to ECR
Replace `<REGION>` and `<ACCOUNT_ID>` with your values.

```bash
# Create repo (one-time)
aws ecr create-repository --repository-name youtube-backend --region <REGION>

# Get ECR login and push
aws ecr get-login-password --region <REGION> \
  | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com

docker tag youtube-backend:latest <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/youtube-backend:latest

docker push <ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/youtube-backend:latest
```

## 4) Deploy with AWS App Runner (simplest)
- Create service in AWS Console → App Runner → Create service
  - Source: Container registry → ECR → select your image (`youtube-backend:latest`)
  - Port: `8000`
  - Auto scaling: default is fine
  - Health check path: `/health`
  - Add environment variables matching your backend `.env` keys:
    - `APP_S3_BUCKET_NAME`, `APP_AWS_REGION`, `APP_ALLOWED_ORIGINS`, etc.
  - IAM Access: attach a role that allows S3 operations on your bucket (if not using static credentials).
- Create service. Note the public URL once it’s healthy.

Update your frontend’s API base to the new URL (e.g., `https://<apprunner-id>.<region>.awsapprunner.com/uploads`).

### S3 Bucket CORS (required for browser PUT)
Ensure the bucket has a CORS policy that allows your frontend origins, exposes `ETag`, and allows `PUT`:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://your-frontend.example.com", "http://localhost:5174"],
      "AllowedMethods": ["PUT", "GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "ExposeHeaders": ["ETag", "x-amz-request-id", "x-amz-id-2"]
    }
  ]
}
```

Apply via CLI:

```bash
aws s3api put-bucket-cors \
  --bucket your-bucket \
  --cors-configuration file://bucket-cors.json
```

## 5) (Alternative) Deploy with ECS Fargate
High-level steps:
1. Create an ECR repo and push the image (as above).
2. Create a new ECS cluster (Fargate).
3. Define a Task Definition:
   - Container image: `<ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/youtube-backend:latest`
   - Port mappings: container `8000`
   - Environment variables: same as above
   - Task role / execution role: grant S3 access as needed
4. Create a Service using Fargate launch type
   - Configure a public-facing Application Load Balancer (ALB)
   - Target group health check path: `/health`
5. Update DNS to point to the ALB as needed; update the UI API base URL accordingly.

## Notes
- The backend enforces AWS SigV4 for S3 presigned URLs and expects the bucket region in `APP_AWS_REGION` to match the actual bucket region.
- CORS must be set on the bucket to allow browser `PUT` and to expose the `ETag` header (required for completing multipart upload).
- In App Runner or ECS, prefer IAM roles for the task/service instead of embedding static credentials in env vars.
