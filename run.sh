#!/usr/bin/env bash
# Run script for Wyoming Pocket TTS Home Assistant app/add-on
set -e

CONFIG_PATH=/data/options.json

# Read an array (or legacy string) option as comma-separated values.
read_array_option() {
    local key="$1"
    jq -r --arg key "$key" '
        if (.[$key] | type) == "array" then (.[$key] | join(","))
        elif (.[$key] | type) == "string" then .[$key]
        else "" end
    ' "$CONFIG_PATH" 2>/dev/null
}

read_preload() {
    jq -r 'if (.preload_voices | type) == "array" then (.preload_voices | join(","))
           else (.preload_voices // "") end' "$CONFIG_PATH" 2>/dev/null
}

# Join comma-separated fragments, remove empty values and de-duplicate while
# preserving order.
combine_csv() {
    printf '%s\n' "$@" \
        | tr ',' '\n' \
        | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
        | sed '/^$/d' \
        | awk '!seen[$0]++' \
        | paste -sd, -
}

# Releases <=1.4.9 stored preset and custom names together in `voices`. When the
# new preset selector is used, keep arbitrary custom names from that old list but
# discard old preset names so the selector is authoritative.
filter_legacy_custom_voices() {
    local raw="$1"
    local item
    local result=""

    IFS=',' read -ra items <<< "$raw"
    for item in "${items[@]}"; do
        item="${item#${item%%[![:space:]]*}}"
        item="${item%${item##*[![:space:]]}}"
        [ -z "$item" ] && continue
        case "$item" in
            alba|anna|azelma|bill_boerst|caro_davy|charles|cosette|eponine|eve|fantine|george|jane|jean|javert|marius|mary|michael|paul|peter_yearsley|stuart_bell|vera|estelle|juergen|rafael|giovanni|lola)
                ;;
            *)
                result=$(combine_csv "$result" "$item")
                ;;
        esac
    done
    printf '%s' "$result"
}

if [ -f "$CONFIG_PATH" ]; then
    LANGUAGE=$(jq -r '.language // "en"' "$CONFIG_PATH")
    QUALITY=$(jq -r '.quality // "balanced"' "$CONFIG_PATH")
    VOICES_DIR=$(jq -r '.voices_dir // "/share/tts-voices"' "$CONFIG_PATH")
    DEBUG=$(jq -r '.debug // false' "$CONFIG_PATH")
    HF_TOKEN=$(jq -r '.hf_token // ""' "$CONFIG_PATH")
    DEVICE=$(jq -r '.device // "cpu"' "$CONFIG_PATH")
    PRESET_VOICES_CONFIG=$(read_array_option 'preset_voices')
    CUSTOM_VOICES=$(read_array_option 'custom_voices')
    LEGACY_VOICES=$(read_array_option 'voices')
    LEGACY_VOICE=$(jq -r '.voice // ""' "$CONFIG_PATH" 2>/dev/null)
    LEGACY_PRELOAD=$(read_preload)
else
    # Standalone Docker defaults remain conservative/backwards compatible.
    LANGUAGE="${LANGUAGE:-en}"
    QUALITY="${QUALITY:-balanced}"
    VOICES_DIR="${VOICES_DIR:-/share/tts-voices}"
    DEBUG="${DEBUG:-false}"
    HF_TOKEN="${HF_TOKEN:-}"
    DEVICE="${DEVICE:-cpu}"
    PRESET_VOICES_CONFIG="${PRESET_VOICES:-}"
    CUSTOM_VOICES="${CUSTOM_VOICES:-}"
    LEGACY_VOICES="${VOICES:-alba}"
    LEGACY_VOICE="${LEGACY_VOICE:-}"
    LEGACY_PRELOAD="${LEGACY_PRELOAD:-}"
fi

# New UI: selected presets are authoritative, but preserve any custom names from
# an older combined `voices` list. If no preset selector value is present, retain
# the legacy list exactly so upgrades remain backwards compatible.
if [ -n "$PRESET_VOICES_CONFIG" ] && [ "$PRESET_VOICES_CONFIG" != "null" ]; then
    LEGACY_CUSTOM_VOICES=$(filter_legacy_custom_voices "$LEGACY_VOICES")
    VOICES=$(combine_csv "$PRESET_VOICES_CONFIG" "$CUSTOM_VOICES" "$LEGACY_CUSTOM_VOICES")
else
    VOICES=$(combine_csv "$LEGACY_VOICES" "$CUSTOM_VOICES")
fi

# Export Hugging Face token if provided.
if [ -n "$HF_TOKEN" ] && [ "$HF_TOKEN" != "null" ]; then
    export HF_TOKEN
    echo "Hugging Face token configured"
fi

mkdir -p "$VOICES_DIR"

ARGS=(
    --host "0.0.0.0"
    --port "10200"
    --language "$LANGUAGE"
    --quality "$QUALITY"
    --voices-dir "$VOICES_DIR"
    --device "$DEVICE"
    --voices "$VOICES"
)

# Legacy passthrough (used by the server only when --voices is empty).
[ "$LEGACY_VOICE" = "null" ] && LEGACY_VOICE=""
[ -n "$LEGACY_VOICE" ] && ARGS+=(--voice "$LEGACY_VOICE")
case "$LEGACY_PRELOAD" in
    true | True | TRUE) LEGACY_PRELOAD="all" ;;
    false | False | FALSE | null) LEGACY_PRELOAD="" ;;
esac
[ -n "$LEGACY_PRELOAD" ] && ARGS+=(--preload-voices "$LEGACY_PRELOAD")

if [ "$DEBUG" = "true" ]; then
    ARGS+=(--debug)
fi

echo "========================================"
echo "Wyoming Pocket TTS Server"
echo "========================================"
echo "Language: $LANGUAGE"
echo "Quality: $QUALITY"
echo "Device: $DEVICE"
echo "Voices: ${VOICES:-<all built-in + custom (on demand)>}"
echo "Voices dir: $VOICES_DIR"
echo "Debug: $DEBUG"
echo "========================================"

# Function to send discovery info to Home Assistant
send_discovery() {
    # Wait for the server to be ready (up to 5 minutes for first model download)
    local max_wait=300
    local waited=0
    echo "Waiting for Wyoming server to be ready for discovery..."

    while [ $waited -lt $max_wait ]; do
        if echo '{"type":"describe"}' | nc -w 2 localhost 10200 2>/dev/null | grep -q "pocket-tts"; then
            echo "Server is ready after ${waited}s"
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done

    if [ $waited -ge $max_wait ]; then
        echo "Warning: Timed out waiting for server to start for discovery"
        return 1
    fi

    sleep 1

    if [ -n "$SUPERVISOR_TOKEN" ]; then
        local hostname discovery_host ipv4
        hostname=$(hostname | tr '_' '-')

        # Prefer IPv4 because some Home Assistant hosts resolve the app hostname
        # to an unreachable IPv6 address first.
        ipv4=$(hostname -i 2>/dev/null | tr ' ' '\n' \
            | grep -E '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | head -n1)
        if [ -z "$ipv4" ]; then
            ipv4=$(getent ahostsv4 "$hostname" 2>/dev/null | awk '{print $1; exit}')
        fi
        if [ -n "$ipv4" ]; then
            discovery_host="$ipv4"
            echo "Advertising IPv4 address ${ipv4} for discovery"
        else
            discovery_host="$hostname"
            echo "Could not determine IPv4 address; falling back to hostname ${hostname}"
        fi
        echo "Sending discovery for host: ${discovery_host}:10200"

        local retry=0
        local max_retries=3
        while [ $retry -lt $max_retries ]; do
            local response
            response=$(curl -s -X POST \
                -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" \
                -H "Content-Type: application/json" \
                -d "{\"service\": \"wyoming\", \"config\": {\"uri\": \"tcp://${discovery_host}:10200\"}}" \
                "http://supervisor/discovery" 2>&1)

            if echo "$response" | grep -q '"result".*"ok"'; then
                echo "Successfully sent discovery information to Home Assistant"
                return 0
            fi

            echo "Discovery attempt $((retry + 1)) response: $response"
            retry=$((retry + 1))
            sleep 2
        done
        echo "Warning: Failed to send discovery after ${max_retries} attempts"
    else
        echo "Not running in Home Assistant (no SUPERVISOR_TOKEN) - skipping discovery"
    fi
}

send_discovery &

exec python3 -m wyoming_pocket_tts "${ARGS[@]}"
