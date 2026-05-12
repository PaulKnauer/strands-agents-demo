"""CloudWatch Transaction Search infrastructure for AgentCore observability."""

import aws_cdk as cdk
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_logs as logs
from aws_cdk import aws_xray as xray
from constructs import Construct


class TransactionSearchStack(Stack):
    """Enable CloudWatch Transaction Search for the current account/region."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        indexing_percentage = int(
            self.node.try_get_context("transactionSearchIndexingPercentage") or "100"
        )
        if not 0 <= indexing_percentage <= 100:
            raise ValueError(
                "transactionSearchIndexingPercentage must be between 0 and 100."
            )

        transaction_search_access = logs.CfnResourcePolicy(
            self,
            "TransactionSearchAccessPolicy",
            policy_name="TransactionSearchAccess",
            policy_document=cdk.Fn.sub("""
                {
                  "Version": "2012-10-17",
                  "Statement": [
                    {
                      "Sid": "TransactionSearchXRayAccess",
                      "Effect": "Allow",
                      "Principal": {
                        "Service": "xray.amazonaws.com"
                      },
                      "Action": "logs:PutLogEvents",
                      "Resource": [
                        "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws/spans:*",
                        "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/application-signals/data:*"
                      ],
                      "Condition": {
                        "ArnLike": {
                          "aws:SourceArn": "arn:${AWS::Partition}:xray:${AWS::Region}:${AWS::AccountId}:*"
                        },
                        "StringEquals": {
                          "aws:SourceAccount": "${AWS::AccountId}"
                        }
                      }
                    }
                  ]
                }
                """),
        )

        transaction_search_config = xray.CfnTransactionSearchConfig(
            self,
            "TransactionSearchConfig",
            indexing_percentage=indexing_percentage,
        )
        transaction_search_config.add_dependency(transaction_search_access)

        CfnOutput(
            self,
            "TransactionSearchStatusCommand",
            value="aws xray get-trace-segment-destination",
            description="Run this command to verify Transaction Search is ACTIVE.",
        )
        CfnOutput(
            self,
            "TransactionSearchIndexingPercentage",
            value=str(indexing_percentage),
            description="Percentage of ingested spans indexed for trace summary search.",
        )
