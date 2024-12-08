
python main.py \
    --mode human \
    --input human \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9000 --stream







### server d
python main.py \
    --server \
    --mode llm \
    --server-ws-uri ws://127.0.0.1:9003 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9004 --stream

### server c
python main.py \
    --server \
    --mode llm \
    --server-ws-uri ws://127.0.0.1:9002 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9003 --stream

# server b
python main.py \
    --server \
    --mode persona \
    --persona english_german_translator \
    --server-ws-uri ws://127.0.0.1:9001 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9002 --stream

# server a
python main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9000 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9001 --stream

# final displayer
```bash
python main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9004 \
    --output human \
    --stream
```