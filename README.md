# Docker Student Form Task — 5 Containers

This project uses exactly five Docker containers:

1. `student_entry_form` — student entry form — http://localhost:5000
2. `student_viewer_form` — student records page — http://localhost:5001
3. `student_api` — shared REST API — http://localhost:5002
4. `student_redis` — Redis server-side cache
5. `student_mysql` — MySQL database

## Student fields
- Roll No
- Student Name
- Email
- Department
- Semester
- CGPA

## MySQL host volume mapping
MySQL data is persisted on the PC using:

```yaml
volumes:
  - ./mysql-data:/var/lib/mysql
```

So database files stay inside the project's `mysql-data` folder even if the MySQL container is recreated.

## How data flows

```text
Browser
  |
  +--> localhost:5000  Entry Form
  |        |
  |        v
  |      API :5002 -----> MySQL
  |        |
  |        +------------> Redis cache invalidation
  |
  +--> localhost:5001  Records Form
           |
           v
         API :5002 -----> Redis cache first
                           |
                           +--> MySQL on cache miss
```

## Run

Install Docker Desktop, open a terminal in this folder, then run:

```bash
docker compose up --build
```

Open:
- Entry form: http://localhost:5000
- Records page: http://localhost:5001

## Verify five containers

```bash
docker compose ps
```

Expected services:
- mysql
- redis
- api
- entry-form
- viewer-form

## Verify Redis caching

Open http://localhost:5001 twice. The first API response normally comes from `mysql`; the next one comes from `redis-cache` until the 60-second cache expires.

You can also run:

```bash
curl http://localhost:5002/students
```

## Stop containers

```bash
docker compose down
```

To stop and also remove database data from your PC, first run `docker compose down` and then manually delete the `mysql-data` folder. Do not delete it if you need to preserve records.
