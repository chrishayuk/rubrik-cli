
## Human to Websocket Server
The following script allows you to connect the cli to a websocket server, but allow the human to interact with the cli

```bash
python main.py \
    --mode human \
    --input websocket \
    --output websocket \
    --input-ws-uri ws://localhost:8000/ws \
    --output-ws-uri ws://localhost:8000/ws
```

## LLM to WebSocket Server
The following script allows you to connect the cli to a websocket server, but allow the LLM to interact with the cli

```bash
python main.py \
    --mode llm \
    --provider ollama \
    --model llama3.3 \
    --input websocket \
    --output websocket \
    --input-ws-uri ws://localhost:8000/ws \
    --output-ws-uri ws://localhost:8000/ws \
    --stream
```

## Persona to WebSocket Server
The following script allows you to connect the cli to a websocket server, but allow the persona to interact with the cli

### server
the following starts up a client as a websocket server

```bash
uv run src/main.py \
    --mode human \
    --input websocket \
    --output stdout \
    --server \
    --server-ws-uri ws://127.0.0.1:8045 \
    --stream
```

```bash
uv run src/main.py \
    --mode persona \
    --input websocket \
    --output stdout \
    --server \
    --server-ws-uri ws://127.0.0.1:8045 \
    --persona sassy_persona \
    --stream
```

### connect client
the following connects a client to the server
it allows us to enter human inputs, but send output to the server

```bash
uv run src/main.py \
    --mode human \
    --input human \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:8045 \
    --stream
```

