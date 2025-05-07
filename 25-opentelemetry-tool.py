from mcp.server.fastmcp import FastMCP
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Setup OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)
span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(span_processor)

mcp = FastMCP("OpenTelemetry Tool Example")


@mcp.tool()
def traced_add(a: int, b: int) -> int:
    """Add two numbers with OpenTelemetry tracing"""
    with tracer.start_as_current_span("traced_add") as span:
        span.set_attribute("input.a", a)
        span.set_attribute("input.b", b)
        result = a + b
        span.set_attribute("result", result)
        return result


@mcp.resource("otel://last-span")
def get_last_span() -> str:
    """Return a message indicating tracing is active (see console for spans)"""
    return "Tracing is active. Check your console for OpenTelemetry spans."
