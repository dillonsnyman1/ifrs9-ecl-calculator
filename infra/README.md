# Infrastructure

Terraform config that deploys the dashboard to AWS using only default AWS
URLs (no custom domain/Route 53/ACM):

```
                ┌──────────────┐        ┌──────────────────────┐
   users ─────▶ │  CloudFront  │ ─────▶ │  S3 (frontend bucket)  │
                └──────────────┘        └──────────────────────┘
                       (OAC: bucket has no public access)

                ┌──────────────┐        ┌──────────────────────┐
   browser ───▶ │ API Gateway  │ ─────▶ │  Lambda (container)   │ ◀── image
                │  (HTTP API)  │        │  FastAPI via Mangum    │     from ECR
                └──────────────┘        └──────────────────────┘
```

- **Frontend**: the Vite build output is synced to a private S3 bucket and
  served through a CloudFront distribution using Origin Access Control
  (OAC) - the bucket itself is never publicly reachable.
- **Backend**: the FastAPI app runs in a Lambda function packaged as a
  container image (pandas needs a real Linux build, so a zip deployment
  package isn't practical), built for arm64/Graviton and pushed to ECR.
  API Gateway's HTTP API exposes it with a Lambda proxy integration.

## Layout

- `bootstrap/` - one-time config, applied manually with local state. Creates
  the Terraform remote state backend (S3 + DynamoDB) and the IAM role the
  GitHub Actions deploy workflow assumes via OIDC.
- `main.tf`, `variables.tf`, `frontend.tf`, `backend.tf`, `outputs.tf` - the
  application infrastructure, applied by `.github/workflows/deploy.yml` on
  every push to `main`.

## One-time setup

You need an AWS account and credentials configured locally (e.g. via `aws
configure` or SSO) with permission to create IAM roles/policies, S3 buckets
and a DynamoDB table.

1. **Apply the bootstrap config** (local state, run once):

   ```bash
   cd infra/bootstrap
   terraform init
   terraform apply
   ```

   Note the three outputs: `state_bucket_name`, `lock_table_name` and
   `github_actions_role_arn`.

2. **Add GitHub repository secrets** (Settings → Secrets and variables →
   Actions):

   | Secret | Value |
   |---|---|
   | `AWS_DEPLOY_ROLE_ARN` | `github_actions_role_arn` output |
   | `TF_STATE_BUCKET` | `state_bucket_name` output |
   | `TF_LOCK_TABLE` | `lock_table_name` output |

   Optionally add a repository **variable** `AWS_REGION` if you used a
   region other than the default `eu-west-2` (must match
   `infra/bootstrap`'s `aws_region`).

3. **Run the "Deploy" workflow manually** (Actions tab → Deploy → Run
   workflow). It builds the backend image, runs `terraform init`/`apply`
   against the bootstrap-created backend, builds the frontend against the
   new API URL, and syncs it to S3.

   The workflow is manual-trigger only (`workflow_dispatch`) so that pushes
   to `main` don't attempt a deploy before this setup is done. Once steps
   1-2 are complete, you can switch `.github/workflows/deploy.yml`'s `on:`
   trigger to `push: branches: [main]` to deploy automatically on every
   merge.

4. The CloudFront URL is printed in the workflow's job summary
   (`terraform output cloudfront_domain_name`), and is also available any
   time via:

   ```bash
   cd infra
   terraform init -backend-config="bucket=<state_bucket_name>" \
     -backend-config="key=ifrs9-ecl-calculator/terraform.tfstate" \
     -backend-config="region=<aws_region>" \
     -backend-config="dynamodb_table=<lock_table_name>"
   terraform output cloudfront_domain_name
   ```

## Terraform variables vs GitHub secrets

| Name | Where it lives | Set by |
|---|---|---|
| `aws_region`, `project_name`, `lambda_image_tag` | Terraform variables (`infra/variables.tf`) | `deploy.yml`, with defaults for the first two |
| `AWS_DEPLOY_ROLE_ARN`, `TF_STATE_BUCKET`, `TF_LOCK_TABLE` | GitHub secrets | You, from `infra/bootstrap` outputs (step 2 above) |
| `AWS_REGION` (optional) | GitHub repository variable | You, only if not using `eu-west-2` |

## Tearing down

```bash
cd infra
terraform init -backend-config=... # as above
terraform destroy

cd ../bootstrap
terraform destroy
```
