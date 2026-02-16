# ElevenLabs to Tuner Integration Demo

This is a simple Python application that retrieves call data from ElevenLabs conversational AI agents and pushes it to the Tuner system for analysis and monitoring. This code is for demonstration purpose only and not production ready.

## Features

- Retrieves conversations from ElevenLabs for a specified agent
- **Time window filtering** to limit conversations to a specific time range
- Transforms conversation data to Tuner API format
- Pushes call data to Tuner API
- Simple CLI interface with progress tracking

## Prerequisites

- Python 3.7 or higher
- ElevenLabs API key and Agent ID
- Tuner API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/usetuner/api-integration-demo.git
cd api-integration-demo
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file from the example:
```bash
cp .env.example .env
```

5. Edit the `.env` file and add your API credentials:
```bash
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_AGENT_ID=your_agent_id_here
TUNER_API_KEY=your_tuner_api_key_here
TUNER_API_URL=https://api.usetuner.ai/api/v1/calls

# Optional: Set time window (default is last 24 hours)
TIME_WINDOW_HOURS=24
```

## Usage

Run the script from the terminal:

```bash
python sync_calls.py
```

The script will:
1. Load configuration from the `.env` file
2. Retrieve conversations from ElevenLabs for the specified agent
3. Transform the data to Tuner format
4. Push each call to the Tuner API
5. Display progress and summary

## API References

- **ElevenLabs API**: https://elevenlabs.io/docs/api-reference/conversations/list
- **Tuner API**: https://docs.usetuner.ai/docs/api-reference/send-call-api

## Configuration

All configuration is managed through environment variables in the `.env` file:

| Variable | Description | Required |
|----------|-------------|----------|
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key | Yes |
| `ELEVENLABS_AGENT_ID` | The agent ID to retrieve calls from | Yes |
| `TUNER_API_KEY` | Your Tuner API key | Yes |
| `TUNER_API_URL` | Tuner API endpoint (default provided) | No |
| `TIME_WINDOW_HOURS` | Retrieve calls from last N hours (default: 24) | No |
| `START_TIME_UNIX` | Custom start time as Unix timestamp | No |
| `END_TIME_UNIX` | Custom end time as Unix timestamp | No |

### Time Window Filtering

By default, the script retrieves calls from the **last 24 hours**. You can customize this in two ways:

1. **Simple time window**: Set `TIME_WINDOW_HOURS` to retrieve calls from the last N hours
   ```bash
   TIME_WINDOW_HOURS=48  # Last 48 hours
   ```

2. **Custom time range**: Use Unix timestamps for precise control
   ```bash
   START_TIME_UNIX=1707811200  # February 13, 2026 00:00:00
   END_TIME_UNIX=1707897600    # February 14, 2026 00:00:00
   ```

## Example Output

```
============================================================
ElevenLabs to Tuner Integration
============================================================

✓ Configuration loaded successfully

Fetching conversations for agent: agent_123abc (from 2026-02-12 00:00:00 to 2026-02-13 00:00:00)
Retrieved 10 conversations, 5 within time window

Pushing 5 calls to Tuner...
  [1/5] Successfully pushed call ID: conv_abc123
  [2/5] Successfully pushed call ID: conv_def456
  [3/5] Successfully pushed call ID: conv_ghi789
  [4/5] Successfully pushed call ID: conv_jkl012
  [5/5] Successfully pushed call ID: conv_mno345

Summary: 5 successful, 0 failed

============================================================
Integration completed successfully!
============================================================
```

## Troubleshooting

### Missing API Keys
If you see an error about missing environment variables, ensure your `.env` file is properly configured with all required credentials.

### API Errors
- **ElevenLabs**: Check that your API key is valid and the agent ID exists
- **Tuner**: Verify your Tuner API key and endpoint URL are correct

## License

This project is licensed under the terms specified in the LICENSE file.
