#!/bin/bash

# Full Population Workflow with Zapr Notifications
# Runs all CLI4 population steps sequentially with admin notifications
# Author: CLI4 System
# Date: $(date)

set -e  # Exit on any error

# Configuration
ZAPR_SESSION_ID="6b0c2791-9780-425a-9509-ac2f4c1470a2"
ADMIN_NUMBER="5521981328933"
ZAPR_BASE_URL="https://api.zapr.link/message"
VENV_PATH="$HOME/.virtualenvs/open-data-gov"
PROJECT_ROOT="/Users/fcavalcanti/dev/open-data-gov"

# Dry run mode (set to true to test without sending messages)
DRY_RUN=${DRY_RUN:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="$PROJECT_ROOT/logs/full_population_$(date +%Y%m%d_%H%M%S).log"

# Ensure logs directory exists
mkdir -p "$PROJECT_ROOT/logs"

echo -e "${BLUE}🚀 FULL POPULATION WORKFLOW STARTED${NC}"
echo "Log file: $LOG_FILE"
echo "Start time: $(date)"
echo ""

# Function to send Zapr message
send_zapr_message() {
    local message="$1"
    local response

    echo -e "${YELLOW}📱 Sending Zapr notification...${NC}"

    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${BLUE}🧪 DRY RUN MODE - Would send message:${NC}"
        echo "To: $ADMIN_NUMBER"
        echo "Session: $ZAPR_SESSION_ID"
        echo "Message: $message"
        echo -e "${GREEN}✅ Dry run message logged${NC}"
    else
        # Use correct Zapr API format: POST /message/{sessionID}
        local zapr_url="$ZAPR_BASE_URL/$ZAPR_SESSION_ID"

        # Use jq to properly encode JSON with multiline messages
        local json_payload=$(jq -n --arg numbers "$ADMIN_NUMBER" --arg message "$message" '{numbers: $numbers, message: $message}')

        response=$(curl -s -X POST "$zapr_url" \
            -H "Content-Type: application/json; charset=utf-8" \
            -d "$json_payload")

        if echo "$response" | grep -q '"success":true'; then
            echo -e "${GREEN}✅ Zapr message sent successfully${NC}"
        else
            echo -e "${RED}❌ Zapr message failed: $response${NC}"
            # Continue execution even if notification fails
        fi
    fi
    echo ""
}

# Function to run command and capture output
run_step() {
    local step_name="$1"
    local command="$2"
    local step_log="$LOG_FILE.$(echo "$step_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '_')"

    echo -e "${BLUE}🔄 Starting: $step_name${NC}"
    echo "Command: $command"
    echo "Time: $(date)"
    echo ""

    # Record start time
    local start_time=$(date +%s)

    # Run command and capture output
    if eval "$command" > "$step_log" 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${GREEN}✅ $step_name completed successfully${NC}"
        echo "Duration: ${duration}s"

        # Get summary from output
        local summary=$(tail -20 "$step_log" | grep -E "(completed|processed|inserted|updated|success)" | head -5)

        # Send success notification
        local message="✅ CLI4 $step_name COMPLETED
Duration: ${duration}s
Time: $(date +'%H:%M')

📊 Summary:
$summary

Full log available in system."

        send_zapr_message "$message"

    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${RED}❌ $step_name failed${NC}"
        echo "Duration: ${duration}s"

        # Get error details
        local error_details=$(tail -10 "$step_log" | grep -E "(error|Error|ERROR|failed|Failed)" | head -3)

        # Send failure notification
        local message="❌ CLI4 $step_name FAILED
Duration: ${duration}s
Time: $(date +'%H:%M')

🚨 Error Details:
$error_details

Check system logs for full details."

        send_zapr_message "$message"

        echo -e "${RED}❌ WORKFLOW STOPPED DUE TO ERROR${NC}"
        echo "Check log file: $step_log"
        exit 1
    fi

    # Append step log to main log
    echo "=== $step_name ===" >> "$LOG_FILE"
    cat "$step_log" >> "$LOG_FILE"
    echo "" >> "$LOG_FILE"

    echo ""
}

# Kill any existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
pkill -f "python.*cli4" || true
sleep 2

# Activate virtual environment
echo -e "${YELLOW}🐍 Activating virtual environment...${NC}"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_PATH${NC}"
    exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$PROJECT_ROOT"

echo -e "${GREEN}✅ Environment activated${NC}"
echo "Python: $(which python)"
echo "Working directory: $(pwd)"
echo ""

# Record overall start time
OVERALL_START=$(date +%s)

# Send initial notification
send_zapr_message "🚀 CLI4 FULL POPULATION STARTED

Time: $(date +'%H:%M')
System: $(hostname)

Steps (512 politicians):
1️⃣ Politicians Population (~1-2 hours)
2️⃣ Financial Records (~24-28 hours) ⚠️⚠️
3️⃣ Electoral Records (~2-3 hours)
4️⃣ Network Records (~3-4 hours)
5️⃣ Career History (~1-2 hours) 📋 NEW!
6️⃣ Asset Declarations (~1-2 hours) 🏛️ NEW!
7️⃣ Professional Background (~30-45 min) 💼 NEW!
8️⃣ Parliamentary Events (~1-2 hours) 🏛️ NEW!
9️⃣ Vendor Sanctions (~1 hour) ⚠️ CORRUPTION DETECTION!
🔟 TCU Disqualifications (~30 min) ⚖️ CORRUPTION DETECTION!
1️⃣1️⃣ Senado Politicians (~15 min) 🏛️ FAMILY NETWORKS!
1️⃣2️⃣ Post-Processing (~30 min) 📊 CRITICAL!
1️⃣3️⃣ Wealth Population (~1-2 hours) 💎 OPTIMIZED!
1️⃣4️⃣ Full Validation (~1-3 min) ✅ ALWAYS LAST

⏰ Total estimated: 37-49 HOURS
💡 MUST use tmux/screen - this will run for DAYS!
🎯 NEW: 21,795 sanctions + TCU disqualifications + Senado family networks for corruption detection!"

# Step 1: Politicians Population
run_step "POLITICIANS POPULATION" "python cli4/main.py populate"

# Step 2: Financial Population
run_step "FINANCIAL POPULATION" "python cli4/main.py populate-financial"

# Step 3: Electoral Population
run_step "ELECTORAL POPULATION" "python cli4/main.py populate-electoral"

# Step 4: Network Population
run_step "NETWORK POPULATION" "python cli4/main.py populate-networks"

# Step 5: Career History Population
run_step "CAREER HISTORY POPULATION" "python cli4/main.py populate-career"

# Step 6: Assets Population
run_step "ASSET DECLARATIONS POPULATION" "python cli4/main.py populate-assets"

# Step 7: Professional Background Population
run_step "PROFESSIONAL BACKGROUND POPULATION" "python cli4/main.py populate-professional"

# Step 8: Parliamentary Events Population
run_step "PARLIAMENTARY EVENTS POPULATION" "python cli4/main.py populate-events"

# Step 9: Vendor Sanctions Population (NEW! Corruption Detection)
run_step "VENDOR SANCTIONS POPULATION" "python cli4/main.py populate-sanctions --max-pages 1500"

# Step 10: TCU Disqualifications Population (NEW! Corruption Detection)
run_step "TCU DISQUALIFICATIONS POPULATION" "python cli4/main.py populate-tcu --max-pages 100"

# Step 11: Senado Politicians Population (NEW! Family Networks)
run_step "SENADO POLITICIANS POPULATION" "python cli4/main.py populate-senado"

# Step 12: Post-Processing (MUST RUN BEFORE WEALTH!)
run_step "POST-PROCESSING" "python cli4/main.py post-process"

# Step 13: Wealth Population (DEPENDS ON POST-PROCESSING!)
run_step "WEALTH POPULATION" "python cli4/main.py populate-wealth"

# Step 14: Full Validation (ALWAYS LAST)
run_step "FULL VALIDATION" "python cli4/main.py validate"

# Calculate total duration
OVERALL_END=$(date +%s)
TOTAL_DURATION=$((OVERALL_END - OVERALL_START))
HOURS=$((TOTAL_DURATION / 3600))
MINUTES=$(((TOTAL_DURATION % 3600) / 60))
SECONDS=$((TOTAL_DURATION % 60))

# Send completion notification
echo -e "${GREEN}🎉 FULL POPULATION WORKFLOW COMPLETED SUCCESSFULLY${NC}"
echo "Total duration: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo "End time: $(date)"
echo "Log file: $LOG_FILE"

# Add a note about actual duration vs estimate
DAYS=$((HOURS / 24))
REMAINING_HOURS=$((HOURS % 24))

send_zapr_message "🎉 CLI4 FULL POPULATION COMPLETED

✅ ALL STEPS SUCCESSFUL
Total Duration: ${HOURS}h ${MINUTES}m ${SECONDS}s
(${DAYS} days, ${REMAINING_HOURS} hours)
End Time: $(date +'%H:%M')

📊 Final Status:
✅ Politicians populated
✅ Financial records populated (24-28h)
✅ Electoral records populated
✅ Network records populated
✅ Career history populated (NEW!)
✅ Asset declarations populated (NEW!)
✅ Professional background populated (NEW!)
✅ Parliamentary events populated (NEW!)
✅ Vendor sanctions populated (NEW! 21,795 records)
✅ TCU disqualifications populated (NEW! Federal Audit Court)
✅ Senado politicians populated (NEW! Family networks)
✅ Post-processing completed (aggregates)
✅ Wealth tracking populated (optimized!)
✅ Full validation passed (ALWAYS LAST)

🎯 CORRUPTION DETECTION READY:
✅ 21,795 sanctions for vendor cross-referencing
✅ TCU disqualifications for CPF cross-referencing
✅ Senado politicians for family network detection
✅ Enhanced MVP with corruption validation
✅ Fast local CNPJ/CPF/surname lookups enabled

🗄️ Complete logs available in system
📈 Data pipeline ready for analysis
⏱️ Marathon complete!"

echo -e "${BLUE}📄 Log files created:${NC}"
ls -la "$LOG_FILE"*

echo ""
echo -e "${GREEN}🚀 Workflow completed successfully!${NC}"