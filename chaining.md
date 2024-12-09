### receiving human
python main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9004 \
    --output human

### german to english translator
python main.py \
    --server \
    --mode persona \
    --persona german_english_translator \
    --server-ws-uri ws://127.0.0.1:9003 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9004

# german helpful native
chrishayuk$ python main.py \
    --server \
    --mode persona \
    --persona german_helpful_native \
    --server-ws-uri ws://127.0.0.1:9002 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9003

# english to german translator
python main.py \
    --server \
    --mode persona \
    --persona english_german_translator \
    --server-ws-uri ws://127.0.0.1:9001 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9002

# forwarder
python main.py \
    --server \
    --mode forwarder \
    --server-ws-uri ws://127.0.0.1:9000 \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9001

# input client
python main.py \
    --mode human \
    --input human \
    --output websocket \
    --output-ws-uri ws://127.0.0.1:9000