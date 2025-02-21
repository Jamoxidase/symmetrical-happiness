first make venv, install requirements.
to load env vars & start proxy at port 4000 run $ dotenv run litellm --config config.yaml --detailed_debug


test call:
curl -X POST 'http://0.0.0.0:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer sk-FsjWvXqIQR2i95CxiAb2sLT8DYdNvHTuESnrQSQdg4' \
-d '{
    "model": "claude-3-5-haiku",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful math tutor. Guide the user through the solution step by step."
      },
      {
        "role": "user",
        "content": "how can I solve 8x + 7 = -23"
      }
    ]
}'