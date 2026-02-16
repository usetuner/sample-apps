#!/usr/bin/env python3
"""
ElevenLabs to Tuner Integration
This script retrieves call data from ElevenLabs and pushes it to Tuner API.
"""

import os
import sys

from config import load_config
from clients.elevenlabs_client import get_elevenlabs_conversations
from clients.tuner_client import push_to_tuner


def main():
    """Main entry point for the application."""
    print("=" * 60)
    print("ElevenLabs to Tuner Integration")
    print("=" * 60)
    print()
    
    # Load configuration
    config = load_config()
    print("✓ Configuration loaded successfully")
    print()
    
    # Get conversations from ElevenLabs
    try:
        conversations = get_elevenlabs_conversations(
            config.elevenlabs_api_key,
            config.elevenlabs_agent_id,
            config.start_time,
            config.end_time,
        )
        print()
        
        if not conversations:
            print("No conversations found to push to Tuner")
            return
        
        # Push to Tuner
        # Note: workspace_id and agent_remote_identifier should be added to config/env vars
        workspace_id = os.getenv('TUNER_WORKSPACE_ID')
        agent_remote_identifier = os.getenv('TUNER_AGENT_REMOTE_IDENTIFIER')
        
        if not workspace_id or not agent_remote_identifier:
            print("Error: Missing required Tuner parameters")
            print("Please set TUNER_WORKSPACE_ID and TUNER_AGENT_REMOTE_IDENTIFIER environment variables")
            return
        
        push_to_tuner(
            config.tuner_api_key,
            config.tuner_api_url,
            conversations,
            workspace_id,
            agent_remote_identifier
        )
        print()
        print("=" * 60)
        print("Integration completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
