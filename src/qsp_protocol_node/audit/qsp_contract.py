####################################################################################################
#                                                                                                  #
# (c) 2018 Quantstamp, Inc. All rights reserved.  This content shall not be used, copied,          #
# modified, redistributed, or otherwise disseminated except to the extent expressly authorized by  #
# Quantstamp for credentialed users. This content and its use are governed by the Quantstamp       #
# Demonstration License Terms at <https://s3.amazonaws.com/qsp-protocol-license/LICENSE.txt>.      #
#                                                                                                  #
####################################################################################################

from component import BaseConfigComponent
from utils.eth import mk_read_only_call

class QSPContract(BaseConfigComponent):

    # Must be in sync with
    # https://github.com/quantstamp/qsp-protocol-audit-contract/blob/develop/contracts/QuantstampAuditData.sol#L14
    AUDIT_STATE_SUCCESS = 4

    # Must be in sync with
    # https://github.com/quantstamp/qsp-protocol-audit-contract/blob/develop/contracts/QuantstampAuditData.sol#L15
    AUDIT_STATE_ERROR = 5

    # Must be in sync with
    # https://github__get_next_police_assignment.com/quantstamp/qsp-protocol-audit-contract/blob/develop/contracts/QuantstampAudit.sol#L106
    AVAILABLE_AUDIT_STATE_READY = 1

    # Must be in sync with
    # https://github.com/quantstamp/qsp-protocol-audit-contract/blob/develop/contracts/QuantstampAudit.sol#L110
    AVAILABLE_AUDIT_UNDERSTAKED = 5

    def __init__(self, instance, address, eth_wrapper):
        super().__init__({'address': address})
        self.__instance = instance
        self.__eth_wrapper = eth_wrapper

    def any_request_available(self):
        """
        Locally executes the anyRequestAvailable view function in the QSP Audit contract. 
        """        
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.anyRequestAvailable()
        )

    def assigned_request_count(self):
        """
        Locally executes the assignedRequestCount view function in the QSP Audit contract. 
        """
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.assignedRequestCount(self.eth_wrapper.account.address)
        )

    def claim_rewards(self, wait_for_transaction_receipt=True):
        """
        Executes a transaction invoking the claimRewards function in the QSP Audit contract. 
        """
        return self.__exec_transaction(
            self.__instance.functions.claimRewards(),
            wait_for_transaction_receipt
        )

    def get_audit_timeout_in_blocks(self):
        """
        Locally executes the getAuditTimeoutInBlocks view function in the QSP Audit contract. 
        """
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.getAuditTimeoutInBlocks()
        )

    def get_min_audit_price(self):
        """
        Locally executes the getMinAuditPrice view function in the QSP Audit contract. 
        """
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.getMinAuditPrice(self.__eth_wrapper.account.address)
        )

    def get_min_stake_qsp(self):
        """
        Locally executes the getMinAuditStake view function in the QSP Audit
        contract (wei-QSP), converting the result back to QSP.
        """
        min_stake = self.__eth_wrapper.mk_read_only_call(self.__instance.functions.getMinAuditStake())

        # Puts the result (wei-QSP) back to QSP
        return min_stake / (10 ** 18)

    def get_max_assigned_requests(self):
        """
        Locally executes the getMaxAssignedRequests view function in the QSP Audit contract. 
        """
        return self.__eth_wrapper.mk_read_only_call(self.__instance.functions.getMaxAssignedRequests())        

    def get_next_audit_request(self, wait_for_transaction_receipt=True):
        """
        Executes a transaction invoking the getNextAuditRequest function in the QSP Audit contract. 
        """
        return self.__exec_transaction(
            self.__instance.functions.getNextAuditRequest(),
            wait_for_transaction_receipt
        )
        
    def get_next_police_assignment(self):
        """
        Locally executes the getNextPoliceAssignment view function in the QSP Audit contract. 
        """
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.getNextPoliceAssignment()
        )

    def get_report(self, request_id):
        """
        Locally executes the getReport view function in the QSP Audit contract.
        Returns a hex representation of the compressed report.
        """
        compressed_report_bytes = self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.getReport(request_id)
        )
        if compressed_report_bytes is None or len(compressed_report_bytes) == 0:
            return None

        return compressed_report_bytes.hex()

    def has_enough_stake(self):
        """
        Locally executes the hasEnoughStake view function in the QSP Audit contract.
        """
        return self.__eth_wrapper.mk_read_only_call(
                    self.__instance.functions.hasEnoughStake(self.__eth_wrapper.account.address)
                )

    def has_available_rewards(self):
        """
        Locally executes the hasAvailableRewards view function in the QSP Audit contract.
        """
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.hasAvailableRewards()
        )

    def is_audit_finished(self, request_id):
        """
        Locally executes the isAuditFinished view function in the QSP Audit contract.
        """       
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.isAuditFinished(request_id)
        )

    def is_police_node(self):
        """
        Locally executes the isPoliceNode view function in the QSP Audit
        contract. If call to smart contract fails, assumes the node is not
        a police officer.
        """
        is_police = False
        try:
            is_police = self.__eth_wrapper.mk_read_only_call(
                self.config.audit_contract.functions.isPoliceNode(self.__eth_wrapper.account.address)
            )
        except Exception as err:
            self.get_logger().debug("Failed to check if node is a police officer: {0}".format(err))
            self.get_logger().debug("Assuming the node is not a police officer.")

        return is_police


    def my_most_recent_assigned_audit(self):
        """
        Locally executes the myMostRecentAssignedAudit view function in the QSP Audit contract.
        """       
        return self.__eth_wrapper.mk_read_only_call(
            self.__instance.functions.myMostRecentAssignedAudit()
        )

    def set_audit_node_price(self, price_qsp, wait_for_transaction_receipt=True):
        """
        Executes a transaction invoking the setAuditNodePrice function in the
        QSP Audit contract. Takes the input in QSP, converting it to wei-QSP
        """
        price_wei_qsp = price_qsp * (10 ** 18)
        return self.__exec_transaction(
            self.__instance.functions.setAuditNodePrice(price_wei_qsp),
            wait_for_transaction_receipt
        )

    def submit_audit_report(self, request_id, audit_state, compressed_report, wait_for_transaction_receipt=True):
        # TODO: already preparing for upcoming change in QSP-1000
        """
        Executes a transaction invoking the submitAuditReport function in the QSP Audit contract. 
        """
        # Convert from a bitstring to a bytes array
        return self.__exec_transaction(self.__instance.functions.submitReport(
                                    request_id,
                                    audit_state,
                                    compressed_report_bytes),
                                 wait_for_transaction_receipt
                                )

    def submit_police_report(self, request_id, compressed_report, is_verified, wait_for_transaction_receipt=True):
        """
        Submits the police report to the entire QSP network.
        """
        return self.__exec_transaction(self.__config.audit_contract.functions.submitPoliceReport(
                                    request_id,
                                    compressed_report_bytes,
                                    is_verified),
                                    wait_for_transaction_receipt
                                )

    def __exec_transaction(self, function_call, wait_for_transaction_receipt):
        tx_hash = None
        try:
            tx_hash = eth_wrapper.send_signed_transaction(
                function_call,
                wait_for_transaction_receipt
            )
        except Timeout as timeout_error:
            self.get_logger().debug("Transaction receipt timeout happened for {0}. {1}".format(
                    function_call,
                    timeout_err
                )
            )
            raise timeout_err
    
        except DeduplicationException as deduplication_err:
            error_msg = "A transaction already exists for {0}," \
                        + " but has not yet been mined. " \
                        + " This may take several iterations. {1}"
            self.get_logger().debug(error_msg.format(
                    function_call,
                    deduplication_err
                )
            )
            raise depluplication_err

        except TransactionNotConfirmedException as transaction_not_confirmed_err:
            error_msg = "The {0} transaction executed, but it was uncled and never recovered. {1}"
            self.get_logger().debug(error_msg.format(
                    function_call,
                    transaction_not_confirmed_err
                )
            )
            raise transaction_not_confirmed_err

        except Exception as err:
            error_msg = "Error executing {0} transaction. {1}"
            self.get_logger().exception(error_msg.format(
                transaction,
                err
                )
            )
            raise err

        self.get_logger.debug("Successfully executed {0} transaction (msg.sender = {1}).".format(
                function_call,
                self.__eth_wrapper.account.address
            )
        )

        return tx_hash