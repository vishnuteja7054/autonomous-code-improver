#!/bin/bash

# End-to-end test script

set -e

echo "Running end-to-end tests..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set environment variables
export NEO4J_URI=${NEO4J_URI:-"bolt://localhost:7687"}
export NEO4J_USER=${NEO4J_USER:-"neo4j"}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-"password"}
export POSTGRES_URI=${POSTGRES_URI:-"postgresql://postgres:password@localhost:5432/autonomous_code_improver"}
export LLM_ENDPOINT=${LLM_ENDPOINT:-"http://localhost:8000/v1"}
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export NATS_URL=${NATS_URL:-"nats://localhost:4222"}

# Start the application in the background
echo "Starting the application..."
python -m agent.runtime.orchestrator &
APP_PID=$!

# Wait for the application to start
echo "Waiting for the application to start..."
sleep 10

# Check if the application is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "Error: Application failed to start"
    kill $APP_PID
    exit 1
fi

# Create a temporary directory for the test repo
TEST_REPO_DIR=$(mktemp -d)
echo "Creating test repository in $TEST_REPO_DIR"

# Create a simple Python repository for testing
cd $TEST_REPO_DIR
git init
mkdir -p src

# Create a simple Python file with issues
cat > src/main.py << 'EOF'
import sqlite3
import os

def get_user(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # SQL injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    
    user = cursor.fetchone()
    conn.close()
    
    return user

def process_items(items):
    # Inefficient loop
    result = []
    for i in items:
        for j in items:
            if i == j:
                result.append(i)
    return result

# Missing docstring
def helper_function():
    return "help"
EOF

# Create requirements.txt
cat > requirements.txt << 'EOF'
requests==2.28.0
flask==2.2.0
EOF

# Commit the files
git add .
git commit -m "Initial commit"

# Get the absolute path of the test repo
TEST_REPO_ABS_PATH=$(pwd)

# Go back to the project root
cd -

# Submit an enhancement job
echo "Submitting enhancement job..."
JOB_ID=$(curl -s -X POST http://localhost:8000/enhance \
    -H "Content-Type: application/json" \
    -d "{
        \"repo_url\": \"file://$TEST_REPO_ABS_PATH\",
        \"dry_run\": true
    }" | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Wait for the job to complete
echo "Waiting for job to complete..."
while true; do
    STATUS=$(curl -s http://localhost:8000/status/$JOB_ID | jq -r '.status')
    
    if [ "$STATUS" = "completed" ]; then
        echo "Job completed successfully"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "Job failed"
        ERROR=$(curl -s http://localhost:8000/status/$JOB_ID | jq -r '.error_message')
        echo "Error: $ERROR"
        kill $APP_PID
        exit 1
    else
        echo "Job status: $STATUS"
        sleep 5
    fi
done

# Get the job results
echo "Getting job results..."
curl -s http://localhost:8000/status/$JOB_ID | jq '.result_data'

# Stop the application
echo "Stopping the application..."
kill $APP_PID

# Clean up
echo "Cleaning up..."
rm -rf $TEST_REPO_DIR

echo "End-to-end tests completed successfully!"
