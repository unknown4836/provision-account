# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the BSD-style license. See LICENSE file in the project root for full license information.

import os

import attrdict
import cfnresponse
import pytest
from voluptuous import All, Schema, ALLOW_EXTRA
from toolz.curried import assoc_in

import src.app as app


LOCAL_ACCOUNT_ID = '123456789012'
REMOTE_ACCOUNT_ID = '999999999999'

LOCAL_BUCKET_NAME = 'local-bucket'
REMOTE_BUCKET_NAME = 'remote-bucket'

LOCAL_TRAIL_ARN = f'arn:aws:cloudtrail:us-east-1:{LOCAL_ACCOUNT_ID}:trail/local-trail'
REMOTE_TRAIL_ARN = f'arn:aws:cloudtrail:us-east-1:{REMOTE_ACCOUNT_ID}:trail/remote-trail'

LOCAL_TOPIC_ARN = f'arn:aws:sns:us-east-1:{LOCAL_ACCOUNT_ID}:local-cloudtrail-topic'
REMOTE_TOPIC_ARN = f'arn:aws:sns:us-east-1:{REMOTE_ACCOUNT_ID}:remote-cloudtrail-topic'


# TODO: Replace these fixtures with Voluptuous Schemas + Hypothesis + Property Tests
@pytest.fixture()
def cfn_event():
    return {
        'LogicalResourceId': 'some logical resource id',
        'PhysicalResourceId': None,
        'RequestId': 'some request id',
        'RequestType': 'Create',
        'ResourceProperties': {
            'AccountId': LOCAL_ACCOUNT_ID,
        },
        'ResponseURL': 'https://cfn.amazonaws.com/callback',
        'StackId': 'some-cfn-stack-id',
    }


@pytest.fixture()
def describe_trails_response_local():
    return {
        'trailList': [
            {
                'HasCustomEventSelectors': True,
                'HomeRegion': 'us-east-1',
                'IncludeGlobalServiceEvents': True,
                'IsMultiRegionTrail': True,
                'IsOrganizationTrail': False,
                'LogFileValidationEnabled': True,
                'Name': 'my-local-trail',
                'S3BucketName': LOCAL_BUCKET_NAME,
                'SnsTopicARN': LOCAL_TOPIC_ARN,
                'SnsTopicName': LOCAL_TOPIC_ARN,
                'TrailARN': LOCAL_TRAIL_ARN,
            },
        ],
    }


@pytest.fixture()
def describe_trails_response_remote():
    return {
        'trailList': [
            {
                'HasCustomEventSelectors': True,
                'HomeRegion': 'us-east-1',
                'IncludeGlobalServiceEvents': True,
                'IsMultiRegionTrail': True,
                'IsOrganizationTrail': False,
                'LogFileValidationEnabled': True,
                'Name': 'my-local-trail',
                'S3BucketName': LOCAL_BUCKET_NAME,
                'SnsTopicARN': REMOTE_TOPIC_ARN,
                'SnsTopicName': REMOTE_TOPIC_ARN,
                'TrailARN': REMOTE_TRAIL_ARN,
            },
        ],
    }


@pytest.fixture()
def describe_trails_response_remote_bucket():
    return {
        'trailList': [
            {
                'HasCustomEventSelectors': True,
                'HomeRegion': 'us-east-1',
                'IncludeGlobalServiceEvents': True,
                'IsMultiRegionTrail': True,
                'IsOrganizationTrail': False,
                'LogFileValidationEnabled': True,
                'Name': 'my-local-trail',
                'S3BucketName': REMOTE_BUCKET_NAME,
                'SnsTopicARN': LOCAL_TOPIC_ARN,
                'SnsTopicName': LOCAL_TOPIC_ARN,
                'TrailARN': LOCAL_TRAIL_ARN,
            },
        ],
    }


@pytest.fixture()
def list_buckets_response():
    return {
        'Buckets': [
            {
                'Name': LOCAL_BUCKET_NAME,
            }
        ]
    }


@pytest.fixture()
def describe_report_definitions_response_local():
    return {
        'ReportDefinitions': [
            {
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'path',
                'ReportName': 'billing_report',
            },
            {
                "ReportName": "valid-local-report",
                "TimeUnit": "HOURLY",
                "Format": "textORcsv",
                "Compression": "GZIP",
                "AdditionalSchemaElements": [
                    "RESOURCES"
                ],
                "S3Bucket": LOCAL_BUCKET_NAME,
                "S3Prefix": "reports",
                "S3Region": "us-east-1",
                "AdditionalArtifacts": [
                    "REDSHIFT"
                ],
                "RefreshClosedReports": True,
                "ReportVersioning": "CREATE_NEW_REPORT"
            }
        ]
    }


@pytest.fixture()
def describe_report_definitions_response_remote():
    return {
        'ReportDefinitions': [
            {
                "ReportName": "valid-local-report",
                "TimeUnit": "HOURLY",
                "Format": "textORcsv",
                "Compression": "GZIP",
                "AdditionalSchemaElements": [
                    "RESOURCES"
                ],
                "S3Bucket": REMOTE_BUCKET_NAME,
                "S3Prefix": "reports",
                "S3Region": "us-east-1",
                "AdditionalArtifacts": [
                    "REDSHIFT"
                ],
                "RefreshClosedReports": True,
                "ReportVersioning": "CREATE_NEW_REPORT"
            }
        ]
    }


@pytest.fixture()
def describe_report_definitions_response_invalid():
    return {
        'ReportDefinitions': [
            {
                'S3Bucket': LOCAL_BUCKET_NAME,
                'S3Prefix': 'path',
                'ReportName': 'billing_report',
            },
        ]
    }


@pytest.fixture(scope='function')
def context(mocker):
    context = attrdict.AttrMap()
    orig_env = os.environ.copy()
    context.os = {'environ': os.environ}
    context.prefix = app.__name__
    context.mock_cfnresponse_send = mocker.patch(f'{context.prefix}.cfnresponse.send', autospec=True)
    context.mock_ct = mocker.patch(f'{context.prefix}.ct', autospec=True)
    context.mock_cur = mocker.patch(f'{context.prefix}.cur', autospec=True)
    context.mock_s3 = mocker.patch(f'{context.prefix}.s3', autospec=True)
    yield context
    os.environ = orig_env
    mocker.stopall()


IS_MASTER_PAYER = Schema({
    'IsMasterPayerAccount': True,
    'MasterPayerBillingBucketName': LOCAL_BUCKET_NAME,
}, extra=ALLOW_EXTRA, required=True)

IS_AUDIT = Schema({
    'IsAuditAccount': True,
}, extra=ALLOW_EXTRA, required=True)

IS_CONNECTED = Schema({
    'IsConnectedAccount': True,
}, extra=ALLOW_EXTRA, required=True)

IS_CLOUDTRAIL_OWNER = Schema({
    'CloudTrailSNSTopicName': LOCAL_TOPIC_ARN,
    'IsCloudTrailAccount': True,
}, extra=ALLOW_EXTRA, required=True)

ALL_LOCAL = All(IS_MASTER_PAYER, IS_AUDIT, IS_CONNECTED, IS_CLOUDTRAIL_OWNER)


@pytest.mark.unit
def test_handler_all_local(context, cfn_event, describe_trails_response_local, list_buckets_response, describe_report_definitions_response_local):
    context.mock_ct.describe_trails.return_value = describe_trails_response_local
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': LOCAL_BUCKET_NAME,
        'CloudTrailSNSTopicName': LOCAL_TOPIC_ARN,
        'IsAuditAccount': True,
        'IsCloudTrailAccount': True,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': True,
        'MasterPayerBillingBucketName': LOCAL_BUCKET_NAME,
    }


@pytest.mark.unit
def test_handler_non_audit(context, cfn_event, describe_trails_response_remote_bucket, list_buckets_response, describe_report_definitions_response_local):
    context.mock_ct.describe_trails.return_value = describe_trails_response_remote_bucket
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': REMOTE_BUCKET_NAME,
        'CloudTrailSNSTopicName': LOCAL_TOPIC_ARN,
        'IsAuditAccount': False,
        'IsCloudTrailAccount': True,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': True,
        'MasterPayerBillingBucketName': LOCAL_BUCKET_NAME,
    }


@pytest.mark.unit
def test_handler_non_cloudtrail_owner(context, cfn_event, describe_trails_response_remote, list_buckets_response, describe_report_definitions_response_local):
    context.mock_ct.describe_trails.return_value = describe_trails_response_remote
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_local
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': LOCAL_BUCKET_NAME,
        'CloudTrailSNSTopicName': REMOTE_TOPIC_ARN,
        'IsAuditAccount': True,
        'IsCloudTrailAccount': False,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': True,
        'MasterPayerBillingBucketName': LOCAL_BUCKET_NAME,
    }


@pytest.mark.unit
def test_handler_non_master_payer_invalid(context, cfn_event, describe_trails_response_local, list_buckets_response, describe_report_definitions_response_invalid):
    context.mock_ct.describe_trails.return_value = describe_trails_response_local
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_invalid
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': LOCAL_BUCKET_NAME,
        'CloudTrailSNSTopicName': LOCAL_TOPIC_ARN,
        'IsAuditAccount': True,
        'IsCloudTrailAccount': True,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': False,
        'MasterPayerBillingBucketName': None,
    }


@pytest.mark.unit
def test_handler_non_master_payer_remote(context, cfn_event, describe_trails_response_local, list_buckets_response, describe_report_definitions_response_remote):
    context.mock_ct.describe_trails.return_value = describe_trails_response_local
    context.mock_cur.describe_report_definitions.return_value = describe_report_definitions_response_remote
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': LOCAL_BUCKET_NAME,
        'CloudTrailSNSTopicName': LOCAL_TOPIC_ARN,
        'IsAuditAccount': True,
        'IsCloudTrailAccount': True,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': False,
        'MasterPayerBillingBucketName': REMOTE_BUCKET_NAME,
    }


@pytest.mark.unit
def test_handler_cannot_determine_audit_only(context, cfn_event, list_buckets_response):
    context.mock_ct.describe_trails.return_value = {'trailList': []}
    context.mock_cur.describe_report_definitions.return_value = {'ReportDefinitions': []}
    context.mock_s3.list_buckets.return_value = list_buckets_response
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == {
        'AuditCloudTrailBucketName': None,
        'CloudTrailSNSTopicName': None,
        'IsAuditAccount': False,
        'IsCloudTrailAccount': False,
        'IsConnectedAccount': True,
        'IsMasterPayerAccount': False,
        'MasterPayerBillingBucketName': None,
    }


@pytest.mark.unit
def test_handler_only_connected(context, cfn_event):
    context.mock_ct.describe_trails.return_value = {'trailList': []}
    context.mock_cur.describe_report_definitions.return_value = {'ReportDefinitions': []}
    context.mock_s3.list_buckets.return_value = {'Buckets': []}
    ret = app.handler(cfn_event, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == assoc_in(app.DEFAULT_OUTPUT, ['IsConnectedAccount'], True)


@pytest.mark.unit
def test_handler_exception(context):
    ret = app.handler({}, None)
    assert ret is None
    assert context.mock_cfnresponse_send.call_count == 1
    ((_, _, status, output, _), kwargs) = context.mock_cfnresponse_send.call_args
    assert status == cfnresponse.SUCCESS
    assert output == app.DEFAULT_OUTPUT