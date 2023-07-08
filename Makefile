dev:
	export PYTHONPATH=`pwd`/src:`pwd`/src/api && python src/app.py
test-chat-completion:
	export PYTHONPATH=`pwd`/src:`pwd`/src/api && python src/tests/chat_completion.py
