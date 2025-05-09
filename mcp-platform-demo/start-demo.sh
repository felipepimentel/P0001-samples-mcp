#!/bin/bash
# start-demo.sh

echo "🚀 Starting MCP DevOps Platform Demo..."
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prerequisites() {
    echo "📋 Checking prerequisites..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found${NC}"
        exit 1
    fi
    
    # Required ports
    ports=(3000 3001 8000 8001 9090 9999 16686)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            echo -e "${YELLOW}⚠️  Port $port in use${NC}"
        fi
    done
    
    echo -e "${GREEN}✅ Prerequisites checked${NC}"
}

# Clean previous environment
cleanup() {
    echo "🧹 Cleaning previous environment..."
    docker-compose down -v
    docker system prune -f
    echo -e "${GREEN}✅ Environment cleaned${NC}"
}

# Build images
build_images() {
    echo "🏗️  Building images..."
    docker-compose build --parallel
    echo -e "${GREEN}✅ Images built${NC}"
}

# Start core services
start_core_services() {
    echo "🔧 Starting core services..."
    docker-compose up -d postgres redis rabbitmq
    
    # Wait for services to be ready
    echo "⏳ Waiting for databases..."
    sleep 10
    
    docker-compose up -d kong prometheus grafana jaeger
    sleep 10
    
    echo -e "${GREEN}✅ Core services started${NC}"
}

# Start MCP and services
start_mcp_services() {
    echo "🧠 Starting MCP Gateway and services..."
    docker-compose up -d mcp-gateway demo-orchestrator
    docker-compose up -d user-service payment-service order-service
    docker-compose up -d platform-dashboard
    
    echo -e "${GREEN}✅ MCP and services started${NC}"
}

# Configure Kong
setup_kong() {
    echo "🌐 Configuring API Gateway..."
    sleep 5
    
    # Wait for Kong to be ready
    until $(curl --output /dev/null --silent --head --fail http://localhost:8001); do
        printf '.'
        sleep 2
    done
    
    echo -e "\n${GREEN}✅ Kong configured${NC}"
}

# Check service health
health_check() {
    echo "🏥 Checking service health..."
    
    services=(
        "http://localhost:3000|Grafana"
        "http://localhost:3001|Dashboard"
        "http://localhost:8000|Kong Gateway"
        "http://localhost:9090|Prometheus"
        "http://localhost:16686|Jaeger"
    )
    
    for service in "${services[@]}"; do
        IFS='|' read -r url name <<< "$service"
        if curl --output /dev/null --silent --head --fail "$url"; then
            echo -e "${GREEN}✅ $name is healthy${NC}"
        else
            echo -e "${RED}❌ $name is not responding${NC}"
        fi
    done
}

# Show access URLs
show_urls() {
    echo -e "\n🎉 ${GREEN}Platform started successfully!${NC}"
    echo "================================================"
    echo "📌 Access URLs:"
    echo ""
    echo "🎯 Main Dashboard: http://localhost:3001"
    echo "📊 Grafana: http://localhost:3000 (admin/demo)"
    echo "🔍 Jaeger Tracing: http://localhost:16686"
    echo "🌐 Kong Admin: http://localhost:8001"
    echo "📡 RabbitMQ: http://localhost:15672 (demo/demo)"
    echo "🐳 Portainer: http://localhost:9000"
    echo ""
    echo "📚 Documentation: http://localhost:8082"
    echo "🤖 MCP WebSocket: ws://localhost:9999"
    echo ""
    echo "================================================"
    echo "🚀 To start the demo, open VSCode and type:"
    echo "   'I'm new to the team, help me with onboarding'"
    echo "================================================"
}

# Main function
main() {
    echo "🎬 Starting MCP DevOps Platform Demo..."
    echo ""
    
    check_prerequisites
    cleanup
    build_images
    start_core_services
    start_mcp_services
    setup_kong
    
    echo ""
    echo "⏳ Waiting for full initialization..."
    sleep 20
    
    health_check
    show_urls
    
    echo ""
    echo "📝 Logs available with: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    echo ""
    echo "✨ Platform ready for demonstration! ✨"
}

# Execute
main 