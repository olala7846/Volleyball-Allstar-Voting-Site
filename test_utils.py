from google.appengine.ext import testbed
from utils import sanitize_email_local_part
import os


class GAETestMixin:
    """ Sets up GAE testbed stubs """

    def setup_method(self, method):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # root_path must be set the the location of queue.yaml.
        self.testbed.init_taskqueue_stub(root_path=os.path.abspath('.'))
        self.taskqueue_stub = self.testbed.get_stub(
            testbed.TASKQUEUE_SERVICE_NAME)

    def teardown_method(self, method):
        self.testbed.deactivate()


class TestSanitizeEmailLocalPart(GAETestMixin):

    def test_id_upper_case(self):
        assert sanitize_email_local_part('B98765432') == 'b98765432'
        assert sanitize_email_local_part('b98765432') == 'b98765432'
        assert sanitize_email_local_part('B96A02034') == 'b96a02034'

    def test_teacher_id(self):
        assert sanitize_email_local_part('lls') == 'lls'
        assert sanitize_email_local_part('Lls') == 'lls'
        assert sanitize_email_local_part('LLS') == 'lls'

    def test_id_with_spaces(self):
        assert sanitize_email_local_part(' B98765432') == 'b98765432'
        assert sanitize_email_local_part('B98 765432') == 'b98765432'
        assert sanitize_email_local_part('B98765432  ') == 'b98765432'
        assert sanitize_email_local_part('B98765432\t') == 'b98765432'
        assert sanitize_email_local_part('B98765432\n') == 'b98765432'

    def test_id_with_special_characters(self):
        assert sanitize_email_local_part('B98+765432') == 'b98765432'
        assert sanitize_email_local_part('B98.765432') == 'b98765432'
