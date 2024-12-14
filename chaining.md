### receiving human
uv run src/main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9004 \
    --output human \
    --stream

### german to english translator
uv run src/main.py \
    --server \
    --mode persona \
    --persona german_english_translator \
    --server-ws-uri ws://127.0.0.1:9003 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9004 \
    --stream

# german helpful native
uv run src/main.py \
    --server \
    --mode persona \
    --persona german_helpful_native \
    --server-ws-uri ws://127.0.0.1:9002 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9003 \
    --stream

# english to german translator
uv run src/main.py \
    --server \
    --mode persona \
    --persona english_german_translator \
    --server-ws-uri ws://127.0.0.1:9001 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9002 \
    --stream

# forwarder
uv run src/main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9000 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9001 \
    --stream

# input client
uv run src/main.py \
    --mode human \
    --input human \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9000 \
    --stream