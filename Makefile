####################################################################################################
#                                                                                                  #
# (c) 2018 Quantstamp, Inc. All rights reserved.  This content shall not be used, copied,          #
# modified, redistributed, or otherwise disseminated except to the extent expressly authorized by  #
# Quantstamp for credentialed users. This content and its use are governed by the Quantstamp       #
# Demonstration License Terms at <https://s3.amazonaws.com/qsp-protocol-license/LICENSE.txt>.                                                    #
#                                                                                                  #
####################################################################################################

MAKEFLAGS += --silent

QSP_ENV="testnet"
QSP_CONFIG=deployment/local/config.yaml
QSP_ETH_PASSPHRASE=abc123ropsten
QSP_ETH_AUTH_TOKEN="71def1d8ee0f477e87695f16c5d96f13"
QSP_IGNORE_CODES=E121,E122,E123,E124,E125,E126,E127,E128,E129,E131,E501
QSP_LOG_DIR ?= $(HOME)/qsp-protocol

clean:
	find . | egrep "^.*/(__pycache__|.*\.pyc|tests/coverage/htmlcov|tests/coverage/.coverage|app.tar)$$" | xargs rm -rf
	docker rmi --force qsp-protocol-node:latest

run: build
	docker run -it \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v /tmp:/tmp \
		-v $(PWD)/deployment/local/keystore:/app/keystore:Z \
		-v $(QSP_LOG_DIR):/var/log/qsp-protocol:Z \
		-e AWS_ACCESS_KEY_ID="$(shell aws --profile default configure get aws_access_key_id)" \
		-e AWS_SECRET_ACCESS_KEY="$(shell aws --profile default configure get aws_secret_access_key)" \
		-e AWS_DEFAULT_REGION="us-east-1" \
		-e QSP_ETH_AUTH_TOKEN=$(QSP_ETH_AUTH_TOKEN) \
		-e QSP_ETH_PASSPHRASE="$(QSP_ETH_PASSPHRASE)" \
		qsp-protocol-node sh -c "./qsp-protocol-node -a $(QSP_ENV) $(QSP_CONFIG)"

build:
		docker build -t qsp-protocol-node .

test: build
	docker run -it \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v /tmp:/tmp \
		-v $(QSP_LOG_DIR):/var/log/qsp-protocol:Z \
		-e AWS_ACCESS_KEY_ID="$(shell aws --profile default configure get aws_access_key_id)" \
		-e AWS_SECRET_ACCESS_KEY="$(shell aws --profile default configure get aws_secret_access_key)" \
		-e AWS_DEFAULT_REGION="us-east-1" \
		qsp-protocol-node sh -c "./qsp-protocol-node -t"

test-ci: 
	docker build --cache-from $(CACHE_IMAGE) -t qsp-protocol-node .
	docker run -t \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v /tmp:/tmp \
		-v $(QSP_LOG_DIR):/var/log/qsp-protocol:Z \
		-v $(PWD)/tests/coverage:/app/tests/coverage \
		-e AWS_ACCESS_KEY_ID="$(AWS_ACCESS_KEY_ID)" \
		-e AWS_SECRET_ACCESS_KEY="$(AWS_SECRET_ACCESS_KEY)" \
		-e AWS_SESSION_TOKEN="$(AWS_SESSION_TOKEN)" \
		-e AWS_DEFAULT_REGION="us-east-1" \
		qsp-protocol-node sh -c "./qsp-protocol-node -t"

bundle:	test
	./create-bundle.sh

stylecheck:
	echo "Running Stylecheck"
	find . -name \*.py -exec pycodestyle --ignore=$(QSP_IGNORE_CODES) {} +
	echo "Stylecheck passed"

elk:
	cd deployment/local/elk && docker-compose up -d