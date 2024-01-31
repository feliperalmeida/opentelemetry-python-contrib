import os

from opentelemetry.instrumentation.subprocess import SubprocessInstrumentor
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace import SpanKind


class TestSubprocess(TestBase):
    def setUp(self):
        super().setUp()
        SubprocessInstrumentor().instrument()

    def tearDown(self):
        super().tearDown()
        SubprocessInstrumentor().uninstrument()

    def test_ossystem_empty_cmd(self):
        os.system("")
        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 0)

    def test_ossystem_span_properties(self):
        cmd = "echo ."
        os.system(cmd)
        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "command_execution")
        self.assertEqual(span.kind, SpanKind.INTERNAL)
        self.assertEqual(span.attributes.get("command"), cmd)
        self.assertEqual(span.attributes.get("return_value"), 0)
        self.assertTrue(span.attributes.get("shell"))
