#!/bin/bash
###############################################################################
# Virtual HIL Framework - ECU Simulator Startup Script
#
# This script starts all ECU simulators with the specified configuration.
###############################################################################

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default configuration
CONFIG_FILE="${PROJECT_ROOT}/config/ecu_config.yaml"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

###############################################################################
# Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    # Check if Python is installed
    if ! command -v python &> /dev/null; then
        log_error "Python is not installed"
        exit 1
    fi

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Install from https://github.com/astral-sh/uv"
        exit 1
    fi

    log_info "Dependencies OK"
}

start_battery_ecu() {
    log_info "Starting Battery ECU..."

    cd "$PROJECT_ROOT"

    # Start battery ECU in background
    nohup uv run python -m ecu_simulation.battery_ecu \
        > "$LOG_DIR/battery_ecu.log" 2>&1 &

    local pid=$!
    echo $pid > "$PID_DIR/battery_ecu.pid"

    log_info "Battery ECU started (PID: $pid)"
}

start_door_ecu() {
    log_info "Starting Door ECU..."

    cd "$PROJECT_ROOT"

    # Start door ECU in background
    nohup uv run python -m ecu_simulation.door_ecu \
        > "$LOG_DIR/door_ecu.log" 2>&1 &

    local pid=$!
    echo $pid > "$PID_DIR/door_ecu.pid"

    log_info "Door ECU started (PID: $pid)"
}

start_can_interface() {
    log_info "Starting CAN Interface..."

    cd "$PROJECT_ROOT"

    # Start CAN interface in background
    nohup uv run python -c "
import asyncio
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from ecu_simulation.can_interface import CANInterface

async def main():
    can = CANInterface()
    await can.start()
    try:
        await can.simulate_bus_traffic()
    except KeyboardInterrupt:
        await can.stop()

asyncio.run(main())
" \
        > "$LOG_DIR/can_interface.log" 2>&1 &

    local pid=$!
    echo $pid > "$PID_DIR/can_interface.pid"

    log_info "CAN Interface started (PID: $pid)"
}

start_diagnostic_server() {
    log_info "Starting Diagnostic Server..."

    cd "$PROJECT_ROOT"

    # Start diagnostic server in background
    nohup uv run python -c "
import asyncio
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from ecu_simulation.diagnostic_server import DiagnosticServer

async def main():
    server = DiagnosticServer()
    await server.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await server.stop()

asyncio.run(main())
" \
        > "$LOG_DIR/diagnostic_server.log" 2>&1 &

    local pid=$!
    echo $pid > "$PID_DIR/diagnostic_server.pid"

    log_info "Diagnostic Server started (PID: $pid)"
}

stop_simulators() {
    log_info "Stopping all simulators..."

    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                if kill -0 "$pid" 2>/dev/null; then
                    kill "$pid"
                    log_info "Stopped process $pid"
                fi
                rm -f "$pid_file"
            fi
        done
    fi

    log_info "All simulators stopped"
}

show_status() {
    log_info "ECU Simulator Status:"

    if [ -d "$PID_DIR" ]; then
        for pid_file in "$PID_DIR"/*.pid; do
            if [ -f "$pid_file" ]; then
                pid=$(cat "$pid_file")
                name=$(basename "$pid_file" .pid)
                if kill -0 "$pid" 2>/dev/null; then
                    echo -e "  ${GREEN}●${NC} $name (PID: $pid)"
                else
                    echo -e "  ${RED}○${NC} $name (not running)"
                fi
            fi
        done
    fi
}

show_help() {
    cat << EOF
Virtual HIL Framework - ECU Simulator Control

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    start       Start all ECU simulators
    stop        Stop all running simulators
    restart     Restart all simulators
    status      Show status of simulators
    help        Show this help message

Options:
    --config    Path to configuration file (default: config/ecu_config.yaml)
    --no-can    Don't start CAN interface
    --no-diag   Don't start diagnostic server

Examples:
    $0 start
    $0 start --config custom_config.yaml
    $0 status
    $0 stop

EOF
}

###############################################################################
# Main Script
###############################################################################

main() {
    check_dependencies

    # Default: start all simulators
    local command="start"
    local start_can=true
    local start_diag=true

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            start|stop|restart|status|help)
                command="$1"
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --no-can)
                start_can=false
                shift
                ;;
            --no-diag)
                start_diag=false
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Execute command
    case $command in
        start)
            log_info "Starting ECU simulators..."
            log_info "Configuration: $CONFIG_FILE"
            start_battery_ecu
            start_door_ecu
            if [ "$start_can" = true ]; then
                start_can_interface
            fi
            if [ "$start_diag" = true ]; then
                start_diagnostic_server
            fi
            sleep 1
            show_status
            log_info "All simulators started. Logs: $LOG_DIR"
            ;;
        stop)
            stop_simulators
            ;;
        restart)
            stop_simulators
            sleep 2
            log_info "Restarting ECU simulators..."
            start_battery_ecu
            start_door_ecu
            if [ "$start_can" = true ]; then
                start_can_interface
            fi
            if [ "$start_diag" = true ]; then
                start_diagnostic_server
            fi
            show_status
            ;;
        status)
            show_status
            ;;
        help)
            show_help
            ;;
    esac
}

# Trap to ensure cleanup on exit
trap stop_simulators EXIT INT TERM

main "$@"
