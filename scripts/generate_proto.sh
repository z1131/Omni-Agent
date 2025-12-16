#!/bin/bash
# 生成 gRPC Python 代码

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PROTO_DIR="$PROJECT_DIR/proto"
OUTPUT_DIR="$PROJECT_DIR/src/server/grpc/generated"

echo "Generating gRPC code..."
echo "Proto dir: $PROTO_DIR"
echo "Output dir: $OUTPUT_DIR"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 生成 Python gRPC 代码
python -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROTO_DIR"/*.proto

# 修复 import 路径
# protoc 生成的代码使用 import stt_pb2，但我们需要相对导入
cd "$OUTPUT_DIR"
for file in *_pb2_grpc.py; do
    if [[ -f "$file" ]]; then
        # macOS sed 需要 -i '' 
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' 's/^import \(.*\)_pb2 as/from . import \1_pb2 as/' "$file"
        else
            sed -i 's/^import \(.*\)_pb2 as/from . import \1_pb2 as/' "$file"
        fi
    fi
done

# 同样修复 _pb2.py 文件中的 import
for file in *_pb2.py; do
    if [[ -f "$file" ]]; then
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' 's/^import \(stt_pb2\|llm_pb2\) as/from . import \1 as/' "$file"
        else
            sed -i 's/^import \(stt_pb2\|llm_pb2\) as/from . import \1 as/' "$file"
        fi
    fi
done

# 创建 __init__.py
cat > "$OUTPUT_DIR/__init__.py" << 'EOF'
"""
Auto-generated gRPC code for Omni-Agent.
Do not edit manually.
"""
from .omni_agent_pb2 import *
from .omni_agent_pb2_grpc import *
from .stt_pb2 import *
from .stt_pb2_grpc import *
from .llm_pb2 import *
from .llm_pb2_grpc import *
EOF

echo "Done! Generated files in $OUTPUT_DIR"
ls -la "$OUTPUT_DIR"
