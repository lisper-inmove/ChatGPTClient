install-lib:
	pip install -r requirement.txt
dev:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/app.py
test-chat-completion:
	export PYTHONPATH=`pwd`/src:`pwd`/src/proto/grpc_api && python src/tests/chat_completion.py
grpc-python:
	cd src/proto && make grpc-python
