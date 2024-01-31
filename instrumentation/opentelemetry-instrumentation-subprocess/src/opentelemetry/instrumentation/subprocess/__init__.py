# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import shlex
from typing import Collection

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.trace import Tracer
from wrapt import wrap_function_wrapper as _wrap

from opentelemetry import trace
from opentelemetry.instrumentation.subprocess.constants import SPAN_NAME
from opentelemetry.instrumentation.subprocess.package import _instruments
from opentelemetry.instrumentation.subprocess.version import __version__


class CommandLine:
    def __init__(self, args):
        if isinstance(args, str):
            self.tokens = shlex.split(args)
        else:
            raise NotImplementedError

        if len(self.tokens) > 0:
            self.file = self.tokens[0]
        if len(self.tokens) > 1:
            self.args = self.tokens[1:]

    def __str__(self):
        return shlex.join(self.tokens)

    def is_empty(self):
        return len(self.tokens) == 0


# TODO: Truncate commands? What's the limit?
def _instrument(tracer: Tracer):
    def _traced_ossystem(func, instance, args, kwargs):
        cmd = args[0]
        if cmd:
            with tracer.start_as_current_span(SPAN_NAME) as span:
                if span.is_recording():
                    span.set_attribute("command", str(cmd))
                    span.set_attribute("shell", True)
                ret = func(*args, **kwargs)
                span.set_attribute("return_value", ret)
                return ret
        else:
            return func(*args, **kwargs)

    _wrap(os, "system", _traced_ossystem)


class SubprocessInstrumentor(BaseInstrumentor):  # pylint: disable=empty-docstring
    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        tracer_provider = (
            kwargs.get("tracer_provider", None) or trace.get_tracer_provider()
        )

        tracer = trace.get_tracer(
            __name__,
            __version__,
            tracer_provider=tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.11.0",
        )

        _instrument(tracer)

    def _uninstrument(self, **kwargs):
        unwrap(os, "system")
