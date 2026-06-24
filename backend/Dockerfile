# slim variant omits build tools and docs, reducing image size
#
# "base" holds everything both production and test images need: the
# runtime dependencies and the application code itself. Neither later
# stage re-does this work -- they each start FROM base and only add
# what's specific to their purpose.
FROM python:3.11-slim AS base

WORKDIR /app

# Copy requirements first so this layer is only rebuilt when dependencies change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# "test" stage: adds test-only dependencies (pytest, httpx) and the test
# suite itself, on top of base. This is the stage docker-compose.test.yml
# tells the backend service to build when running the test suite -- it's
# never used for the deployed image.
FROM base AS test

COPY requirements-test.txt pytest.ini .
RUN pip install --no-cache-dir -r requirements-test.txt

COPY ./tests ./tests

CMD ["pytest"]

# "production" stage: built directly from base, so it never sees
# requirements-test.txt or the tests/ directory at all -- not "installed
# then ignored," genuinely never copied into this image's filesystem.
# This is the stage actually deployed.
FROM base AS production

# 0.0.0.0 makes the server reachable from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
