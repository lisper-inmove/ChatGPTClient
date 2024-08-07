install-lib:
	pip install -r requirement.txt
dev:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/grpc_server.py
run:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && nohup python src/grpc_server.py &
w-dev: # websocket dev
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/wsserver.py

api:
	cd src/proto && make api-python
entity:
	cd src/proto && make entity
grpc:
	cd src/proto && make grpc-python && make grpc-typescript

test-chat-completion:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && rlwrap python src/tests/chat.py
test-pdf-embedding:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/tests/embedding_pdf.py

test-query-embedding-text:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/tests/embedding_query.py

test:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/tests/test.py
