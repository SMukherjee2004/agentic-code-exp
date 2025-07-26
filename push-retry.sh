#!/bin/bash
# Script to retry Docker push with backoff

IMAGE_NAME="smukherjee2004/ai-github-analyzer:latest"
MAX_RETRIES=5
RETRY_COUNT=0

echo "🚀 Starting Docker push with retry logic..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "📦 Attempt $((RETRY_COUNT + 1)) of $MAX_RETRIES"
    
    if docker push $IMAGE_NAME; then
        echo "✅ Successfully pushed $IMAGE_NAME to Docker Hub!"
        exit 0
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            WAIT_TIME=$((RETRY_COUNT * 30))
            echo "❌ Push failed. Waiting ${WAIT_TIME} seconds before retry..."
            sleep $WAIT_TIME
        fi
    fi
done

echo "❌ Failed to push after $MAX_RETRIES attempts"
echo "💡 Try the following:"
echo "   1. Check your internet connection"
echo "   2. Make sure you're logged into Docker Hub: docker login"
echo "   3. Try pushing during off-peak hours"
echo "   4. Consider using the local build option in docker-compose.yml"
exit 1
