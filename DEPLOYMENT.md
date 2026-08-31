# CI/CD Deployment to Vercel

## Important architecture note

The local assignment still uses **5 Docker containers** with Docker Compose:

1. `student_entry_form`
2. `student_viewer_form`
3. `student_api`
4. `student_mysql`
5. `student_redis`

The local MySQL bind mount remains:

```yaml
volumes:
  - ./mysql-data:/var/lib/mysql
```

Vercel does not deploy `docker-compose.yml` directly and does not provide persistent Docker bind mounts. For cloud deployment, the three HTTP applications run as Vercel Services, while MySQL and Redis must be managed cloud services.

## Public URLs on Vercel

Vercel exposes one HTTPS domain rather than public Docker ports:

- Student Entry: `/`
- Student Records: `/records`
- API: internal service binding only

Ports `5000`, `5001`, and `5002` are still used for local Docker Compose development.

## Pipeline

Deployment is automatic from GitHub Actions:

`git push -> GitHub Actions test -> Vercel build -> Vercel production deploy`

Do **not** deploy production manually with `vercel --prod`.

## One-time setup

1. Push this project to a GitHub repository.
2. Create a Vercel project and set **Framework Preset = Services**.
3. Configure a managed MySQL database and a managed Redis database.
4. Add these Vercel Production environment variables:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`
   - `REDIS_URL`
   - `VIEWER_URL=/records`
   - `ENTRY_URL=/`
5. Add these GitHub repository secrets:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
6. Push/merge to the `main` branch.

The workflow `.github/workflows/vercel-deploy.yml` will deploy automatically after the test job passes.

## Local development

Your original local 5-container setup is unchanged:

```bash
docker compose up --build
```

Local URLs:

- http://localhost:5000
- http://localhost:5001
