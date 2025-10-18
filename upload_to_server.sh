#!/bin/bash

# Upload files to server
SERVER="root@saas.akylman.online"
REMOTE_PATH="/opt/beautyhub/saas_salon"

echo "Uploading files to server..."

# Upload Docker files
scp apps/web/Dockerfile $SERVER:$REMOTE_PATH/apps/web/
scp apps/web/.dockerignore $SERVER:$REMOTE_PATH/apps/web/
scp apps/web/tsconfig.json $SERVER:$REMOTE_PATH/apps/web/
scp apps/web/next-env.d.ts $SERVER:$REMOTE_PATH/apps/web/
scp apps/worker/Dockerfile $SERVER:$REMOTE_PATH/apps/worker/
scp apps/worker/beat.Dockerfile $SERVER:$REMOTE_PATH/apps/worker/
scp infra/docker-compose.yml $SERVER:$REMOTE_PATH/infra/

echo "Files uploaded successfully!"
echo ""
echo "Now connect to server and rebuild:"
echo "ssh $SERVER"
echo "cd $REMOTE_PATH"
echo "docker compose -f infra/docker-compose.yml down"
echo "docker system prune -af"
echo "docker compose -f infra/docker-compose.yml build --no-cache"
echo "docker compose -f infra/docker-compose.yml up -d"
