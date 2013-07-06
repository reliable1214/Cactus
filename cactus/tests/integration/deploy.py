#coding:utf-8
import os
import StringIO
import gzip

from cactus.tests.integration import IntegrationTestCase
from cactus.tests.integration.s3 import S3TestHTTPConnection


class DeployTestCase(IntegrationTestCase):
    connection_class = S3TestHTTPConnection

    def setUp(self):
        super(DeployTestCase, self).setUp()
        self.site.config.set('aws-bucket-name', 'website')

    def test_simple_deploy(self):
        """
        Test our file deployment

        - Uploaded
        - Have the correct name
        - Compressed (if useful) -- #TODO
        - Publicly readable
        """

        payload = "\x01" * 1000 + "\x02" * 1000  # Will compress very well

        with open(os.path.join(self.site.static_path, "static.css"), 'wb') as f:
            f.write(payload)

        self.site.upload()

        puts = [req for req in self.connection_factory.requests if req.method == "PUT"]

        # How many files did we upload?
        self.assertEqual(1, len(puts))
        put = puts[0]

        # What file did we upload?
        self.assertEqual("/static/static.css", put.url)

        # Where the AWS standard headers correct?
        self.assertEqual("public-read", put.headers["x-amz-acl"])
        self.assertEqual("gzip", put.headers["content-encoding"])

        # Did we use the correct access key?
        self.assertEqual("AWS 123", put.headers["authorization"].split(':')[0])

        # Did we talk to the right host?
        self.assertEqual("website.s3.amazonaws.com", put.connection.host)

        # Are the file contents correct?
        compressed = gzip.GzipFile(fileobj=StringIO.StringIO(put.body), mode="r")
        self.assertEqual(payload, compressed.read())
