docker compose down
docker compose up --build -d
docker exec -it massaciuccoli_app python -m versions.v6_1_orchestrator